"""
=============================================================================
Stage 2: Spatial-Temporal SORT Tracking & Best-Frame Sharpness Selection
=============================================================================
- Real-time Kalman Filter Bounding Box Tracker
- Linear Sum Assignment / Hungarian Matching via IoU Cost Matrix
- Temporal Frame Accumulation (5-10 consecutive frames)
- Laplacian Variance Quality Scoring for Motion-Blur Rejection
- OCR Result Caching per Track to optimize frame latency under 50ms
=============================================================================
"""

import time
from typing import List, Tuple, Optional, Dict, Any
import cv2
import numpy as np

from ..models.detector import DetectionBox
from ..config import ANPRConfig, DEFAULT_CONFIG

try:
    from scipy.optimize import linear_sum_assignment
except ImportError:
    linear_sum_assignment = None


def calculate_laplacian_sharpness(image: np.ndarray) -> float:
    """
    Computes the focus/sharpness metric using the Variance of the Laplacian.
    Blurry or motion-distorted frames produce low variance; crisp character
    edges produce high variance:
        Sharpness = Var(Laplacian(I))
    """
    if image is None or image.size == 0:
        return 0.0
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    # Compute Laplacian with 64-bit float to prevent overflow
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    variance = laplacian.var()
    return float(variance)


def convert_bbox_to_z(bbox: List[int]) -> np.ndarray:
    """
    Takes [x1, y1, x2, y2] and returns observation vector [u, v, s, r]^T
    where u, v are center coordinates, s is scale/area, and r is aspect ratio.
    """
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = bbox[0] + w / 2.0
    y = bbox[1] + h / 2.0
    s = w * h  # scale (area)
    r = w / float(h) if h > 0 else 1.0  # aspect ratio
    return np.array([x, y, s, r]).reshape((4, 1))


def convert_x_to_bbox(x: np.ndarray, score: float = 0.0) -> List[int]:
    """
    Takes state vector [u, v, s, r, u_dot, v_dot, s_dot]^T and returns [x1, y1, x2, y2].
    """
    x_arr = np.asarray(x, dtype=np.float64).flatten()
    w = float(np.sqrt(max(0.0, float(x_arr[2]) * float(x_arr[3]))))
    h = float(x_arr[2] / w) if w > 0 else 0.0
    x1 = int(round(float(x_arr[0]) - w / 2.0))
    y1 = int(round(float(x_arr[1]) - h / 2.0))
    x2 = int(round(float(x_arr[0]) + w / 2.0))
    y2 = int(round(float(x_arr[1]) + h / 2.0))
    return [x1, y1, x2, y2]


class KalmanBoxTracker:
    """
    Lightweight, high-performance Kalman Filter Tracker for 2D bounding boxes.
    Tracks state: [u, v, s, r, u_dot, v_dot, s_dot]^T (position, scale, velocity).
    """

    count = 0

    def __init__(self, bbox: List[int]):
        # Define constant velocity motion model
        self.dim_x = 7
        self.dim_z = 4

        # State transition matrix F
        self.F = np.eye(self.dim_x)
        for i in range(3):
            self.F[i, i + 4] = 1.0  # dt = 1 frame

        # Measurement function H
        self.H = np.zeros((self.dim_z, self.dim_x))
        for i in range(self.dim_z):
            self.H[i, i] = 1.0

        # Measurement uncertainty R
        self.R = np.eye(self.dim_z)
        self.R[2:, 2:] *= 10.0

        # State covariance P
        self.P = np.eye(self.dim_x) * 10.0
        self.P[4:, 4:] *= 1000.0  # High initial velocity uncertainty

        # Process covariance Q
        self.Q = np.eye(self.dim_x)
        self.Q[4:, 4:] *= 0.01

        # Initial state x
        self.x = np.zeros((self.dim_x, 1))
        self.x[:4] = convert_bbox_to_z(bbox)

        self.time_since_update = 0
        self.id = KalmanBoxTracker.count
        KalmanBoxTracker.count += 1
        self.history = []
        self.hits = 0
        self.hit_streak = 0
        self.age = 0

    def update(self, bbox: List[int]):
        """Updates state with observed bounding box measurement."""
        self.time_since_update = 0
        self.history = []
        self.hits += 1
        self.hit_streak += 1

        # Measurement update
        z = convert_bbox_to_z(bbox)
        y = z - np.dot(self.H, self.x)
        S = np.dot(self.H, np.dot(self.P, self.H.T)) + self.R
        K = np.dot(np.dot(self.P, self.H.T), np.linalg.inv(S))
        self.x = self.x + np.dot(K, y)
        I = np.eye(self.dim_x)
        self.P = np.dot(I - np.dot(K, self.H), self.P)

    def predict(self, dt: float = 1.0) -> List[int]:
        """Advances state vector forward by one time step using given dt."""
        # Update state transition matrix F with dt
        self.F[0, 4] = dt
        self.F[1, 5] = dt
        self.F[2, 6] = dt
        
        if (self.x[6] + self.x[2]) <= 0:
            self.x[6] *= 0.0
        self.x = np.dot(self.F, self.x)
        self.P = np.dot(np.dot(self.F, self.P), self.F.T) + self.Q

        self.age += 1
        if self.time_since_update > 0:
            self.hit_streak = 0
        self.time_since_update += 1
        self.history.append(convert_x_to_bbox(self.x))
        return self.history[-1]

    def get_state(self) -> List[int]:
        """Returns current bounding box estimate."""
        return convert_x_to_bbox(self.x)


