import os
import sys
import time
import logging
import threading
import requests
import queue
import collections
import cv2
from typing import Dict, Any, List, Optional, Callable, Tuple

# Ensure backend directory is in sys.path
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from database import SentinelDatabase, db
from anpr_pipeline.unified_source import UnifiedFrameSource, FramePacket

logger = logging.getLogger("CameraManager")

# Explicit Stream Status Enum Values (Requirement 7)
STREAM_STATUS = {
    "INACTIVE": "INACTIVE",
    "STARTING": "STARTING",
    "ONLINE": "ONLINE",
    "DEGRADED": "DEGRADED",
    "RECONNECTING": "RECONNECTING",
    "STOPPING": "STOPPING",
    "OFFLINE": "OFFLINE",
    "FAILED": "FAILED"
}

# Reconnect backoff sequence in seconds (Requirement 21)
RECONNECT_BACKOFF = [2, 4, 8, 16, 30, 30]


class LatestFrameBuffer:
    """
    Thread-safe bounded frame buffer for live RTSP analytics (Requirements 4, 5, 6, 7).
    Discipline:
      - LIVE mode: Bounded capacity (1-2 frames). On full, drops oldest frame (Drop-Oldest / Coalesce).
        Never drops the newest live frame. Also rejects frames exceeding max_live_lag_ms.
      - RECORDED mode: Sequential FIFO without intentional dropping.
    """
    def __init__(
        self,
        camera_id: str = "GLOBAL",
        capacity: int = 2,
        mode: str = "LIVE",
        max_live_lag_ms: float = 2000.0
    ):
        self.camera_id = camera_id
        self.capacity = max(1, capacity)
        self.mode = mode.upper()
        self.max_live_lag_ms = max_live_lag_ms

        self._buffer = collections.deque()
        self._lock = threading.Lock()
        self._not_empty = threading.Condition(self._lock)

        # Telemetry & PTS tracking
        self.enqueued_count = 0
        self.dequeued_count = 0
        self.dropped_stale_count = 0
        self.latest_source_pts_ms: Optional[float] = None
        self.latest_arrival_monotonic: float = 0.0

    def put(self, packet: FramePacket) -> bool:
        with self._lock:
            self.latest_source_pts_ms = packet.source_pts_ms
            self.latest_arrival_monotonic = packet.arrival_monotonic
            self.enqueued_count += 1

            if self.mode == "LIVE":
                # Drop oldest waiting frame when full to prioritize live edge
                while len(self._buffer) >= self.capacity:
                    self._buffer.popleft()
                    self.dropped_stale_count += 1

                self._buffer.append(packet)
                self._not_empty.notify()
                return True
            else:
                self._buffer.append(packet)
                self._not_empty.notify()
                return True

    def put_nowait(self, packet: FramePacket) -> bool:
        return self.put(packet)

    def get(self, block: bool = True, timeout: Optional[float] = 0.5) -> Optional[FramePacket]:
        with self._not_empty:
            if not block:
                if not self._buffer:
                    return None
                return self._pop_fresh()

            end_time = time.monotonic() + (timeout if timeout is not None else 0.0)
            while not self._buffer:
                if timeout is not None:
                    remaining = end_time - time.monotonic()
                    if remaining <= 0:
                        return None
                    self._not_empty.wait(remaining)
                else:
                    self._not_empty.wait()

            return self._pop_fresh()

    def _pop_fresh(self) -> Optional[FramePacket]:
        if not self._buffer:
            return None
        if self.mode == "LIVE":
            now_mono = time.monotonic()
            while self._buffer:
                pkt = self._buffer.popleft()
                lag_ms = (now_mono - pkt.arrival_monotonic) * 1000.0
                if lag_ms > self.max_live_lag_ms and self._buffer:
                    self.dropped_stale_count += 1
                    continue
                self.dequeued_count += 1
                return pkt
            return None
        else:
            self.dequeued_count += 1
            return self._buffer.popleft()

    def qsize(self) -> int:
        with self._lock:
            return len(self._buffer)

    def empty(self) -> bool:
        with self._lock:
            return len(self._buffer) == 0

    def clear(self):
        with self._lock:
            self._buffer.clear()


