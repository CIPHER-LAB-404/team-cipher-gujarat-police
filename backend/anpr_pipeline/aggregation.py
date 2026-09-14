"""
=============================================================================
Gujarat Police Sentinel - Multi-Frame Temporal ANPR Aggregator
=============================================================================
- Tracklet history maintenance across consecutive video frames
- Slot-by-slot weighted character consensus voting
- Tracking state machine:
    DETECTED -> OCR_PENDING -> CANDIDATE -> STABILIZING -> CONFIRMED / UNCERTAIN -> FINALIZED
- Best snapshot selection based on sharpness × resolution × confidence
- Snapshot persistence to disk (outputs/plates/YYYY-MM-DD/)
=============================================================================
"""

import os
import time
import datetime
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

import cv2
import numpy as np

from .postprocess.syntax_validator import PlateValidationResult, IndianPlateSyntaxValidator
from .category_classifier import PlateVisualClassifier, VisualClassificationResult
from .preprocessing import PlatePreprocessor


@dataclass
class Observation:
    """A single frame observation of a tracked plate."""
    frame_idx: int
    timestamp: float
    plate_text: str
    raw_ocr: str
    ocr_confidence: float
    detector_confidence: float
    sharpness: float
    plate_crop: np.ndarray
    full_frame: Optional[np.ndarray]
    vehicle_bbox: Tuple[int, int, int, int]
    plate_bbox: Tuple[int, int, int, int]
    validation_result: Optional[PlateValidationResult]
    visual_result: Optional[VisualClassificationResult]


class PlateTracklet:
    """Maintains multi-frame observations and temporal consensus for a tracked vehicle."""

    def __init__(self, track_id: int, vehicle_type: str = "Car"):
        self.track_id = track_id
        self.vehicle_type = vehicle_type
        self.state = "DETECTED"  # "DETECTED", "CANDIDATE", "STABILIZING", "CONFIRMED", "UNCERTAIN", "FINALIZED"
        self.observations: List[Observation] = []
        self.last_seen_frame = 0
        self.last_seen_timestamp = time.time()
        self.best_snapshot_score = -1.0
        self.best_plate_crop: Optional[np.ndarray] = None
        self.best_full_frame: Optional[np.ndarray] = None
        self.best_vehicle_bbox: Tuple[int, int, int, int] = (0, 0, 0, 0)
        self.best_plate_bbox: Tuple[int, int, int, int] = (0, 0, 0, 0)
        self.consensus_plate: str = ""
        self.consensus_confidence: float = 0.0
        self.final_validation_result: Optional[PlateValidationResult] = None
        self.final_category: str = "UNKNOWN"
        self.is_finalized = False
        self.saved_snapshot_path: str = ""

    def add_observation(self, obs: Observation):
        """Appends new frame observation and updates best visual snapshot."""
        self.observations.append(obs)
        self.last_seen_frame = obs.frame_idx
        self.last_seen_timestamp = obs.timestamp

        # Score visual quality of this crop: sharpness * det_conf * ocr_conf
        q_score = (obs.sharpness / 50.0) * (obs.detector_confidence + 0.5) * (obs.ocr_confidence + 0.5)
        if q_score > self.best_snapshot_score:
            self.best_snapshot_score = q_score
            self.best_plate_crop = obs.plate_crop.copy() if obs.plate_crop is not None else None
            self.best_full_frame = obs.full_frame.copy() if obs.full_frame is not None else None
            self.best_vehicle_bbox = obs.vehicle_bbox
            self.best_plate_bbox = obs.plate_bbox

        # Update state progression
        n_obs = len(self.observations)
        if n_obs == 1:
            self.state = "CANDIDATE" if obs.plate_text else "DETECTED"
        elif n_obs < 3:
            self.state = "STABILIZING"
        else:
            self._update_consensus()

    def _update_consensus(self):
        """Performs slot-by-slot weighted character voting across tracklet history."""
        valid_readings = [o for o in self.observations if o.plate_text and len(o.plate_text) >= 4]
        if not valid_readings:
            self.state = "UNCERTAIN"
            return

        # Determine most common length
        lengths = defaultdict(float)
        for o in valid_readings:
            w = (o.ocr_confidence + 0.1) * (min(2.0, o.sharpness / 40.0) + 0.2)
            lengths[len(o.plate_text)] += w

        best_len = max(lengths, key=lengths.get)
        matching_obs = [o for o in valid_readings if len(o.plate_text) == best_len]

        if not matching_obs:
            matching_obs = valid_readings

        # Slot-by-slot weighted voting
        voted_chars = []
        slot_confidences = []

        for slot_idx in range(best_len):
            char_weights = defaultdict(float)
            for o in matching_obs:
                if slot_idx < len(o.plate_text):
                    ch = o.plate_text[slot_idx]
                    weight = o.ocr_confidence * (1.0 + min(1.0, o.sharpness / 80.0))
                    char_weights[ch] += weight

            if char_weights:
                best_char = max(char_weights, key=char_weights.get)
                total_slot_w = sum(char_weights.values())
                slot_conf = char_weights[best_char] / max(0.01, total_slot_w)
                voted_chars.append(best_char)
                slot_confidences.append(slot_conf)
            else:
                voted_chars.append("?")
                slot_confidences.append(0.0)

        raw_consensus = "".join(voted_chars)
        avg_slot_conf = float(np.mean(slot_confidences)) if slot_confidences else 0.0

        # Validate consensus string with Indian registration rule engine
        validator = IndianPlateSyntaxValidator()
        v_res = validator.correct_and_validate(raw_consensus, initial_confidence=avg_slot_conf)

        self.consensus_plate = v_res.validated_plate
        self.consensus_confidence = v_res.confidence
        self.final_validation_result = v_res

        # Fuse category with visual classifier if available
        last_visual = next((o.visual_result for o in reversed(self.observations) if o.visual_result), None)
        if last_visual:
            fused_cat, _ = PlateVisualClassifier.fuse_category(v_res.plate_category, last_visual, self.vehicle_type)
            self.final_category = fused_cat
        else:
            self.final_category = v_res.plate_category

        if v_res.validation_status == "VALID" and avg_slot_conf >= 0.70:
            self.state = "CONFIRMED"
        elif v_res.validation_status in ["VALID", "PLAUSIBLE"]:
            self.state = "CONFIRMED" if len(self.observations) >= 4 else "STABILIZING"
        else:
            self.state = "UNCERTAIN" if len(self.observations) >= 5 else "STABILIZING"


