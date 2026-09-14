"""
Detection models module for Vehicle and License Plate Dual-Stage Detection.
"""
from .detector import (
    BaseInferenceEngine,
    YOLOVehicleDetector,
    YOLOLicensePlateDetector,
    DetectionBox,
)

__all__ = [
    "BaseInferenceEngine",
    "YOLOVehicleDetector",
    "YOLOLicensePlateDetector",
    "DetectionBox",
]