def calculate_iou_matrix(boxes_a: np.ndarray, boxes_b: np.ndarray) -> np.ndarray:
    """Computes pairwise IoU between two sets of bounding boxes."""
    if len(boxes_a) == 0 or len(boxes_b) == 0:
        return np.empty((0, 0))

    area_a = (boxes_a[:, 2] - boxes_a[:, 0]) * (boxes_a[:, 3] - boxes_a[:, 1])
    area_b = (boxes_b[:, 2] - boxes_b[:, 0]) * (boxes_b[:, 3] - boxes_b[:, 1])

    iou_matrix = np.zeros((len(boxes_a), len(boxes_b)), dtype=np.float32)
    for i, a in enumerate(boxes_a):
        xx1 = np.maximum(a[0], boxes_b[:, 0])
        yy1 = np.maximum(a[1], boxes_b[:, 1])
        xx2 = np.minimum(a[2], boxes_b[:, 2])
        yy2 = np.minimum(a[3], boxes_b[:, 3])

        w = np.maximum(0.0, xx2 - xx1)
        h = np.maximum(0.0, yy2 - yy1)
        inter = w * h
        union = area_a[i] + area_b - inter
        iou_matrix[i, :] = inter / np.maximum(union, 1e-6)

    return iou_matrix


def linear_assignment(cost_matrix: np.ndarray) -> np.ndarray:
    """Hungarian algorithm solver with SciPy or pure NumPy fallback."""
    if linear_sum_assignment is not None:
        x, y = linear_sum_assignment(cost_matrix)
        return np.array(list(zip(x, y)))
    # Greedy fallback assignment if scipy is absent
    if cost_matrix.size == 0:
        return np.empty((0, 2), dtype=int)
    matches = []
    matrix = cost_matrix.copy()
    for _ in range(min(matrix.shape)):
        min_idx = np.unravel_index(np.argmin(matrix), matrix.shape)
        if matrix[min_idx] >= 1e5:
            break
        matches.append([min_idx[0], min_idx[1]])
        matrix[min_idx[0], :] = 1e5
        matrix[:, min_idx[1]] = 1e5
    return np.array(matches, dtype=int)


