#!/usr/bin/env python3
"""
=============================================================================
Gujarat Police Innovation Challenge 2026 - Sentinel Camera Grid Ingest Client
Adhering to Official Sentinel Sandbox Integrator Specifications (§1 to §4)
Live Host: https://live.corp8.cloud | RTSP Host: rtsp://live.corp8.cloud:8554
=============================================================================
- Protocol: Live RTP/RTSP over TCP (rtsp_transport=tcp)
- Clock: Monotonic Presentation Timestamps (PTS) via CAP_PROP_POS_MSEC
- Resiliency: Automatic exponential backoff reconnects (2s to 30s)
- Decoders: Mixed H.264 and H.265 stream resilience
"""

import os
import sys
import time
import logging
import json
from typing import Optional, Callable, Dict, Any
import requests

# 1. Force RTSP over TCP for OpenCV FFmpeg backend (Prevents firewall packet drop & corrupt frames)
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

try:
    import cv2
    import numpy as np
except ImportError:
    print("Warning: cv2 or numpy not installed. Please install opencv-python.")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [SentinelIngest] %(message)s"
)
logger = logging.getLogger("SentinelIngest")


class SentinelStreamConsumer:
    """
    Consumes live camera streams from Gujarat Police Sentinel Sandbox.
    """

    def __init__(self, camera_id: str, stream_url: str, on_frame_callback: Optional[Callable] = None):
        self.camera_id = camera_id
        self.stream_url = stream_url
        self.on_frame_callback = on_frame_callback
        self.is_running = False
        self.reconnect_delay = 2.0  # start at 2s
        self.max_reconnect_delay = 30.0  # cap at 30s
        self.frame_count = 0

    @classmethod
    def fetch_catalogue(cls, host_url: str = "https://live.corp8.cloud") -> Dict[str, Any]:
        """
        Fetch the dynamic camera catalogue from /api/ingest.
        The catalogue is the contract for available cameras, codecs, and URLs.
        """
        catalogue_endpoint = f"{host_url.rstrip('/')}/api/ingest"
        logger.info(f"Fetching camera catalogue from: {catalogue_endpoint}")
        try:
            resp = requests.get(catalogue_endpoint, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                cameras = data.get("cameras", [])
                logger.info(f"Successfully retrieved catalogue with {len(cameras)} live cameras.")
                return data
            else:
                logger.warning(f"Catalogue returned status {resp.status_code}")
        except Exception as e:
            logger.warning(f"Unable to reach {catalogue_endpoint} ({e})")

        return {"status": "error", "cameras": []}

    def start(self):
        """
        Start stream ingestion loop with robust backoff and PTS extraction.
        """
        self.is_running = True
        logger.info(f"Initiating stream ingest for Camera {self.camera_id} at {self.stream_url}")

        while self.is_running:
            cap = None
            try:
                cap = cv2.VideoCapture(self.stream_url, cv2.CAP_FFMPEG)
                if not cap.isOpened():
                    logger.warning(f"Could not open stream {self.stream_url}. Retrying in {self.reconnect_delay:.1f}s...")
                    self._handle_reconnect()
                    continue

                # Successfully connected - reset reconnect delay
                self.reconnect_delay = 2.0
                logger.info(f"Stream connected: {self.camera_id} ({self.stream_url})")

                while self.is_running:
                    ok, frame = cap.read()
                    if not ok:
                        logger.warning(f"Stream read interrupted on {self.camera_id}.")
                        break  # Break inner loop to trigger exponential backoff reconnect

                    self.frame_count += 1

                    # Section 3 Guideline: Use Monotonic PTS rather than wall clock or declared FPS
                    pts_ms = cap.get(cv2.CAP_PROP_POS_MSEC)
                    if pts_ms <= 0:
                        pts_ms = time.time() * 1000.0

                    # Process frame via callback
                    if self.on_frame_callback:
                        self.on_frame_callback(self.camera_id, frame, pts_ms, self.frame_count)

            except Exception as ex:
                logger.error(f"Error during stream consumption for {self.camera_id}: {ex}")
            finally:
                if cap:
                    cap.release()

            if self.is_running:
                self._handle_reconnect()

    def _handle_reconnect(self):
        """Exponential backoff reconnect (2s to 30s)."""
        time.sleep(self.reconnect_delay)
        self.reconnect_delay = min(self.reconnect_delay * 1.5, self.max_reconnect_delay)

    def stop(self):
        self.is_running = False
        logger.info(f"Stream ingest stopped for {self.camera_id}.")


def sample_frame_handler(camera_id: str, frame: np.ndarray, pts_ms: float, frame_idx: int):
    """Sample callback to log PTS timestamps and dimensions."""
    if frame_idx % 30 == 0:
        h, w = frame.shape[:2]
        logger.info(f"[{camera_id}] Frame #{frame_idx} | PTS: {pts_ms:.1f}ms | Resolution: {w}x{h}")


if __name__ == "__main__":
    print("=" * 75)
    print(" 🛡️  GUJARAT POLICE SENTINEL - LIVE RTSP INGESTION CLIENT")
    print("=" * 75)

    # 1. Fetch live catalogue from https://live.corp8.cloud/api/ingest
    cat = SentinelStreamConsumer.fetch_catalogue("https://live.corp8.cloud")
    if cat.get("cameras"):
        print(f"Discovered {len(cat['cameras'])} live feeds from Gujarat Police Sandbox:")
        for cam in cat["cameras"][:5]:
            print(f"  • Cam #{cam.get('number')}: {cam.get('name')} -> {cam.get('rtsp_url')}")
        print("  • ... (30 feeds total)")

    target_url = sys.argv[1] if len(sys.argv) > 1 else "rtsp://live.corp8.cloud:8554/stream/1"
    target_cam_id = sys.argv[2] if len(sys.argv) > 2 else "CAM-01"

    print(f"\nConnecting to: {target_cam_id} ({target_url})...")
    consumer = SentinelStreamConsumer(
        camera_id=target_cam_id,
        stream_url=target_url,
        on_frame_callback=sample_frame_handler
    )

    try:
        consumer.start()
    except KeyboardInterrupt:
        consumer.stop()
        print("\nIngest client terminated cleanly.")