class AsyncPersistenceWorker:
    """
    Non-blocking background worker for SQLite writes and snapshot generation (Requirement 13).
    Ensures live frame ingestion and analytics workers are never blocked by disk I/O.
    """
    def __init__(self, db_instance: SentinelDatabase, maxsize: int = 500):
        self.db = db_instance
        self.task_queue: queue.Queue = queue.Queue(maxsize=maxsize)
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.dropped_low_priority = 0
        self.last_write_latency_ms = 0.0

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True, name="AsyncPersistenceWorker")
        self.thread.start()

    def submit(self, task_type: str, data: Dict[str, Any], is_high_priority: bool = False) -> bool:
        if not self.running:
            return False

        if not is_high_priority and self.task_queue.qsize() > int(self.task_queue.maxsize * 0.8):
            self.dropped_low_priority += 1
            return False

        try:
            self.task_queue.put_nowait((task_type, data))
            return True
        except queue.Full:
            if is_high_priority:
                try:
                    _ = self.task_queue.get_nowait()
                    self.task_queue.put_nowait((task_type, data))
                    return True
                except Exception:
                    pass
            self.dropped_low_priority += 1
            return False

    def _run(self):
        while self.running:
            try:
                task = self.task_queue.get(timeout=0.5)
                if task is None:
                    continue
                task_type, data = task
                t0 = time.perf_counter()

                if task_type == "RECORD_DETECTION":
                    self.db.record_detection(data)
                elif task_type == "RECORD_ANPR_OBSERVATION":
                    self.db.record_anpr_observation(data)
                elif task_type == "RECORD_GLOBAL_VEHICLE":
                    self.db.record_global_vehicle(**data)
                elif task_type == "RECORD_JOURNEY_EVENT":
                    self.db.record_vehicle_journey_event(**data)

                self.last_write_latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)
                self.task_queue.task_done()
            except queue.Empty:
                continue
            except Exception as ex:
                logger.warning(f"Async persistence write error: {ex}")

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)