class TrackedVehicle:
    """
    Maintains temporal state for a single vehicle across 5-10 frames:
    - Kalman tracker instance
    - Buffer of recent plate crops + timestamps
    - Laplacian sharpness metrics
    - Cached OCR plate string and confidence (to avoid re-OCRing redundant frames)
    """

    def __init__(self, track_id: int, initial_box: DetectionBox, max_buffer: int = 8):
        self.track_id = track_id
        self.vehicle_label = initial_box.label
        self.max_buffer = max_buffer
        
        # Spatial-temporal buffer: list of dicts with crop, plate_box, sharpness, timestamp
        self.plate_buffer: List[Dict[str, Any]] = []
        
        # Cached OCR result for tracklet
        self.recognized_plate: Optional[str] = None
        self.ocr_confidence: float = 0.0
        self.syntax_valid: bool = False
        self.last_ocr_timestamp: float = 0.0

        # Optimization: Plate crop location caching relative to vehicle bbox
        self.last_plate_box: Optional[DetectionBox] = None
        self.last_plate_crop: Optional[np.ndarray] = None
        self.last_plate_detection_time: float = 0.0
        self.relative_plate_norm: Optional[List[float]] = None  # [rx1, ry1, rx2, ry2] normalized to vehicle bbox

    def record_plate_detection(
        self,
        plate_box: DetectionBox,
        plate_crop: np.ndarray,
        veh_box: DetectionBox,
        current_time: float
    ):
        """Records a successful plate detection and normalizes plate coordinates relative to vehicle."""
        self.last_plate_box = plate_box
        self.last_plate_crop = plate_crop
        self.last_plate_detection_time = current_time

        vx1, vy1, vx2, vy2 = veh_box.xyxy
        vw = max(1, vx2 - vx1)
        vh = max(1, vy2 - vy1)
        px1, py1, px2, py2 = plate_box.xyxy

        self.relative_plate_norm = [
            max(0.0, min(1.0, (px1 - vx1) / float(vw))),
            max(0.0, min(1.0, (py1 - vy1) / float(vh))),
            max(0.0, min(1.0, (px2 - vx1) / float(vw))),
            max(0.0, min(1.0, (py2 - vy1) / float(vh)))
        ]

    def get_estimated_plate_box_and_crop(
        self,
        frame: np.ndarray,
        veh_box: DetectionBox
    ) -> Optional[Tuple[DetectionBox, np.ndarray]]:
        """
        Estimates plate crop directly from vehicle bounding box using cached relative geometry.
        Avoids running heavy plate detection YOLO on every frame for confirmed vehicles (Req 9).
        """
        if not self.relative_plate_norm or frame is None or frame.size == 0:
            return None

        vx1, vy1, vx2, vy2 = veh_box.xyxy
        vw = max(1, vx2 - vx1)
        vh = max(1, vy2 - vy1)
        rx1, ry1, rx2, ry2 = self.relative_plate_norm

        px1 = int(vx1 + rx1 * vw)
        py1 = int(vy1 + ry1 * vh)
        px2 = int(vx1 + rx2 * vw)
        py2 = int(vy1 + ry2 * vh)

        h_img, w_img = frame.shape[:2]
        px1 = max(0, min(w_img - 5, px1))
        py1 = max(0, min(h_img - 5, py1))
        px2 = max(px1 + 10, min(w_img, px2))
        py2 = max(py1 + 5, min(h_img, py2))

        crop = frame[py1:py2, px1:px2]
        if crop.size == 0:
            return None

        prev_conf = self.last_plate_box.confidence if self.last_plate_box else 0.88
        est_box = DetectionBox(
            xyxy=[px1, py1, px2, py2],
            confidence=prev_conf,
            class_id=0,
            label="plate"
        )
        return est_box, crop

    def add_plate_observation(
        self,
        plate_crop: np.ndarray,
        plate_box: DetectionBox,
        timestamp: float
    ):
        """Adds a new plate crop to the temporal buffer and scores its optical sharpness."""
        if plate_crop is None or plate_crop.size == 0:
            return

        sharpness = calculate_laplacian_sharpness(plate_crop)
        obs = {
            "crop": plate_crop,
            "box": plate_box,
            "sharpness": sharpness,
            "timestamp": timestamp,
            "area": plate_box.area
        }
        self.plate_buffer.append(obs)
        if len(self.plate_buffer) > self.max_buffer:
            self.plate_buffer.pop(0)

    def get_best_plate_crop(self) -> Optional[Dict[str, Any]]:
        """
        Selects the sharpest, highest-quality frame from the recent tracklet buffer.
        Rejects motion-blurred and dark occluded frames.
        """
        if not self.plate_buffer:
            return None
        # Rank by optical sharpness (variance of Laplacian)
        return max(self.plate_buffer, key=lambda x: x["sharpness"])

    def update_ocr_result(self, plate_text: str, confidence: float, is_valid: bool):
        """Updates the cached OCR result if the new recognition is of higher confidence."""
        if confidence > self.ocr_confidence or (is_valid and not self.syntax_valid):
            self.recognized_plate = plate_text
            self.ocr_confidence = confidence
            self.syntax_valid = is_valid
            self.last_ocr_timestamp = time.time()


