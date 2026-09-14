"""
=============================================================================
Gujarat Police Sentinel - Modular Two-Stage ANPR Pipeline Package
=============================================================================
"""

from .config import ANPRConfig, DEFAULT_CONFIG
from .models.detector import YOLOVehicleDetector, YOLOLicensePlateDetector, DetectionBox
from .tracking.sort_tracker import SORTTracker, TrackedVehicle, calculate_laplacian_sharpness
from .ocr.lprnet_crnn import PlateOCREngine, OCRResult, CTCDecoder
from .postprocess.state_registry import IndianStateRegistry, StateRecord
from .postprocess.syntax_validator import IndianPlateSyntaxValidator, PlateValidationResult, FancyPatternEvaluator
from .category_classifier import PlateVisualClassifier, VisualClassificationResult
from .preprocessing import PlatePreprocessor, QualityMetrics
from .aggregation import MultiFrameAggregator, PlateTracklet, Observation
from .unified_source import UnifiedFrameSource
from .pipeline import (
    ANPRTwoStagePipeline,
    ANPRDetectionResult,
    ANPRFrameOutput,
    FrameTelemetry,
)

__all__ = [
    "ANPRConfig",
    "DEFAULT_CONFIG",
    "YOLOVehicleDetector",
    "YOLOLicensePlateDetector",
    "DetectionBox",
    "SORTTracker",
    "TrackedVehicle",
    "calculate_laplacian_sharpness",
    "PlateOCREngine",
    "OCRResult",
    "CTCDecoder",
    "IndianStateRegistry",
    "StateRecord",
    "IndianPlateSyntaxValidator",
    "PlateValidationResult",
    "FancyPatternEvaluator",
    "PlateVisualClassifier",
    "VisualClassificationResult",
    "PlatePreprocessor",
    "QualityMetrics",
    "MultiFrameAggregator",
    "PlateTracklet",
    "Observation",
    "UnifiedFrameSource",
    "ANPRTwoStagePipeline",
    "ANPRDetectionResult",
    "ANPRFrameOutput",
    "FrameTelemetry",
]
