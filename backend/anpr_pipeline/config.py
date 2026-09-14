"""
=============================================================================
Gujarat Police Sentinel - ANPR Pipeline Configuration
=============================================================================
Centralized configuration for Dual-Stage YOLOv8/v11 Detection,
SORT Tracking, Multi-Line CRNN/LPRNet OCR, and Indian RTO Syntax Engine.
=============================================================================
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class ANPRConfig:
    # -------------------------------------------------------------------------
    # Execution & Hardware Acceleration
    # -------------------------------------------------------------------------
    device: str = "cpu"  # Options: "cuda", "cpu", "tensorrt", "mps"
    fp16: bool = False  # Set True when CUDA is available
    num_threads: int = 4  # CPU threads for ONNX runtime if CPU is used

    # -------------------------------------------------------------------------
    # Live Stream & Low-Latency Analytics Configuration
    # -------------------------------------------------------------------------
    pipeline_mode: str = "LIVE"  # "LIVE" (latency-first, drop-oldest) or "RECORDED" (complete)
    max_live_frame_lag_ms: float = 1800.0  # Max acceptable latency before dropping stale frame in LIVE mode
    live_frame_buffer_size: int = 2  # Bounded per-camera frame slot capacity
    adaptive_detector_enabled: bool = True  # Enable adaptive detector/tracker co-scheduling
    max_detector_interval_frames: int = 5  # Max frames between detector refreshes for stable tracks
    min_vehicle_area_px: int = 1600  # Ignore vehicles smaller than 40x40 px
    max_candidate_vehicles_per_frame: int = 4  # Prioritize top N most prominent candidate vehicles
    plate_recheck_interval_sec: float = 1.5  # Re-run plate detection on confirmed tracks every 1.5s
    ocr_recheck_interval_sec: float = 1.5  # Re-run OCR on confirmed tracks every 1.5s

    # -------------------------------------------------------------------------
    # Model Weights & Paths
    # (Swap out paths below with your trained .pt, .onnx, or .engine files)
    # -------------------------------------------------------------------------
    weights_dir: str = os.path.join(os.path.dirname(__file__), "weights")
    
    # Stage 1: Vehicle Detection (YOLOv8n / YOLO11n)
    vehicle_model_path: str = os.path.join(weights_dir, "yolov8n_vehicle.onnx")
    vehicle_pt_path: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "yolov8n.pt")  # Ultralytics PyTorch fallback
    vehicle_input_size: Tuple[int, int] = (640, 640)
    vehicle_conf_thresh: float = 0.15
    vehicle_iou_thresh: float = 0.45
    # COCO Class IDs for vehicles: 2: car, 3: motorcycle, 5: bus, 7: truck
    vehicle_classes: List[int] = field(default_factory=lambda: [2, 3, 5, 7])

    # Stage 2: License Plate Detection (Custom YOLOv8n-Plate / YOLO11n-Plate)
    plate_model_path: str = os.path.join(weights_dir, "license_plate_detector.onnx")
    plate_pt_path: str = os.path.join(weights_dir, "license_plate_detector.pt")
    plate_input_size: Tuple[int, int] = (640, 640)
    plate_conf_thresh: float = 0.08
    plate_iou_thresh: float = 0.35
    plate_padding_ratio: float = 0.08  # 8% crop padding to avoid clipping plate border rivets

    # Stage 3: Spatial-Temporal Tracking (SORT)
    track_max_age: int = 15  # Max frames to keep dead track
    track_min_hits: int = 1  # Instant 1st-frame detection for single-frame scans and responsive tracking
    track_iou_threshold: float = 0.30
    temporal_buffer_size: int = 8  # Track 5-10 consecutive frames per vehicle

    # Stage 4: OCR Engine (MobileViT v2 / CRNN / FastPlateOCR)
    ocr_model_path: str = os.path.join(weights_dir, "global_mobile_vit_v2_ocr.onnx")
    ocr_config_path: str = os.path.join(weights_dir, "global_mobile_vit_v2_ocr_config.yaml")
    ocr_pt_path: str = os.path.join(weights_dir, "crnn_lprnet.pt")
    ocr_input_size: Tuple[int, int] = (140, 70)  # Width, Height for MobileViT v2
    multiline_aspect_ratio_threshold: float = 2.4  # Plates with W/H < 2.4 are multi-line 2-tier plates

    # OCR Alphabet Vocabulary (Alphanumeric uppercase + Blank token for CTC)
    ocr_characters: str = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    blank_index: int = 0  # Index of CTC blank token

    # -------------------------------------------------------------------------
    # Stage 5: Indian RTO & MoRTH Syntax Specifications
    # -------------------------------------------------------------------------
    # All 36 Indian States & Union Territories
    valid_state_codes: set = field(default_factory=lambda: {
        "AN", "AP", "AR", "AS", "BR", "CG", "CH", "DD", "DL", "DN",
        "GA", "GJ", "HP", "HR", "JH", "JK", "KA", "KL", "LA", "LD",
        "MH", "ML", "MN", "MP", "MZ", "NL", "OD", "OR", "PB", "PY",
        "RJ", "SK", "TN", "TR", "TS", "UK", "UP", "WB", "BH"
    })

    # Standard Regex Patterns for Indian Plates
    # 1. Standard: 2 letters (State) + 1-2 digits (RTO) + 0-4 letters (Series/Class) + 1-4 digits (Num)
    regex_standard: str = r"^[A-Z]{2}[0-9]{1,2}[A-Z]{0,4}[0-9]{1,4}$"
    # 2. Bharat Series: 2 digits (Year) + "BH" + 4 digits + 1-2 letters
    regex_bharat: str = r"^[0-9]{2}BH[0-9]{4}[A-Z]{1,2}$"
    # 3. Defense / Military Vehicles: Upward Arrow (represented by ^ or A) + 2 digits + Letters + Digits
    regex_defense: str = r"^(\^[0-9]{2}[A-Z][0-9]{5,6}[A-Z]|[0-9]{2}[A-Z][0-9]{5,6}[A-Z])$"
    # 4. Commercial / Transport Vehicles (Yellow plate, T/TR/TX/TA/TB series)
    regex_commercial: str = r"^[A-Z]{2}[0-9]{1,2}(T|TR|TX|TA|TB|TC|TD)[A-Z]{0,2}[0-9]{1,4}$"
    # 5. Electric Vehicles (Green plate, EV series)
    regex_ev: str = r"^[A-Z]{2}[0-9]{1,2}[A-Z]{0,2}EV[0-9]{1,4}$"
    # 6. Diplomatic / Consular / UN (Blue plate, CD/CC/UN)
    regex_diplomatic: str = r"^[0-9]{1,3}(CD|CC|UN)[0-9]{1,4}$"
    # 7. Temporary Registration (Yellow/Red, TR/TEMP/CR)
    regex_temporary: str = r"^[A-Z]{2}[0-9]{1,2}(TR|TEMP|CR)[0-9]{1,4}$"
    # 8. Vintage & Classic Vehicles (VA series)
    regex_vintage: str = r"^[A-Z]{2}VA[A-Z]{0,2}[0-9]{4}$"

    # Neural Network Confusion Correction Tables
    digit_to_letter_map: Dict[str, str] = field(default_factory=lambda: {
        '0': 'O', '1': 'I', '2': 'Z', '3': 'E', '4': 'A',
        '5': 'S', '6': 'G', '8': 'B'
    })

    letter_to_digit_map: Dict[str, str] = field(default_factory=lambda: {
        'O': '0', 'Q': '0', 'D': '0',
        'I': '1', 'L': '1', 'T': '1',
        'Z': '2',
        'E': '3',
        'A': '4',
        'S': '5',
        'G': '6', 'C': '6',
        'B': '8',
        'P': '9'
    })


# Global default configuration instance
DEFAULT_CONFIG = ANPRConfig()