class SORTTracker:
    """
    Spatial-Temporal Multi-Object Tracker.
    Associates detected vehicles across video frames using IoU overlap & Kalman predictions.
    """

    def __init__(self, config: Optional[ANPRConfig] = None):
        cfg = config or DEFAULT_CONFIG
        self.max_age = cfg.track_max_age
        self.min_hits = cfg.track_min_hits
        self.iou_threshold = cfg.track_iou_threshold
        self.buffer_size = cfg.temporal_buffer_size

        self.trackers: List[KalmanBoxTracker] = []
        self.vehicle_objects: Dict[int, TrackedVehicle] = {}

    def update(self, detections: List[DetectionBox], dt: float = 1.0) -> List[Tuple[TrackedVehicle, DetectionBox]]:
        """
        Updates trackers with current frame detections.
        Returns: List of (TrackedVehicle, DetectionBox) pairs for actively matched tracks.
        """
        # 1. Predict new locations of existing trackers
        trks = np.zeros((len(self.trackers), 4))
        to_del = []
        for t, trk in enumerate(trks):
            pos = self.trackers[t].predict(dt=dt)
            trk[:] = [pos[0], pos[1], pos[2], pos[3]]
            if np.any(np.isnan(pos)):
                to_del.append(t)
        trks = np.ma.compress_rows(np.ma.masked_invalid(trks))
        for t in reversed(to_del):
            del self.trackers[t]

        # 2. Compute IoU Cost Matrix between predictions and detections
        dets = np.array([d.xyxy for d in detections]) if detections else np.empty((0, 4))
        matched, unmatched_dets, unmatched_trks = self._associate_detections_to_trackers(dets, trks)

        # 3. Update matched trackers with assigned detections
        active_pairs = []
        for t_idx, d_idx in matched:
            tracker = self.trackers[t_idx]
            det_box = detections[d_idx]
            tracker.update(det_box.xyxy)

            # Get or create TrackedVehicle entity
            if tracker.id not in self.vehicle_objects:
                self.vehicle_objects[tracker.id] = TrackedVehicle(tracker.id, det_box, self.buffer_size)
            
            veh_obj = self.vehicle_objects[tracker.id]
            if tracker.hits >= self.min_hits or tracker.age <= 1:
                active_pairs.append((veh_obj, det_box))

        # 4. Create and initialize new trackers for unmatched detections
        for i in unmatched_dets:
            det_box = detections[i]
            trk = KalmanBoxTracker(det_box.xyxy)
            self.trackers.append(trk)
            veh_obj = TrackedVehicle(trk.id, det_box, self.buffer_size)
            self.vehicle_objects[trk.id] = veh_obj
            active_pairs.append((veh_obj, det_box))

        # 5. Remove stale trackers
        i = len(self.trackers)
        for trk in reversed(self.trackers):
            i -= 1
            if trk.time_since_update > self.max_age:
                self.vehicle_objects.pop(trk.id, None)
                self.trackers.pop(i)

        return active_pairs

    def predict_only(self, dt: float = 1.0) -> List[Tuple[TrackedVehicle, DetectionBox]]:
        """
        Advances Kalman state predictions for all active trackers without running YOLO detector (Req 7, 8).
        Ensures continuous tracking continuity and accurate box prediction while eliminating detector compute.
        """
        active_pairs = []
        to_del = []
        for t, trk in enumerate(self.trackers):
            pos = trk.predict(dt=dt)
            if np.any(np.isnan(pos)):
                to_del.append(t)
                continue
            
            x1 = max(0, int(round(pos[0])))
            y1 = max(0, int(round(pos[1])))
            x2 = max(x1 + 10, int(round(pos[2])))
            y2 = max(y1 + 10, int(round(pos[3])))
            
            veh_obj = self.vehicle_objects.get(trk.id)
            if veh_obj:
                det_box = DetectionBox(
                    xyxy=[x1, y1, x2, y2],
                    confidence=0.88,
                    class_id=0,
                    label=veh_obj.vehicle_label
                )
                active_pairs.append((veh_obj, det_box))

        for t in reversed(to_del):
            del self.trackers[t]

        return active_pairs

    def _associate_detections_to_trackers(
        self,
        detections: np.ndarray,
        trackers: np.ndarray
    ) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
        """Assigns detections to tracked objects using Hungarian algorithm."""
        if len(trackers) == 0:
            return [], list(range(len(detections))), []
        if len(detections) == 0:
            return [], [], list(range(len(trackers)))

        iou_matrix = calculate_iou_matrix(trackers, detections)
        # Convert IoU to cost matrix (-IoU)
        matched_indices = linear_assignment(-iou_matrix)

        unmatched_dets = []
        for d in range(len(detections)):
            if d not in matched_indices[:, 1]:
                unmatched_dets.append(d)

        unmatched_trks = []
        for t in range(len(trackers)):
            if t not in matched_indices[:, 0]:
                unmatched_trks.append(t)

        # Filter out matches with low IoU
        matches = []
        for m in matched_indices:
            if iou_matrix[m[0], m[1]] < self.iou_threshold:
                unmatched_trks.append(m[0])
                unmatched_dets.append(m[1])
            else:
                matches.append((m[0], m[1]))

        return matches, unmatched_dets, unmatched_trks


