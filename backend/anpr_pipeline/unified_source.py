"""
=============================================================================
Gujarat Police Sentinel - Unified Frame Acquisition Source
=============================================================================
Abstracts video frame ingestion across all input types:
1. Local recorded video files (.mp4, .avi, .mov, .mkv)
2. Live USB / Integrated Webcams (device indices 0, 1)
3. Direct IP CCTV & RTSP / HTTP video streams
4. YouTube live streams & video URLs (via yt-dlp direct stream resolution)
=============================================================================
"""

import os
import time
import logging
from typing import Generator, Tuple, Optional, Any, Dict
from dataclasses import dataclass
from abc import ABC, abstractmethod
import subprocess

import cv2
import numpy as np

logger = logging.getLogger("UnifiedFrameSource")

@dataclass(frozen=True)
class FramePacket:
    camera_id: str
    department: str
    camera_name: str
    latitude: float
    longitude: float
    source_type: str
    codec: str
    width: int
    height: int
    source_pts_ms: float
    arrival_monotonic: float
    frame_number: int
    frame: np.ndarray
    capture_wait_latency_ms: float = 0.0
    
class TimestampProvider(ABC):
    @abstractmethod
    def get_pts(self, frame_index: int, cap: cv2.VideoCapture) -> float:
        pass

class OpenCVTimestampProvider(TimestampProvider):
    def get_pts(self, frame_index: int, cap: cv2.VideoCapture) -> float:
        pts = cap.get(cv2.CAP_PROP_POS_MSEC)
        if pts <= 0:
            logger.warning("Timestamp quality = FALLBACK (CAP_PROP_POS_MSEC <= 0)")
            fps = cap.get(cv2.CAP_PROP_FPS)
            fps = fps if fps > 0 else 25.0
            return float(frame_index * (1000.0 / fps))
        return float(pts)

class UnifiedFrameSource:
    """Provides a uniform frame generator across all multimedia input sources."""

    @staticmethod
    def resolve_youtube_stream_url(youtube_url: str) -> Optional[str]:
        """Uses yt-dlp to extract the best direct HLS / progressive video stream URL."""
        try:
            cmd = [
                "yt-dlp",
                "-f", "best[ext=mp4]/best",
                "-g",
                youtube_url
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
            if result.returncode == 0 and result.stdout.strip():
                resolved_url = result.stdout.strip().split("\n")[0]
                logger.info(f"Resolved YouTube stream URL successfully.")
                return resolved_url
            else:
                logger.warning(f"yt-dlp failed to resolve {youtube_url}: {result.stderr}")
        except Exception as e:
            logger.warning(f"Error executing yt-dlp on {youtube_url}: {e}")
        return None

    @classmethod
    def open_source(cls, source_spec: Any) -> Tuple[Optional[cv2.VideoCapture], Dict[str, Any]]:
        """
        Opens VideoCapture session for any valid input specification.
        Returns: (cap, metadata_dict)
        """
        source_str = str(source_spec).strip()
        metadata = {
            "source": source_str,
            "source_type": "unknown",
            "fps": 25.0,
            "width": 0,
            "height": 0,
            "total_frames": 0,
            "is_live": False
        }

        # 1. Webcam integer index (e.g. 0, 1, "0")
        if source_str.isdigit():
            cam_idx = int(source_str)
            cap = cv2.VideoCapture(cam_idx, cv2.CAP_DSHOW if os.name == 'nt' else cv2.CAP_ANY)
            metadata["source_type"] = "webcam"
            metadata["is_live"] = True

        # 2. YouTube URL
        elif "youtube.com" in source_str or "youtu.be" in source_str:
            direct_url = cls.resolve_youtube_stream_url(source_str)
            if direct_url:
                os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|fflags;nobuffer|flags;low_delay|analyzeduration;500000|probesize;500000"
                cap = cv2.VideoCapture(direct_url)
                metadata["source_type"] = "youtube"
                metadata["is_live"] = True
            else:
                return None, metadata

        # 3. RTSP or Network Stream
        elif source_str.startswith("rtsp://") or source_str.startswith("http://") or source_str.startswith("https://"):
            # Enforce RTSP TCP with low-latency demuxer flags (Requirements 12, 13, 16)
            os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|fflags;nobuffer|flags;low_delay|analyzeduration;500000|probesize;500000"
            cap = cv2.VideoCapture(source_str)
            metadata["source_type"] = "rtsp_or_http"
            metadata["is_live"] = True

        # 4. Local Video File
        elif os.path.exists(source_str):
            cap = cv2.VideoCapture(source_str)
            metadata["source_type"] = "local_file"
            metadata["is_live"] = False
        else:
            logger.error(f"Cannot resolve source specification: {source_str}")
            return None, metadata

        if cap is not None and cap.isOpened():
            if metadata.get("is_live", False):
                try:
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                except Exception:
                    pass

            fps = cap.get(cv2.CAP_PROP_FPS)
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            tot = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            metadata["fps"] = fps if fps > 1.0 else 25.0
            metadata["width"] = w
            metadata["height"] = h
            metadata["total_frames"] = tot if tot > 0 else 0
            return cap, metadata

        return None, metadata

    @classmethod
    def iter_frames(
        cls,
        source_spec: Any,
        camera_metadata: Dict[str, Any],
        max_frames: Optional[int] = None,
        timestamp_provider: Optional[TimestampProvider] = None
    ) -> Generator[FramePacket, None, None]:
        """
        Yields FramePacket continuously.
        Handles frame pacing and stream termination gracefully.
        """
        cap, stream_metadata = cls.open_source(source_spec)
        if cap is None or not cap.isOpened():
            logger.error(f"Failed to open source: {source_spec}")
            return

        if timestamp_provider is None:
            timestamp_provider = OpenCVTimestampProvider()

        frame_idx = 0
        
        # We need codec info; OpenCV CAP_PROP_FOURCC can give it sometimes
        fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
        codec = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)]) if fourcc > 0 else "UNKNOWN"
        
        try:
            while cap.isOpened():
                t_read_start = time.monotonic()
                ret, frame = cap.read()
                arrival = time.monotonic()
                capture_wait_ms = round((arrival - t_read_start) * 1000.0, 2)
                
                if not ret or frame is None:
                    # Could be end of stream, or a dropped frame due to decoder issue
                    # If this is a live RTSP stream, the worker will handle reconnect backoff
                    break

                frame_idx += 1
                source_pts_ms = timestamp_provider.get_pts(frame_idx, cap)

                packet = FramePacket(
                    camera_id=camera_metadata.get("camera_id", "UNKNOWN"),
                    department=camera_metadata.get("department", "Unknown Department"),
                    camera_name=camera_metadata.get("name", "Unknown Camera"),
                    latitude=camera_metadata.get("latitude", 0.0),
                    longitude=camera_metadata.get("longitude", 0.0),
                    source_type=stream_metadata["source_type"],
                    codec=codec,
                    width=stream_metadata["width"],
                    height=stream_metadata["height"],
                    source_pts_ms=source_pts_ms,
                    arrival_monotonic=arrival,
                    frame_number=frame_idx,
                    frame=frame,
                    capture_wait_latency_ms=capture_wait_ms
                )

                yield packet

                if max_frames and frame_idx >= max_frames:
                    break

                if stream_metadata.get("is_live", False):
                    # Small sleep for live simulation pacing if requested
                    pass
        finally:
            cap.release()