class ActiveStreamWorker(threading.Thread):
    """
    Dedicated worker thread for an activated camera stream.
    Enforces TCP RTSP, per-camera LatestFrameBuffer, tracks live health telemetry,
    and shares decoded frames with HUD cache with zero duplicate RTSP connections.
    """

    def __init__(
        self,
        camera_id: str,
        camera_metadata: Dict[str, Any],
        frame_queue: Optional[Any] = None,
        db_instance: SentinelDatabase = None,
        hud_cache_update_cb: Optional[Callable[[str, bytes], None]] = None,
        mode: str = "LIVE",
        buffer_capacity: int = 2,
        max_live_lag_ms: float = 2000.0
    ):
        super().__init__(daemon=True, name=f"StreamWorker-{camera_id}")
        self.camera_id = camera_id
        self.camera_metadata = dict(camera_metadata)
        self.fallback_frame_queue = frame_queue
        self.db = db_instance
        self.hud_cache_update_cb = hud_cache_update_cb
        self.pipeline_mode = mode

        # Per-camera isolated LatestFrameBuffer (Requirements 4, 5, 6, 14)
        self.frame_buffer = LatestFrameBuffer(
            camera_id=camera_id,
            capacity=buffer_capacity,
            mode=mode,
            max_live_lag_ms=max_live_lag_ms
        )

        self.running = False
        self.status = STREAM_STATUS["STARTING"]
        self.reconnect_count = 0
        self.dropped_frames = 0
        self.stale_frames_dropped = 0
        self.total_frames_received = 0
        self.total_frames_processed = 0

        self.last_source_pts = 0.0
        self.processed_source_pts = 0.0
        self.last_frame_received = 0.0
        self.last_frame_processed = 0.0
        self.capture_wait_latency = 0.0
        self.queue_wait_latency = 0.0
        self.processing_latency = 0.0
        self.source_video_lag: Any = "LIVE_EDGE_UNAVAILABLE"

        self.codec = self.camera_metadata.get("codec", "H264")
        self.resolution = self.camera_metadata.get("resolution", "1920x1080")
        self.received_fps = 0.0
        self.processed_fps = 0.0

        self.latest_packet: Optional[FramePacket] = None
        self._fps_window_start = time.time()
        self._fps_window_frames = 0

    def run(self):
        self.running = True
        logger.info(f"[{self.camera_id}] Starting stream worker (TCP RTSP).")
        self._update_status(STREAM_STATUS["STARTING"])

        # Force TCP RTSP (Requirement 21)
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|analyzeduration;1000000|probesize;1000000"

        while self.running:
            source_url = self.camera_metadata.get("rtsp_url")
            if not source_url:
                logger.error(f"[{self.camera_id}] No RTSP URL provided.")
                self._update_status(STREAM_STATUS["FAILED"])
                break

            try:
                self._update_status(STREAM_STATUS["ONLINE"])
                self.reconnect_count = 0
                self._fps_window_start = time.time()
                self._fps_window_frames = 0

                # Consume frames via UnifiedFrameSource
                for packet in UnifiedFrameSource.iter_frames(source_url, self.camera_metadata):
                    if not self.running:
                        break

                    now = time.time()
                    self.last_frame_received = now
                    self.last_source_pts = packet.source_pts_ms
                    self.total_frames_received += 1
                    self._fps_window_frames += 1

                    # Rolling FPS calculation
                    elapsed = now - self._fps_window_start
                    if elapsed >= 1.0:
                        self.received_fps = round(self._fps_window_frames / elapsed, 1)
                        self._fps_window_frames = 0
                        self._fps_window_start = now

                    if packet.codec and packet.codec != "UNKNOWN":
                        self.codec = packet.codec
                    if packet.width and packet.height:
                        self.resolution = f"{packet.width}x{packet.height}"

                    self.latest_packet = packet

                    # Share frame to HUD cache directly (Requirement 25: Single RTSP connection)
                    if self.hud_cache_update_cb and packet.frame is not None:
                        try:
                            resized = cv2.resize(packet.frame, (640, 360))
                            ret, buf = cv2.imencode('.jpg', resized, [cv2.IMWRITE_JPEG_QUALITY, 80])
                            if ret:
                                self.hud_cache_update_cb(self.camera_id, buf.tobytes())
                        except Exception:
                            pass

                    # Store in per-camera LatestFrameBuffer (Req 4, 5, 6, 14)
                    # LIVE mode drops oldest frame to remain locked to live edge; RECORDED mode retains all
                    self.frame_buffer.put(packet)
                    self.dropped_frames = self.frame_buffer.dropped_stale_count
                    self.stale_frames_dropped = self.frame_buffer.dropped_stale_count

                if not self.running:
                    break

            except Exception as e:
                logger.error(f"[{self.camera_id}] Stream capture error: {e}")

            if not self.running:
                break

            # Stream disconnected, apply exponential backoff (2, 4, 8, 16, 30, 30) (Req 21)
            backoff_idx = min(self.reconnect_count, len(RECONNECT_BACKOFF) - 1)
            delay = RECONNECT_BACKOFF[backoff_idx]
            self.reconnect_count += 1
            logger.warning(
                f"[{self.camera_id}] Stream disconnected. Reconnecting in {delay}s... "
                f"(Attempt {self.reconnect_count})"
            )
            self._update_status(STREAM_STATUS["RECONNECTING"])

            # Interruptible sleep
            sleep_time = 0.0
            while sleep_time < delay and self.running:
                time.sleep(0.5)
                sleep_time += 0.5

        self._update_status(STREAM_STATUS["OFFLINE"])
        logger.info(f"[{self.camera_id}] Stream worker cleanly stopped.")

    def record_processed_frame(
        self,
        packet: FramePacket,
        processing_latency_ms: float = 0.0,
        queue_wait_latency_ms: float = 0.0,
        plate_detector_ms: float = 0.0,
        ocr_ms: float = 0.0
    ):
        """Called by pipeline worker when a frame from this camera is processed (Req 1, 2, 3, 33)."""
        now_t = time.time()
        self.last_frame_processed = now_t
        self.total_frames_processed += 1
        self.processing_latency = round(processing_latency_ms, 2)
        self.queue_wait_latency = round(queue_wait_latency_ms, 2)
        self.capture_wait_latency = round(packet.capture_wait_latency_ms, 2)
        self.plate_detector_ms = round(plate_detector_ms, 2)
        self.ocr_ms = round(ocr_ms, 2)
        self.processed_source_pts = packet.source_pts_ms

        # Real Live-Edge Measurement (Req 3):
        # Compare freshest available source PTS with the source PTS currently processed
        if self.last_source_pts > 0 and packet.source_pts_ms > 0:
            self.source_video_lag = max(0.0, round(self.last_source_pts - packet.source_pts_ms, 2))
        else:
            self.source_video_lag = "LIVE_EDGE_UNAVAILABLE"

        # Update rolling processed FPS
        if not hasattr(self, "_proc_fps_window_start"):
            self._proc_fps_window_start = now_t
            self._proc_fps_window_frames = 0
        self._proc_fps_window_frames += 1
        proc_elapsed = now_t - self._proc_fps_window_start
        if proc_elapsed >= 1.0:
            self.processed_fps = round(self._proc_fps_window_frames / proc_elapsed, 1)
            self._proc_fps_window_frames = 0
            self._proc_fps_window_start = now_t

    def stop(self):
        self.running = False
        self._update_status(STREAM_STATUS["STOPPING"])

    def _update_status(self, status: str):
        self.status = status
        self.camera_metadata["status"] = status
        try:
            self.db.update_camera_status(self.camera_id, status)
        except Exception:
            pass

    def get_health(self) -> Dict[str, Any]:
        """Exposes full telemetry metrics (Requirements 1, 2, 3, 20, 33)."""
        return {
            "camera_id": self.camera_id,
            "status": self.status,
            "codec": self.codec,
            "resolution": self.resolution,
            "pipeline_mode": self.pipeline_mode,
            "queue_depth": self.frame_buffer.qsize(),
            "buffer_capacity": self.frame_buffer.capacity,
            "dropped_frames": self.frame_buffer.dropped_stale_count,
            "stale_frames_dropped": self.frame_buffer.dropped_stale_count,
            "received_fps": self.received_fps,
            "processed_fps": self.processed_fps,
            # Independent Latency Taxonomy (Requirement 1, 20, 21, 33)
            "capture_wait_latency_ms": self.capture_wait_latency,
            "queue_wait_latency_ms": self.queue_wait_latency,
            "processing_latency_ms": self.processing_latency,
            "plate_detector_ms": getattr(self, "plate_detector_ms", 0.0),
            "ocr_ms": getattr(self, "ocr_ms", 0.0),
            "inference_latency": self.processing_latency,
            "source_pts_ms": self.last_source_pts,
            "processed_pts_ms": self.processed_source_pts,
            "source_video_lag_ms": self.source_video_lag,
            "last_frame_received": self.last_frame_received,
            "last_frame_processed": self.last_frame_processed,
            "reconnect_count": self.reconnect_count,
            "analytics_active": True
        }