def assess_plate_quality(crop: np.ndarray, box: DetectionBox) -> Tuple[float, float]:
    """
    Evaluates license plate crop quality:
    - Optical sharpness (Laplacian variance)
    - Pixel dimensions (width x height)
    - Aspect ratio suitability
    - Contrast and brightness
    Returns: (sharpness, composite_quality_score)
    """
    if crop is None or crop.size == 0:
        return 0.0, 0.0
    sharpness = calculate_laplacian_sharpness(crop)
    w = max(1, box.width)
    h = max(1, box.height)
    if w < 48 or h < 12:
        return sharpness, sharpness * 0.15

    aspect = w / float(h)
    aspect_factor = 1.0 if (1.4 <= aspect <= 6.5) else 0.6

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if crop.ndim == 3 else crop
    mean_val = float(np.mean(gray))
    brightness_factor = 1.0
    if mean_val < 35 or mean_val > 225:
        brightness_factor = 0.6

    res_factor = min(2.5, max(0.6, w / 70.0))
    composite_quality = sharpness * res_factor * aspect_factor * brightness_factor
    return sharpness, composite_quality


class TrackedPlate:
    """
    Primary State Entity for Plate-First ANPR.
    Maintains optical crop quality metrics, temporal OCR readings, and optional vehicle association.
    """
    def __init__(self, track_id: int, initial_box: DetectionBox, max_buffer: int = 10):
        self.track_id = track_id
        self.last_plate_box: DetectionBox = initial_box
        self.max_buffer = max_buffer
        self.plate_buffer: List[Dict[str, Any]] = []

        self.best_crop: Optional[np.ndarray] = None
        self.best_crop_box: Optional[DetectionBox] = initial_box
        self.best_crop_quality: float = 0.0
        self.best_sharpness: float = 0.0

        self.last_ocr_time: float = 0.0
        self.last_ocr_text: str = ""
        self.best_ocr_confidence: float = 0.0
        self.ocr_history: List[Dict[str, Any]] = []

        self.recognized_plate: Optional[str] = None
        self.ocr_confidence: float = 0.0
        self.syntax_valid: bool = False
        self.validation_status: str = "DETECTED"
        self.plate_category: str = "STANDARD_PRIVATE"
        self.number_type: str = "GENERAL"
        self.state_code: str = ""
        self.state_name: str = ""
        self.is_multiline: bool = False

        # Optional / Secondary Vehicle Association
        self.associated_vehicle_box: Optional[DetectionBox] = None
        self.associated_vehicle_type: str = "Motor Vehicle"
        self.associated_vehicle_id: Optional[int] = None

        # Tracking telemetry
        self.first_seen_time = time.time()
        self.last_seen_time = time.time()
        self.total_observations = 0
        self.hits = 1
        self.age = 1
        self.time_since_update = 0
        self.tracking_confidence = 1.0

    def add_observation(
        self,
        plate_crop: np.ndarray,
        plate_box: DetectionBox,
        timestamp: float
    ) -> Tuple[float, float]:
        """
        Records an optical plate observation.
        Computes sharpness & composite quality, updating best crop if current frame is superior.
        """
        self.last_seen_time = timestamp
        self.last_plate_box = plate_box
        self.total_observations += 1

        if plate_crop is None or plate_crop.size == 0:
            return 0.0, 0.0

        sharpness, quality = assess_plate_quality(plate_crop, plate_box)
        obs = {
            "crop": plate_crop,
            "box": plate_box,
            "sharpness": sharpness,
            "quality": quality,
            "timestamp": timestamp,
            "area": plate_box.area
        }
        self.plate_buffer.append(obs)
        if len(self.plate_buffer) > self.max_buffer:
            self.plate_buffer.pop(0)

        # Update best crop if superior
        if quality > self.best_crop_quality or self.best_crop is None:
            self.best_crop = plate_crop.copy()
            self.best_crop_box = plate_box
            self.best_crop_quality = quality
            self.best_sharpness = sharpness

        return sharpness, quality

    def get_best_crop(self) -> Optional[Dict[str, Any]]:
        """Returns the strongest plate crop based on composite quality score."""
        if not self.plate_buffer:
            if self.best_crop is not None:
                return {
                    "crop": self.best_crop,
                    "box": self.best_crop_box or self.last_plate_box,
                    "sharpness": self.best_sharpness,
                    "quality": self.best_crop_quality,
                    "timestamp": self.last_seen_time
                }
            return None
        return max(self.plate_buffer, key=lambda x: x.get("quality", 0.0))

    def should_run_ocr(
        self,
        current_time: float,
        current_quality: float,
        current_box: DetectionBox
    ) -> bool:
        """
        Selective OCR Gatekeeper (Section 12, 20):
        Avoids wasting compute on redundant frames or low-resolution crops.
        """
        # 1. Do not OCR tiny crops below readable resolution (wait for better frame)
        if current_box.width < 48 or current_box.height < 12:
            return False

        # 2. First observation for a newly detected plate track
        if self.recognized_plate is None:
            return True

        # 3. Previous OCR was invalid/uncertain and minimum delay elapsed
        if not self.syntax_valid and (current_time - self.last_ocr_time) >= 0.4:
            return True

        # 4. Crop quality improved significantly (>25% higher than previous best)
        if current_quality > (self.best_crop_quality * 1.25) and current_quality > 40.0:
            return True

        # 5. Periodic recheck for unconfirmed track
        if (current_time - self.last_ocr_time) >= 1.5 and self.ocr_confidence < 0.85:
            return True

        return False

    def update_ocr_result(
        self,
        plate_text: str,
        confidence: float,
        is_valid: bool,
        validation_status: str = "VALID",
        plate_category: str = "STANDARD_PRIVATE",
        number_type: str = "GENERAL",
        state_code: str = "",
        state_name: str = "",
        is_multiline: bool = False
    ):
        """Updates cached OCR result and records reading in multi-frame history."""
        now = time.time()
        self.last_ocr_time = now
        self.last_ocr_text = plate_text

        self.ocr_history.append({
            "text": plate_text,
            "confidence": confidence,
            "is_valid": is_valid,
            "timestamp": now
        })
        if len(self.ocr_history) > 15:
            self.ocr_history.pop(0)

        # Update confirmed result if higher confidence or higher validity
        if confidence > self.ocr_confidence or (is_valid and not self.syntax_valid):
            self.recognized_plate = plate_text
            self.ocr_confidence = confidence
            self.syntax_valid = is_valid
            self.validation_status = validation_status
            self.plate_category = plate_category
            self.number_type = number_type
            self.state_code = state_code
            self.state_name = state_name
            self.is_multiline = is_multiline

    def associate_vehicle(
        self,
        vehicle_box: Optional[DetectionBox],
        vehicle_type: str = "Motor Vehicle"
    ):
        """Associates secondary vehicle context with the primary plate track."""
        self.associated_vehicle_box = vehicle_box
        self.associated_vehicle_type = vehicle_type or "Motor Vehicle"


