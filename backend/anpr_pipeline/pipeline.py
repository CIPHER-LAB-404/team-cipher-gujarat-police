"""
=============================================================================
Gujarat Police Sentinel - Two-Stage High-Throughput ANPR Pipeline
=============================================================================
Unified Master Pipeline integrating:
- Stage 1: Primary YOLO Vehicle Detection (Car, Bike, Bus, Truck)
- Stage 2: Secondary YOLO License Plate Localization on Vehicle RoIs
- Stage 3: Spatial-Temporal SORT Tracking & Multi-Frame Temporal Aggregator
- Stage 4: Visual Plate Category Classifier (Color / Geometry)
- Stage 5: Multi-Variant Sequence OCR Engine
- Stage 6: Indian RTO MoRTH Registration Rule Engine
- Stage 7: Evidence-based Category Fusion & Choice/Fancy pattern evaluation
- Latency Profiler targeting <50ms frame execution budget
=============================================================================
"""

import time
import os
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple

import cv2
import numpy as np

from .config import ANPRConfig, DEFAULT_CONFIG
from .models.detector import YOLOVehicleDetector, YOLOLicensePlateDetector, DetectionBox
from .tracking.sort_tracker import SORTTracker, TrackedVehicle, PlateSORTTracker, TrackedPlate, assess_plate_quality
from .ocr.lprnet_crnn import PlateOCREngine, OCRResult
from .postprocess.syntax_validator import IndianPlateSyntaxValidator, PlateValidationResult
from .category_classifier import PlateVisualClassifier, VisualClassificationResult
from .aggregation import MultiFrameAggregator, PlateTracklet
from .preprocessing import PlatePreprocessor
from .unified_source import FramePacket

logger = logging.getLogger("ANPR_Pipeline")


@dataclass
class ANPRDetectionResult:
    """Complete recognition record for a single vehicle/plate in a frame."""
    track_id: int
    plate_number: str
    raw_plate_text: str
    normalized_plate: str
    confidence: float
    vehicle_type: str
    validation_status: str     # "VALID", "PLAUSIBLE", "UNCERTAIN", "INVALID"
    is_valid_format: bool
    plate_category: str        # "STANDARD_PRIVATE", "BHARAT_SERIES", "TRANSPORT_COMMERCIAL", etc.
    number_type: str           # "GENERAL", "CHOICE_FANCY_PATTERN"
    fancy_pattern_description: str
    state_code: str
    state_name: str
    is_legacy_state: bool
    tracking_state: str        # "DETECTED", "CANDIDATE", "STABILIZING", "CONFIRMED", "FINALIZED"
    is_multiline: bool
    vehicle_bbox: List[int]    # [x1, y1, x2, y2]
    plate_bbox: List[int]      # [x1, y1, x2, y2]
    sharpness_score: float
    corrections_applied: List[str]
    snapshot_path: str = ""

    # Backwards compatibility
    @property
    def plate_type(self) -> str:
        return self.plate_category

    def __post_init__(self):
        self.track_id = int(self.track_id) if self.track_id is not None else 0
        self.confidence = float(self.confidence) if self.confidence is not None else 0.0
        self.vehicle_bbox = [int(x) for x in self.vehicle_bbox] if self.vehicle_bbox else [0, 0, 0, 0]
        self.plate_bbox = [int(x) for x in self.plate_bbox] if self.plate_bbox else [0, 0, 0, 0]
        self.sharpness_score = float(self.sharpness_score) if self.sharpness_score is not None else 0.0


@dataclass
class FrameTelemetry:
    """Performance latency profiling across each pipeline stage."""
    stage1_plate_ms: float = 0.0
    stage2_tracking_ms: float = 0.0
    stage3_ocr_ms: float = 0.0
    stage4_syntax_ms: float = 0.0
    stage5_vehicle_ms: float = 0.0
    total_pipeline_ms: float = 0.0
    fps: float = 0.0

    # Backwards compatibility properties
    @property
    def stage1_vehicle_ms(self) -> float:
        return self.stage5_vehicle_ms

    @stage1_vehicle_ms.setter
    def stage1_vehicle_ms(self, val: float):
        self.stage5_vehicle_ms = val

    @property
    def stage2_plate_ms(self) -> float:
        return self.stage1_plate_ms

    @stage2_plate_ms.setter
    def stage2_plate_ms(self, val: float):
        self.stage1_plate_ms = val

    @property
    def stage4_ocr_ms(self) -> float:
        return self.stage3_ocr_ms

    @stage4_ocr_ms.setter
    def stage4_ocr_ms(self, val: float):
        self.stage3_ocr_ms = val

    @property
    def stage5_syntax_ms(self) -> float:
        return self.stage4_syntax_ms

    @stage5_syntax_ms.setter
    def stage5_syntax_ms(self, val: float):
        self.stage4_syntax_ms = val