class CameraManager:
    """
    Central Controller for Camera Discovery, Active RTSP Stream Lifecycle,
    and ANPR Ingestion Pipeline Infrastructure.
    """

    def __init__(
        self,
        db_instance: SentinelDatabase,
        max_active_streams: Optional[int] = None,
        queue_size: int = 100,
        anpr_pipeline_instance: Any = None,
        broadcast_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        hud_cache_update_cb: Optional[Callable[[str, bytes], None]] = None
    ):
        self.db = db_instance
        # Configurable max active streams (Requirement 6)
        if max_active_streams is None:
            self.max_active_streams = int(os.environ.get("MAX_ACTIVE_STREAMS", 5))
        else:
            self.max_active_streams = max_active_streams

        self.workers: Dict[str, ActiveStreamWorker] = {}
        self.frame_queue = queue.Queue(maxsize=queue_size)
        self.registry_url = os.environ.get("CAMERA_REGISTRY_URL", "https://live.corp8.cloud/api/ingest")

        self.anpr_pipeline = anpr_pipeline_instance
        self.broadcast_callback = broadcast_callback
        self.hud_cache_update_cb = hud_cache_update_cb

        # Guards against duplicate startup and multiple worker hazards (Requirement 24)
        self.is_running = False
        self._init_lock = threading.Lock()
        self._stream_lock = threading.Lock()

        # Pipeline consumer threads
        self.pipeline_threads: List[threading.Thread] = []
        self._stop_event = threading.Event()
        self._rr_index = 0

        # Non-blocking async persistence worker (Requirement 13)
        self.persistence_worker = AsyncPersistenceWorker(self.db, maxsize=1000)

        # Discovery loop
        self._discovery_thread: Optional[threading.Thread] = None
        self._stop_discovery_event = threading.Event()
        self._seen_event_ids = set()
        self._seen_event_lock = threading.Lock()

    def set_anpr_pipeline(self, pipeline: Any):
        self.anpr_pipeline = pipeline

    def set_broadcast_callback(self, cb: Callable[[Dict[str, Any]], None]):
        self.broadcast_callback = cb

    def set_hud_cache_update_cb(self, cb: Callable[[str, bytes], None]):
        self.hud_cache_update_cb = cb

    # =========================================================================
    # 1. CATALOGUE DISCOVERY & SYNC (Requirements 3, 4, 19, 20)
    # =========================================================================
    def sync_catalogue(self) -> bool:
        """
        Synchronizes camera catalogue from the authoritative /api/ingest.
        Preserves existing historical ANPR data and does not disconnect active streams.
        """
        logger.info(f"Synchronizing camera catalogue from {self.registry_url}")
        try:
            response = requests.get(self.registry_url, timeout=4.0)
            if response.status_code == 200:
                data = response.json()
                cameras_list = []
                if isinstance(data, list):
                    cameras_list = data
                elif isinstance(data, dict):
                    cameras_list = data.get("cameras", data.get("data", []))

                for cam in cameras_list:
                    c_id = str(cam.get("camera_id") or cam.get("id") or "").strip()
                    if not c_id:
                        continue

                    camera_record = {
                        "camera_id": c_id,
                        "name": cam.get("name") or cam.get("camera_name") or f"Camera {c_id}",
                        "department": cam.get("department", "Gujarat Police"),
                        "city": cam.get("city", "Gujarat"),
                        "zone": cam.get("zone", "State Grid"),
                        "location": cam.get("location") or cam.get("zone") or cam.get("name") or "State Grid",
                        "latitude": float(cam.get("latitude") or cam.get("lat") or 23.0225),
                        "longitude": float(cam.get("longitude") or cam.get("lng") or 72.5714),
                        "codec": cam.get("codec", "H264"),
                        "resolution": cam.get("resolution", "1920x1080"),
                        "rtsp_url": cam.get("rtsp_url") or cam.get("rtspUrl") or "",
                        "hls_url": cam.get("hls_url") or cam.get("hlsUrl") or "",
                        "whep_url": cam.get("whep_url") or cam.get("whepUrl") or "",
                        "status": cam.get("status", "ONLINE"),
                        "fps": float(cam.get("fps", 25.0))
                    }
                    self.db.add_camera(camera_record)

                logger.info(f"Successfully synchronized {len(cameras_list)} cameras from registry.")
                return True
        except Exception as e:
            logger.warning(f"Failed to reach registry {self.registry_url}: {e}. Preserving local database.")

        local_cams = self.db.get_all_cameras()
        if local_cams:
            logger.info(f"Loaded {len(local_cams)} existing cameras from local registry.")
            return True
        return False

    def start_discovery_loop(self, interval: Optional[int] = None):
        """
        Starts the background discovery loop with configurable interval (Requirement 4).
        Idempotent: will not spawn duplicate threads.
        """
        with self._init_lock:
            if self._discovery_thread and self._discovery_thread.is_alive():
                logger.info("Discovery loop is already running.")
                return

            if interval is None:
                interval = int(os.environ.get("CAMERA_DISCOVERY_INTERVAL", 30))

            self._stop_discovery_event.clear()

            def _loop():
                logger.info(f"Discovery loop started with interval={interval}s")
                while not self._stop_discovery_event.is_set():
                    try:
                        self.sync_catalogue()
                    except Exception as err:
                        logger.error(f"Error in discovery loop: {err}")
                    self._stop_discovery_event.wait(timeout=float(interval))
                logger.info("Discovery loop stopped.")

            self._discovery_thread = threading.Thread(
                target=_loop, daemon=True, name="Camera-Discovery-Loop"
            )
            self._discovery_thread.start()

    def stop_discovery_loop(self):
        self._stop_discovery_event.set()
        if self._discovery_thread and self._discovery_thread.is_alive():
            self._discovery_thread.join(timeout=2.0)

    # =========================================================================
    # 2. WORKER INFRASTRUCTURE & STARTUP (Requirements 1, 2)
    # =========================================================================
    def start_workers(self, num_consumer_threads: int = 1):
        """
        Initializes the ANPR pipeline worker infrastructure.
        Calling start_workers() DOES NOT automatically connect any cameras (Requirement 2).
        """
        with self._init_lock:
            if self.is_running:
                logger.info("CameraManager worker infrastructure is already running.")
                return

            self.is_running = True
            self._stop_event.clear()
            self.persistence_worker.start()

            for i in range(num_consumer_threads):
                t = threading.Thread(
                    target=self._pipeline_worker_loop,
                    daemon=True,
                    name=f"ANPR-Consumer-Worker-{i+1}"
                )
                self.pipeline_threads.append(t)
                t.start()

            logger.info(f"Started {num_consumer_threads} ANPR pipeline consumer worker(s) and AsyncPersistenceWorker. Active cameras: {len(self.workers)}")

    def _pipeline_worker_loop(self):
        """
        Consumes FramePackets from isolated per-camera frame buffers.
        Propagates camera context and source_pts_ms naturally through:
        FramePacket -> Detection -> Track -> Finalized Observation -> Global Correlation -> Journey Event.
        """
        while self.is_running and not self._stop_event.is_set():
            packet = self.get_frame(block=True, timeout=0.2)
            if packet is None:
                continue

            worker = self.workers.get(packet.camera_id)
            arrival_mono = packet.arrival_monotonic
            queue_wait_ms = max(0.0, (time.monotonic() - arrival_mono) * 1000.0)
            t_start = time.perf_counter()

            try:
                if self.anpr_pipeline:
                    output = self.anpr_pipeline.process_frame(packet)
                    proc_time_ms = (time.perf_counter() - t_start) * 1000.0

                    if worker:
                        worker.record_processed_frame(
                            packet,
                            proc_time_ms,
                            queue_wait_ms,
                            plate_detector_ms=output.telemetry.stage1_plate_ms,
                            ocr_ms=output.telemetry.stage3_ocr_ms
                        )

                    # 1. Process Finalized Tracklet Events (Requirement 1, 9, 10, 13)
                    finalized_list = output.finalized_events or []
                    for fin_event in finalized_list:
                        self._handle_finalized_anpr_event(packet, fin_event, worker)

                    # 2. Check for confirmed/stabilized plate detections
                    for det in output.detections:
                        if det.confidence >= 0.70 and det.plate_number and len(det.plate_number) >= 4:
                            # Non-blocking async persistence write (Req 13)
                            if det.tracking_state in ("STABILIZING", "CONFIRMED") and det.confidence >= 0.85:
                                self.persistence_worker.submit("RECORD_DETECTION", {
                                    "camera_id": packet.camera_id,
                                    "plate": det.plate_number,
                                    "raw_ocr": det.raw_plate_text,
                                    "confidence": det.confidence,
                                    "vehicle_type": det.vehicle_type,
                                    "track_id": det.track_id,
                                    "source_feed": packet.camera_name,
                                    "city": getattr(packet, "city", "Gujarat"),
                                    "timestamp": output.timestamp,
                                    "video_pts_ms": packet.source_pts_ms,
                                    "global_vehicle_id": f"GV-{det.plate_number.replace(' ', '').replace('-', '')}"
                                }, is_high_priority=False)

                            # Live WebSocket Alert/HUD broadcast for immediate real-time display
                            if self.broadcast_callback and (det.tracking_state in ("STABILIZING", "CONFIRMED") or det.confidence >= 0.80):
                                health = worker.get_health() if worker else {}
                                live_payload = {
                                    "type": "ANPR_LIVE_DETECTION",
                                    "event_id": f"live_{packet.camera_id}_{det.track_id}_{int(packet.source_pts_ms)}",
                                    "camera_id": packet.camera_id,
                                    "camera_name": packet.camera_name,
                                    "department": packet.department,
                                    "latitude": packet.latitude,
                                    "longitude": packet.longitude,
                                    "source_pts_ms": packet.source_pts_ms,
                                    "timestamp": output.timestamp,
                                    "global_vehicle_id": f"GV-{det.plate_number.replace(' ', '').replace('-', '')}",
                                    "plate": det.plate_number,
                                    "plate_text": det.plate_number,
                                    "confidence": det.confidence,
                                    "plate_category": det.plate_category,
                                    "vehicle_type": det.vehicle_type,
                                    "snapshot_path": f"/api/stream/snapshot/{packet.camera_id.lower().replace('-', '')}",
                                    "telemetry": {
                                        "queue_depth": health.get("queue_depth", 0),
                                        "dropped_frames": health.get("dropped_frames", 0),
                                        "stale_frames_dropped": health.get("stale_frames_dropped", 0),
                                        "queue_wait_ms": health.get("queue_wait_latency_ms", 0.0),
                                        "processing_ms": health.get("processing_latency_ms", 0.0),
                                        "plate_detector_ms": output.telemetry.stage1_plate_ms,
                                        "ocr_ms": output.telemetry.stage3_ocr_ms,
                                        "source_video_lag_ms": health.get("source_video_lag_ms", "LIVE_EDGE_UNAVAILABLE"),
                                        "received_fps": health.get("received_fps", 0.0),
                                        "processed_fps": health.get("processed_fps", 0.0)
                                    }
                                }
                                self.broadcast_callback(live_payload)

            except Exception as ex:
                logger.error(f"Error processing frame from {packet.camera_id}: {ex}")

    def _handle_finalized_anpr_event(
        self,
        packet: FramePacket,
        fin_event: Dict[str, Any],
        worker: Optional[ActiveStreamWorker] = None
    ):
        """
        Handles a logically finalized ANPR observation.
        Ensures strict deduplication: 1 observation = 1 journey event (Req 1, 9).
        Offloads DB writes to AsyncPersistenceWorker and broadcasts full telemetry.
        """
        plate_text = (fin_event.get("plate_text") or "").strip().upper()
        if not plate_text:
            return

        track_id = fin_event.get("track_id", 0)
        source_pts = packet.source_pts_ms
        # Deterministic event ID (Requirement 9)
        event_id = f"evt_{packet.camera_id}_{track_id}_{int(source_pts)}"

        with self._seen_event_lock:
            if event_id in self._seen_event_ids:
                return
            self._seen_event_ids.add(event_id)
            if len(self._seen_event_ids) > 10000:
                self._seen_event_ids.clear()

        global_id = f"GV-{plate_text.replace(' ', '').replace('-', '')}"
        confidence = float(fin_event.get("confidence", 0.95))
        vehicle_type = fin_event.get("vehicle_type", "Car")
        snapshot_path = fin_event.get("snapshot_path") or f"/api/stream/snapshot/{packet.camera_id.lower().replace('-', '')}"
        now_ts = time.strftime("%Y-%m-%d %H:%M:%S IST")

        # 1. Non-blocking Async Persistence: ANPRObservation (Req 13)
        self.persistence_worker.submit("RECORD_ANPR_OBSERVATION", {
            "observation_id": event_id,
            "camera_id": packet.camera_id,
            "camera_name": packet.camera_name,
            "department": packet.department,
            "latitude": packet.latitude,
            "longitude": packet.longitude,
            "track_id": track_id,
            "plate_text": plate_text,
            "confidence": confidence,
            "plate_category": fin_event.get("plate_category", "STANDARD_PRIVATE"),
            "number_type": fin_event.get("number_type", "GENERAL"),
            "vehicle_type": vehicle_type,
            "source_pts_ms": source_pts,
            "timestamp": now_ts,
            "snapshot_path": snapshot_path,
            "global_vehicle_id": global_id
        }, is_high_priority=True)

        # 2. Non-blocking Async Persistence: GlobalVehicle (Req 13)
        self.persistence_worker.submit("RECORD_GLOBAL_VEHICLE", {
            "global_vehicle_id": global_id,
            "plate_text": plate_text,
            "confidence": confidence,
            "vehicle_class": vehicle_type,
            "source_pts_ms": source_pts
        }, is_high_priority=True)

        # 3. Non-blocking Async Persistence: VehicleJourneyEvent (Req 1, 9, 13)
        self.persistence_worker.submit("RECORD_JOURNEY_EVENT", {
            "global_vehicle_id": global_id,
            "observation_id": event_id,
            "camera_id": packet.camera_id,
            "source_pts_ms": source_pts,
            "latitude": packet.latitude,
            "longitude": packet.longitude,
            "plate_text": plate_text,
            "confidence": confidence,
            "snapshot_path": snapshot_path,
            "timestamp": now_ts,
            "camera_name": packet.camera_name
        }, is_high_priority=True)

        # 4. Broadcast Finalized ANPR Event over WebSocket with full Telemetry (Requirement 9, 13, 20)
        if self.broadcast_callback:
            health = worker.get_health() if worker else {}
            event_payload = {
                "type": "ANPR_FINALIZED_EVENT",
                "event_id": event_id,
                "camera_id": packet.camera_id,
                "camera_name": packet.camera_name,
                "department": packet.department,
                "latitude": packet.latitude,
                "longitude": packet.longitude,
                "source_pts_ms": source_pts,
                "timestamp": now_ts,
                "global_vehicle_id": global_id,
                "plate": plate_text,
                "plate_text": plate_text,
                "plate_category": fin_event.get("plate_category", "STANDARD_PRIVATE"),
                "confidence": confidence,
                "snapshot_path": snapshot_path,
                "telemetry": {
                    "queue_depth": health.get("queue_depth", 0),
                    "dropped_frames": health.get("dropped_frames", 0),
                    "stale_frames_dropped": health.get("stale_frames_dropped", 0),
                    "queue_wait_ms": health.get("queue_wait_latency_ms", 0.0),
                    "processing_ms": health.get("processing_latency_ms", 0.0),
                    "source_video_lag_ms": health.get("source_video_lag_ms", "LIVE_EDGE_UNAVAILABLE"),
                    "received_fps": health.get("received_fps", 0.0),
                    "processed_fps": health.get("processed_fps", 0.0)
                }
            }
            try:
                self.broadcast_callback(event_payload)
            except Exception as e:
                logger.warning(f"Error broadcasting finalized ANPR event: {e}")

    # =========================================================================
    # 3. ACTIVE CAMERA STREAM MANAGEMENT (Requirements 5, 6, 7, 8)
    # =========================================================================
    def start_stream(self, camera_id: str) -> Dict[str, Any]:
        """
        Activates an RTSP stream worker for a camera.
        Idempotent: starting an already-active camera does NOT create a second worker.
        Enforces MAX_ACTIVE_STREAMS limit.
        """
        with self._stream_lock:
            # 1. Idempotency Check (Requirement 8)
            if camera_id in self.workers:
                worker = self.workers[camera_id]
                if worker.is_alive() and worker.running:
                    logger.info(f"Camera {camera_id} is already streaming.")
                    return {
                        "status": "ALREADY_ACTIVE",
                        "message": f"Camera {camera_id} is already streaming.",
                        "active": True,
                        "health": worker.get_health()
                    }

            # 2. Resource Limit Check (Requirement 6)
            active_count = sum(1 for w in self.workers.values() if w.is_alive() and w.running)
            if active_count >= self.max_active_streams:
                logger.warning(
                    f"Max active streams ({self.max_active_streams}) reached. "
                    f"Cannot start stream for {camera_id}."
                )
                return {
                    "status": "RESOURCE_LIMIT_REACHED",
                    "message": f"Maximum active streams limit ({self.max_active_streams}) reached. Cannot start {camera_id}.",
                    "active": False
                }

            # 3. Fetch Camera Metadata
            camera_metadata = self.db.get_camera_by_id(camera_id)
            if not camera_metadata:
                logger.error(f"Camera {camera_id} not found in database.")
                return {
                    "status": "CAMERA_NOT_FOUND",
                    "message": f"Camera {camera_id} not found in registry.",
                    "active": False
                }

            # 4. Start Worker
            mode = "LIVE"
            if self.anpr_pipeline and hasattr(self.anpr_pipeline, "config"):
                mode = getattr(self.anpr_pipeline.config, "pipeline_mode", "LIVE")

            worker = ActiveStreamWorker(
                camera_id=camera_id,
                camera_metadata=camera_metadata,
                frame_queue=self.frame_queue,
                db_instance=self.db,
                hud_cache_update_cb=self.hud_cache_update_cb,
                mode=mode
            )
            self.workers[camera_id] = worker
            worker.start()

            logger.info(f"Activated stream worker for {camera_id} (Active: {active_count + 1}/{self.max_active_streams}, Mode: {mode})")
            return {
                "status": "SUCCESS",
                "message": f"Camera {camera_id} stream started successfully.",
                "active": True,
                "health": worker.get_health()
            }

    def stop_stream(self, camera_id: str) -> Dict[str, Any]:
        """
        Deactivates an active stream worker.
        Idempotent: calling stop twice causes no errors.
        """
        with self._stream_lock:
            if camera_id in self.workers:
                worker = self.workers.pop(camera_id)
                worker.stop()
                logger.info(f"Requested stop for stream {camera_id}.")
                return {
                    "status": "SUCCESS",
                    "message": f"Camera {camera_id} stream stopped.",
                    "active": False
                }
            return {
                "status": "ALREADY_STOPPED",
                "message": f"Camera {camera_id} is not currently active.",
                "active": False
            }

    def get_active_stream_count(self) -> int:
        """Returns the number of currently active RTSP stream workers."""
        with self._stream_lock:
            return sum(1 for w in self.workers.values() if w.is_alive() and w.running)

    def get_camera_health(self, camera_id: str) -> Dict[str, Any]:
        """
        Returns real camera health telemetry (Requirement 23).
        """
        worker = self.workers.get(camera_id)
        if worker and worker.is_alive():
            return worker.get_health()

        # Offline / Inactive state from database
        cam = self.db.get_camera_by_id(camera_id)
        return {
            "camera_id": camera_id,
            "status": STREAM_STATUS["OFFLINE"],
            "codec": cam.get("codec", "H264") if cam else "H264",
            "resolution": cam.get("resolution", "1920x1080") if cam else "1920x1080",
            "last_source_pts": 0.0,
            "last_frame_received": 0.0,
            "last_frame_processed": 0.0,
            "reconnect_count": 0,
            "dropped_frames": 0,
            "received_fps": 0.0,
            "processed_fps": 0.0,
            "inference_latency": 0.0,
            "analytics_active": False
        }

    def get_all_camera_health(self) -> Dict[str, Dict[str, Any]]:
        cams = self.db.get_all_cameras()
        health_map = {}
        for c in cams:
            cid = c["camera_id"]
            health_map[cid] = self.get_camera_health(cid)
        return health_map

    def get_frame(self, block: bool = True, timeout: Optional[float] = 0.5) -> Optional[FramePacket]:
        """
        Fair Round-Robin frame retrieval across isolated per-camera buffers (Req 14, 15).
        Prevents head-of-line blocking and ensures one slow camera cannot stall other cameras.
        """
        with self._stream_lock:
            active_workers = [
                w for w in self.workers.values()
                if (w.is_alive() and w.running) or w.running or (w.frame_buffer and w.frame_buffer.qsize() > 0)
            ]

        if not active_workers:
            try:
                return self.frame_queue.get(block=block, timeout=timeout)
            except queue.Empty:
                return None

        n = len(active_workers)
        start_idx = self._rr_index % n
        end_time = time.monotonic() + (timeout if timeout is not None else 0.0)

        while True:
            for i in range(n):
                idx = (start_idx + i) % n
                worker = active_workers[idx]
                packet = worker.frame_buffer.get(block=False)
                if packet is not None:
                    self._rr_index = (idx + 1) % n
                    return packet

            # Check fallback queue
            try:
                return self.frame_queue.get_nowait()
            except queue.Empty:
                pass

            if not block:
                return None

            if timeout is not None and time.monotonic() >= end_time:
                return None

            time.sleep(0.005)

    def get_latest_frame(self, camera_id: str) -> Optional[FramePacket]:
        worker = self.workers.get(camera_id)
        if worker and worker.latest_packet:
            return worker.latest_packet
        return None

    # =========================================================================
    # 4. SHUTDOWN & CLEANUP (Requirement 1, 24)
    # =========================================================================
    def shutdown(self):
        """
        Cleanly stops all workers, terminates RTSP streams, closes queues, and releases resources.
        """
        with self._init_lock:
            if not self.is_running:
                return

            logger.info("Initiating CameraManager clean shutdown...")
            self.stop_discovery_loop()
            self.persistence_worker.stop()

            # Stop all active stream workers
            with self._stream_lock:
                for cam_id in list(self.workers.keys()):
                    w = self.workers.pop(cam_id)
                    w.stop()

            # Signal consumer threads to stop
            self._stop_event.set()
            self.is_running = False

            # Clear remaining frames in queue
            while not self.frame_queue.empty():
                try:
                    self.frame_queue.get_nowait()
                except Exception:
                    break

            for t in self.pipeline_threads:
                t.join(timeout=1.5)
            self.pipeline_threads.clear()

            logger.info("CameraManager shutdown complete.")

    def stop_workers(self):
        """Alias for shutdown()."""
        self.shutdown()