class PlateSORTTracker:
    """
    Primary Spatial-Temporal Plate Tracker.
    Directly tracks license plate bounding boxes across frames using Kalman filtering and Hungarian matching.
    Supports detector skipping (predict_only) when tracks are confident and stable.
    """
    def __init__(self, config: Optional[ANPRConfig] = None):
        cfg = config or DEFAULT_CONFIG
        self.max_age = cfg.track_max_age
        self.min_hits = cfg.track_min_hits
        self.iou_threshold = getattr(cfg, "plate_tracking_iou_thresh", 0.25)
        self.buffer_size = cfg.temporal_buffer_size

        self.trackers: List[KalmanBoxTracker] = []
        self.plate_objects: Dict[int, TrackedPlate] = {}

    def update(
        self,
        detections: List[DetectionBox],
        dt: float = 1.0
    ) -> List[Tuple[TrackedPlate, DetectionBox]]:
        """
        Updates plate trackers with full-frame detector outputs.
        Returns: List of (TrackedPlate, DetectionBox) pairs.
        """
        # 1. Advance existing Kalman predictions
        trks = np.zeros((len(self.trackers), 4))
        to_del = []
        for t, trk in enumerate(self.trackers):
            pos = trk.predict(dt=dt)
            trks[t, :] = [pos[0], pos[1], pos[2], pos[3]]
            if np.any(np.isnan(pos)):
                to_del.append(t)
        trks = np.ma.compress_rows(np.ma.masked_invalid(trks))
        for t in reversed(to_del):
            del self.trackers[t]

        # 2. Hungarian IoU matching between detections and predictions
        dets = np.array([d.xyxy for d in detections]) if detections else np.empty((0, 4))
        matched, unmatched_dets, unmatched_trks = self._associate_detections_to_trackers(dets, trks)

        # 3. Update matched trackers
        active_pairs = []
        for t_idx, d_idx in matched:
            tracker = self.trackers[t_idx]
            det_box = detections[d_idx]
            tracker.update(det_box.xyxy)

            if tracker.id not in self.plate_objects:
                self.plate_objects[tracker.id] = TrackedPlate(tracker.id, det_box, self.buffer_size)

            plate_obj = self.plate_objects[tracker.id]
            plate_obj.hits = tracker.hits
            plate_obj.age = tracker.age
            plate_obj.time_since_update = 0
            plate_obj.tracking_confidence = min(1.0, tracker.hit_streak / 3.0)

            if tracker.hits >= self.min_hits or tracker.age <= 1:
                active_pairs.append((plate_obj, det_box))

        # 4. Create new trackers for unmatched detections
        for i in unmatched_dets:
            det_box = detections[i]
            trk = KalmanBoxTracker(det_box.xyxy)
            self.trackers.append(trk)
            plate_obj = TrackedPlate(trk.id, det_box, self.buffer_size)
            self.plate_objects[trk.id] = plate_obj
            active_pairs.append((plate_obj, det_box))

        # 5. Prune dead trackers
        i = len(self.trackers)
        for trk in reversed(self.trackers):
            i -= 1
            if trk.time_since_update > self.max_age:
                self.plate_objects.pop(trk.id, None)
                self.trackers.pop(i)

        return active_pairs

    def predict_only(self, dt: float = 1.0) -> List[Tuple[TrackedPlate, DetectionBox]]:
        """
        Advances Kalman state predictions for all active plate tracks without running YOLO plate detector.
        Provides <1ms tracking continuity during non-detector frames.
        """
        active_pairs = []
        to_del = []
        for t, trk in enumerate(self.trackers):
            pos = trk.predict(dt=dt)
            if np.any(np.isnan(pos)):
                to_del.append(t)
                continue

            x1 = max(0, int(round(pos[0])))
            y1 = max(0, int(round(pos[1])))
            x2 = max(x1 + 10, int(round(pos[2])))
            y2 = max(y1 + 10, int(round(pos[3])))

            plate_obj = self.plate_objects.get(trk.id)
            if plate_obj:
                plate_obj.hits = trk.hits
                plate_obj.age = trk.age
                plate_obj.time_since_update = trk.time_since_update
                plate_obj.tracking_confidence = max(0.5, 1.0 - (trk.time_since_update * 0.15))

                prev_conf = plate_obj.last_plate_box.confidence if plate_obj.last_plate_box else 0.85
                det_box = DetectionBox(
                    x1=x1, y1=y1, x2=x2, y2=y2,
                    confidence=prev_conf,
                    class_id=0,
                    label="License Plate"
                )
                active_pairs.append((plate_obj, det_box))

        for t in reversed(to_del):
            del self.trackers[t]

        return active_pairs

    def _associate_detections_to_trackers(
        self,
        detections: np.ndarray,
        trackers: np.ndarray
    ) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
        """Hungarian algorithm solver matching plate detections to tracked boxes."""
        if len(trackers) == 0:
            return [], list(range(len(detections))), []
        if len(detections) == 0:
            return [], [], list(range(len(trackers)))

        iou_matrix = calculate_iou_matrix(trackers, detections)
        matched_indices = linear_assignment(-iou_matrix)

        unmatched_dets = []
        for d in range(len(detections)):
            if d not in matched_indices[:, 1]:
                unmatched_dets.append(d)

        unmatched_trks = []
        for t in range(len(trackers)):
            if t not in matched_indices[:, 0]:
                unmatched_trks.append(t)

        matches = []
        for m in matched_indices:
            if iou_matrix[m[0], m[1]] < self.iou_threshold:
                unmatched_trks.append(m[0])
                unmatched_dets.append(m[1])
            else:
                matches.append((m[0], m[1]))

        return matches, unmatched_dets, unmatched_trks