class MultiFrameAggregator:
    """
    Manages active tracklets across a video stream or camera feed.
    Persists finalized plates, triggers database logging, and stores best snapshots.
    """

    def __init__(self, snapshot_dir: str = "outputs/plates", max_inactive_frames: int = 25):
        self.snapshot_dir = snapshot_dir
        self.max_inactive_frames = max_inactive_frames
        self.tracklets: Dict[int, PlateTracklet] = {}
        self.finalized_events: List[Dict[str, Any]] = []

        # Ensure base snapshot directory exists
        os.makedirs(self.snapshot_dir, exist_ok=True)

    def update_tracklet(
        self,
        track_id: int,
        vehicle_type: str,
        frame_idx: int,
        plate_text: str,
        raw_ocr: str,
        ocr_conf: float,
        det_conf: float,
        sharpness: float,
        plate_crop: np.ndarray,
        full_frame: Optional[np.ndarray],
        vehicle_bbox: Tuple[int, int, int, int],
        plate_bbox: Tuple[int, int, int, int],
        validation_result: Optional[PlateValidationResult],
        visual_result: Optional[VisualClassificationResult]
    ) -> PlateTracklet:
        """Adds observation to tracklet, instantiating if new."""
        if track_id not in self.tracklets:
            self.tracklets[track_id] = PlateTracklet(track_id, vehicle_type)

        tracklet = self.tracklets[track_id]
        obs = Observation(
            frame_idx=frame_idx,
            timestamp=time.time(),
            plate_text=plate_text,
            raw_ocr=raw_ocr,
            ocr_confidence=ocr_conf,
            detector_confidence=det_conf,
            sharpness=sharpness,
            plate_crop=plate_crop,
            full_frame=full_frame,
            vehicle_bbox=vehicle_bbox,
            plate_bbox=plate_bbox,
            validation_result=validation_result,
            visual_result=visual_result
        )
        tracklet.add_observation(obs)
        return tracklet

    def prune_and_finalize(self, current_frame_idx: int) -> List[Dict[str, Any]]:
        """
        Finalizes tracklets that have not been observed for max_inactive_frames.
        Saves best snapshot to disk and returns list of completed event dictionaries.
        """
        expired_ids = []
        newly_finalized = []

        for tid, tlet in self.tracklets.items():
            if (current_frame_idx - tlet.last_seen_frame) > self.max_inactive_frames:
                expired_ids.append(tid)
                if not tlet.is_finalized and tlet.consensus_plate:
                    event = self._finalize_tracklet(tlet)
                    if event:
                        newly_finalized.append(event)

        for tid in expired_ids:
            del self.tracklets[tid]

        return newly_finalized

    def _finalize_tracklet(self, tlet: PlateTracklet) -> Optional[Dict[str, Any]]:
        """Saves reference snapshot and generates final event record."""
        tlet.is_finalized = True
        tlet.state = "FINALIZED"

        if not tlet.consensus_plate or len(tlet.consensus_plate) < 4:
            return None

        # Save snapshot
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        daily_dir = os.path.join(self.snapshot_dir, date_str)
        os.makedirs(daily_dir, exist_ok=True)

        filename = f"event_{int(tlet.last_seen_timestamp)}_{tlet.track_id}_{tlet.consensus_plate}.jpg"
        save_path = os.path.join(daily_dir, filename)

        if tlet.best_plate_crop is not None and tlet.best_plate_crop.size > 0:
            cv2.imwrite(save_path, tlet.best_plate_crop)
            tlet.saved_snapshot_path = save_path

        vres = tlet.final_validation_result

        event_dict = {
            "track_id": tlet.track_id,
            "plate_number": tlet.consensus_plate,
            "raw_ocr": tlet.observations[-1].raw_ocr if tlet.observations else tlet.consensus_plate,
            "confidence": round(tlet.consensus_confidence, 3),
            "state": tlet.state,
            "validation_status": vres.validation_status if vres else "PLAUSIBLE",
            "plate_category": tlet.final_category,
            "number_type": vres.number_type if vres else "GENERAL",
            "fancy_pattern_description": vres.fancy_pattern_description if vres else "",
            "state_code": vres.state_code if vres else "",
            "state_name": vres.state_name if vres else "",
            "vehicle_type": tlet.vehicle_type,
            "snapshot_path": tlet.saved_snapshot_path,
            "timestamp": tlet.last_seen_timestamp,
            "observation_count": len(tlet.observations)
        }

        self.finalized_events.append(event_dict)
        return event_dict
