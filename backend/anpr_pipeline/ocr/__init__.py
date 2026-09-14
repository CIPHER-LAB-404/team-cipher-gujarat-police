"""
Optical Character Recognition (OCR) module for Indian Single-Line & Multi-Line Plates.
"""
from .lprnet_crnn import (
    PlateOCREngine,
    OCRResult,
    CTCDecoder,
)
from ..preprocessing import PlatePreprocessor

# Backwards compatibility alias
MultiLinePlateProcessor = PlatePreprocessor

__all__ = [
    "PlateOCREngine",
    "OCRResult",
    "MultiLinePlateProcessor",
    "CTCDecoder",
]