@dataclass
class ANPRFrameOutput:
    """Master output container for a processed frame."""
    camera_id: str
    timestamp: str
    detections: List[ANPRDetectionResult]
    active_tracks_count: int
    telemetry: FrameTelemetry
    annotated_frame: Optional[np.ndarray] = None
    finalized_events: List[Dict[str, Any]] = field(default_factory=list)


class ANPRTwoStagePipeline:
    """
    Plate-First High-Throughput ANPR Pipeline.
    Processing Order:
    LIVE FRAME -> FULL-FRAME PLATE DETECTOR -> PLATE TRACKING -> QUALITY ASSESSMENT
    -> BEST CROP SELECTION -> SELECTIVE OCR -> INDIAN RTO SYNTAX -> TEMPORAL AGGREGATION
    -> SECONDARY / OPTIONAL VEHICLE ENRICHMENT
    """

    def __init__(self, config: Optional[ANPRConfig] = None):
        self.config = config or DEFAULT_CONFIG
        logger.info(f"Initializing Plate-First ANPRPipeline on target device: {self.config.device}")

        # Primary ANPR Engines
        self.plate_detector = YOLOLicensePlateDetector(self.config)
        self.camera_trackers: Dict[str, PlateSORTTracker] = {}
        self.plate_tracker = PlateSORTTracker(self.config)  # Default/global fallback
        self.tracker = self.plate_tracker  # Alias for backward compatibility
        self.ocr_engine = PlateOCREngine(self.config)
        self.syntax_validator = IndianPlateSyntaxValidator(self.config)
        self.visual_classifier = PlateVisualClassifier()
        self.aggregator = MultiFrameAggregator(
            snapshot_dir=os.path.join(os.getcwd(), "outputs", "plates"),
            max_inactive_frames=25
        )

        # Secondary / Optional Vehicle Detector
        self.vehicle_detector = YOLOVehicleDetector(self.config)

        self.last_pts_ms: Dict[str, float] = {}
        self.total_latency_accum = 0.0
        self.camera_detector_state: Dict[str, Dict[str, Any]] = {}
        self.vehicle_cooldown: Dict[str, int] = {}

    def get_tracker(self, camera_id: str) -> PlateSORTTracker:
        """Retrieves or instantiates isolated per-camera PlateSORTTracker."""
        if camera_id not in self.camera_trackers:
            self.camera_trackers[camera_id] = PlateSORTTracker(self.config)
        return self.camera_trackers[camera_id]

    def process_frame(
        self,
        packet: Any,
        camera_id: Optional[str] = None,
        annotate: bool = False
    ) -> ANPRFrameOutput:
        """
        Executes Plate-First ANPR detection, tracking, selective OCR,
        and temporal aggregation on a single frame packet or raw image.
        """
        start_total = time.perf_counter()
        telemetry = FrameTelemetry()

        # Handle both FramePacket and raw numpy array inputs
        if isinstance(packet, np.ndarray):
            frame = packet
            cid = camera_id or "CAM-01"
            current_pts = time.time() * 1000.0
            frame_idx = 0
            camera_name = cid
        elif hasattr(packet, "frame"):
            frame = packet.frame
            cid = packet.camera_id
            current_pts = packet.source_pts_ms
            frame_idx = packet.frame_number
            camera_name = getattr(packet, "camera_name", cid)
        else:
            frame = None
            cid = camera_id or "CAM-01"
            current_pts = time.time() * 1000.0
            frame_idx = 0
            camera_name = cid

        # Obtain camera-isolated tracker instance (Requirement 23)
        tracker = self.get_tracker(cid)

        if frame is None or frame.size == 0:
            return ANPRFrameOutput(
                camera_id=cid,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S IST"),
                detections=[],
                active_tracks_count=len(tracker.trackers),
                telemetry=telemetry
            )

        last_pts = self.last_pts_ms.get(cid, current_pts)
        dt = (current_pts - last_pts) / 1000.0
        if dt <= 0:
            dt = 1.0 / 25.0
        self.last_pts_ms[cid] = current_pts

        now_wall = time.time()
        is_live = (self.config.pipeline_mode == "LIVE")

        # =====================================================================
        # Stage 1: Adaptive Full-Frame Plate Detector Co-Scheduling
        # =====================================================================
        run_plate_detector = True
        if is_live and self.config.adaptive_detector_enabled:
            st = self.camera_detector_state.setdefault(cid, {"last_run": 0.0, "frames": 0})
            st["frames"] += 1
            time_since_last_det = now_wall - st["last_run"]
            active_plates_count = len(tracker.trackers)

            # Decision criteria:
            # - Always run if no active tracks in scene (discover new vehicles)
            # - Always run if max detector interval reached or time > 1.0s (prevent drift)
            # - Always run if any active track is unconfirmed or new and at least 2 frames elapsed
            if active_plates_count == 0:
                run_plate_detector = True
            elif st["frames"] >= self.config.max_detector_interval_frames or time_since_last_det >= 1.0:
                run_plate_detector = True
            else:
                any_unconfirmed = any(
                    (not p.syntax_valid or p.ocr_confidence < 0.75 or p.hits < 2)
                    for p in tracker.plate_objects.values()
                )
                if any_unconfirmed and st["frames"] >= 2:
                    run_plate_detector = True
                else:
                    # Active tracks are confident and stable: skip detector and rely on Kalman tracking!
                    run_plate_detector = False

        # =====================================================================
        # Stage 2: Plate Detection / Kalman Tracking
        # =====================================================================
        if run_plate_detector:
            t0 = time.perf_counter()
            plate_boxes = self.plate_detector.detect(frame)
            telemetry.stage1_plate_ms = round((time.perf_counter() - t0) * 1000.0, 2)

            t1 = time.perf_counter()
            tracked_plates = tracker.update(plate_boxes, dt=dt)
            telemetry.stage2_tracking_ms = round((time.perf_counter() - t1) * 1000.0, 2)

            if is_live and self.config.adaptive_detector_enabled:
                st["last_run"] = now_wall
                st["frames"] = 0
        else:
            telemetry.stage1_plate_ms = 0.0
            t1 = time.perf_counter()
            tracked_plates = tracker.predict_only(dt=dt)
            telemetry.stage2_tracking_ms = round((time.perf_counter() - t1) * 1000.0, 2)

        # =====================================================================
        # Stage 3: Selective OCR, Indian Syntax & Multi-Frame Consensus
        # =====================================================================
        results: List[ANPRDetectionResult] = []
        stage3_accum_ms = 0.0
        stage4_accum_ms = 0.0
        stage5_accum_ms = 0.0

        h_img, w_img = frame.shape[:2]

        for plate_obj, plate_box in tracked_plates:
            px1, py1, px2, py2 = plate_box.xyxy
            px1 = max(0, min(w_img - 1, px1))
            py1 = max(0, min(h_img - 1, py1))
            px2 = max(px1 + 10, min(w_img, px2))
            py2 = max(py1 + 5, min(h_img, py2))

            current_crop = frame[py1:py2, px1:px2]
            sharpness, quality = plate_obj.add_observation(current_crop, plate_box, now_wall)

            best_obs = plate_obj.get_best_crop()
            crop_for_ocr = best_obs["crop"] if best_obs is not None else current_crop
            best_sharpness = best_obs["sharpness"] if best_obs is not None else sharpness

            # Check selective OCR gatekeeper
            should_ocr = plate_obj.should_run_ocr(now_wall, quality, plate_box)

            if should_ocr and crop_for_ocr is not None and crop_for_ocr.size > 0:
                t_ocr = time.perf_counter()
                visual_res = self.visual_classifier.classify_plate_appearance(crop_for_ocr, plate_obj.associated_vehicle_type)
                ocr_out = self.ocr_engine.recognize(crop_for_ocr, plate_obj.associated_vehicle_type)
                stage3_accum_ms += (time.perf_counter() - t_ocr) * 1000.0

                raw_text = ocr_out.text
                ocr_conf = ocr_out.confidence
                is_multiline = ocr_out.is_multiline

                t_syn = time.perf_counter()
                if ocr_out.validation_result:
                    val_res = ocr_out.validation_result
                else:
                    val_res = self.syntax_validator.correct_and_validate(raw_text, ocr_conf, visual_res.suggested_category)
                stage4_accum_ms += (time.perf_counter() - t_syn) * 1000.0

                fused_cat, _ = PlateVisualClassifier.fuse_category(val_res.plate_category, visual_res, plate_obj.associated_vehicle_type)

                plate_obj.update_ocr_result(
                    plate_text=val_res.validated_plate,
                    confidence=val_res.confidence,
                    is_valid=(val_res.validation_status == "VALID"),
                    validation_status=val_res.validation_status,
                    plate_category=fused_cat,
                    number_type=val_res.number_type,
                    state_code=val_res.state_code,
                    state_name=val_res.state_name,
                    is_multiline=is_multiline
                )
            else:
                raw_text = plate_obj.last_ocr_text
                is_multiline = plate_obj.is_multiline
                fused_cat = plate_obj.plate_category

            # Update temporal aggregator
            vbox = plate_obj.associated_vehicle_box.xyxy if plate_obj.associated_vehicle_box else [
                max(0, px1 - 25), max(0, py1 - 60), min(w_img, px2 + 25), min(h_img, py2 + 25)
            ]
            tlet = self.aggregator.update_tracklet(
                track_id=plate_obj.track_id,
                vehicle_type=plate_obj.associated_vehicle_type,
                frame_idx=frame_idx,
                plate_text=plate_obj.recognized_plate or "",
                raw_ocr=raw_text or "",
                ocr_conf=plate_obj.ocr_confidence,
                det_conf=plate_box.confidence,
                sharpness=best_sharpness,
                plate_crop=crop_for_ocr,
                full_frame=frame,
                vehicle_bbox=vbox,
                plate_bbox=plate_box.xyxy,
                validation_result=None,
                visual_result=None
            )

            display_plate = tlet.consensus_plate if tlet.consensus_plate else (plate_obj.recognized_plate or raw_text or "PLATE")
            display_conf = tlet.consensus_confidence if tlet.consensus_confidence > 0 else plate_obj.ocr_confidence
            display_category = tlet.final_category if tlet.final_category != "UNKNOWN" else fused_cat

            det_item = ANPRDetectionResult(
                track_id=plate_obj.track_id,
                plate_number=display_plate,
                raw_plate_text=plate_obj.last_ocr_text or display_plate,
                normalized_plate=display_plate.replace(" ", "").replace("-", ""),
                confidence=display_conf,
                vehicle_type=plate_obj.associated_vehicle_type,
                validation_status=plate_obj.validation_status,
                is_valid_format=(plate_obj.validation_status in ("VALID", "PLAUSIBLE")),
                plate_category=display_category,
                number_type=plate_obj.number_type,
                fancy_pattern_description="",
                state_code=plate_obj.state_code,
                state_name=plate_obj.state_name,
                is_legacy_state=False,
                tracking_state=tlet.state,
                is_multiline=is_multiline,
                vehicle_bbox=vbox,
                plate_bbox=plate_box.xyxy,
                sharpness_score=round(best_sharpness, 2),
                corrections_applied=[],
                snapshot_path=tlet.saved_snapshot_path
            )
            results.append(det_item)

        # =====================================================================
        # Stage 4: Secondary / Optional Vehicle Detection & Enrichment
        # =====================================================================
        unassociated = [p for (p, _) in tracked_plates if p.associated_vehicle_box is None]
        if unassociated and getattr(self.config, "vehicle_enrichment_enabled", True):
            cd = self.vehicle_cooldown.get(cid, 0)
            if cd <= 0:
                t_veh = time.perf_counter()
                veh_boxes = self.vehicle_detector.detect(frame)
                stage5_accum_ms += (time.perf_counter() - t_veh) * 1000.0
                self.vehicle_cooldown[cid] = 10  # cooldown 10 frames

                for p_obj, p_box in tracked_plates:
                    pcx = (p_box.x1 + p_box.x2) / 2.0
                    pcy = (p_box.y1 + p_box.y2) / 2.0
                    best_vb = None
                    best_dist = float("inf")
                    for vb in veh_boxes:
                        if vb.x1 <= pcx <= vb.x2 and vb.y1 <= pcy <= vb.y2:
                            best_vb = vb
                            break
                        dist = np.hypot(pcx - (vb.x1 + vb.x2) / 2.0, pcy - vb.y2)
                        if dist < best_dist and dist < (vb.height * 1.5):
                            best_dist = dist
                            best_vb = vb
                    if best_vb:
                        p_obj.associate_vehicle(best_vb, best_vb.label)
            else:
                self.vehicle_cooldown[cid] = cd - 1

        # Check for finalized tracklets in aggregator
        finalized_events = self.aggregator.prune_and_finalize(frame_idx)

        telemetry.stage3_ocr_ms = round(stage3_accum_ms, 2)
        telemetry.stage4_syntax_ms = round(stage4_accum_ms, 2)
        telemetry.stage5_vehicle_ms = round(stage5_accum_ms, 2)

        total_elapsed = (time.perf_counter() - start_total) * 1000.0
        telemetry.total_pipeline_ms = round(total_elapsed, 2)
        telemetry.fps = round(1000.0 / total_elapsed, 1) if total_elapsed > 0 else 0.0
        self.total_latency_accum += total_elapsed

        annotated_img = None
        if annotate:
            annotated_img = self.annotate_frame(frame.copy(), results, telemetry)

        return ANPRFrameOutput(
            camera_id=cid,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S IST"),
            detections=results,
            active_tracks_count=len(tracker.trackers),
            telemetry=telemetry,
            annotated_frame=annotated_img,
            finalized_events=finalized_events
        )

    def annotate_frame(
        self,
        img: np.ndarray,
        detections: List[ANPRDetectionResult],
        telemetry: FrameTelemetry
    ) -> np.ndarray:
        """
        Renders rich visual HUD overlay directly on the frame:
        - Cyan box for vehicle
        - Color-coded plate box based on validation_status:
            * Emerald Green: VALID
            * Yellow/Amber: PLAUSIBLE (e.g. Legacy, vintage)
            * Orange: UNCERTAIN
            * Crimson Red: INVALID
        - Plate label badge: [PLATE] ([CONF]%) [CATEGORY]
        - Choice / Fancy pattern tag if present
        - Bottom/Top telemetry HUD with FPS & Stage latency
        """
        for d in detections:
            # 1. Vehicle Bounding Box
            vx1, vy1, vx2, vy2 = d.vehicle_bbox
            cv2.rectangle(img, (vx1, vy1), (vx2, vy2), (248, 189, 56), 2)
            veh_tag = f"ID #{d.track_id} {d.vehicle_type}"
            cv2.putText(img, veh_tag, (vx1, max(20, vy1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (248, 189, 56), 2)

            # 2. Plate Bounding Box
            px1, py1, px2, py2 = d.plate_bbox
            status_colors = {
                "VALID": (74, 222, 128),      # Green
                "PLAUSIBLE": (0, 215, 255),    # Yellow/Gold
                "UNCERTAIN": (0, 140, 255),    # Orange
                "INVALID": (80, 80, 240)       # Red
            }
            box_color = status_colors.get(d.validation_status, (74, 222, 128))
            cv2.rectangle(img, (px1, py1), (px2, py2), box_color, 2)

            # 3. Text Badge
            badge_text = f"{d.plate_number} ({int(d.confidence * 100)}%)"
            if d.number_type == "CHOICE_FANCY_PATTERN":
                badge_text += " [FANCY]"

            (tw, th), _ = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.60, 2)
            badge_y1 = max(th + 10, py1 - th - 8)
            cv2.rectangle(img, (px1, badge_y1), (px1 + tw + 10, badge_y1 + th + 8), box_color, -1)
            cv2.putText(img, badge_text, (px1 + 5, badge_y1 + th + 2), cv2.FONT_HERSHEY_SIMPLEX, 0.60, (0, 0, 0), 2)

            # Secondary Category Tag below plate
            cat_label = f"{d.plate_category} | {d.state_name}"
            cv2.putText(img, cat_label, (px1, py2 + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.42, box_color, 1)

        # 4. Telemetry Header HUD
        hud_bg_w = min(img.shape[1], 720)
        cv2.rectangle(img, (0, 0), (hud_bg_w, 36), (15, 23, 42), -1)  # Slate dark bg
        hud_text = f"Sentinel ANPR Vision AI | {telemetry.fps:.1f} FPS | Total: {telemetry.total_pipeline_ms:.1f}ms (Veh: {telemetry.stage1_vehicle_ms:.0f}ms, OCR: {telemetry.stage4_ocr_ms:.0f}ms)"
        cv2.putText(img, hud_text, (12, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (56, 189, 248), 1, cv2.LINE_AA)

        return img
