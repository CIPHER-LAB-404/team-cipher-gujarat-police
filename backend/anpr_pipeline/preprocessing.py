"""
=============================================================================
Gujarat Police Sentinel - Advanced ANPR Preprocessing & Deskewing Engine
=============================================================================
- Geometric perspective deskewing and orientation rectification
- Quantitative image quality assessment (Laplacian blur variance, contrast)
- Multi-variant adaptive preprocessing pipeline (7 distinct image passes)
- Multi-line two-tier plate decomposition for two-wheelers and auto-rickshaws
=============================================================================
"""

import math
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any

import cv2
import numpy as np


@dataclass
class QualityMetrics:
    """Quantitative quality metrics for a license plate crop."""
    laplacian_variance: float  # Sharpness metric (> 80 is sharp, < 35 is blurry)
    is_blurry: bool
    mean_brightness: float     # 0 to 255
    contrast_std: float        # Standard deviation of pixel values
    width: int
    height: int
    is_adequate_resolution: bool


class PlatePreprocessor:
    """
    Production-grade preprocessing engine for Indian HSRP and standard plates.
    Generates multiple enhanced candidate representations for the OCR stage.
    """

    @staticmethod
    def assess_quality(image: np.ndarray) -> QualityMetrics:
        """Computes blur, contrast, and resolution metrics on plate crop."""
        if image is None or image.size == 0:
            return QualityMetrics(
                laplacian_variance=0.0,
                is_blurry=True,
                mean_brightness=0.0,
                contrast_std=0.0,
                width=0,
                height=0,
                is_adequate_resolution=False
            )

        h, w = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
        lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        mean_b = float(np.mean(gray))
        std_b = float(np.std(gray))

        is_adequate = (w >= 36 and h >= 12)
        is_blurry = (lap_var < 45.0)

        return QualityMetrics(
            laplacian_variance=round(lap_var, 2),
            is_blurry=is_blurry,
            mean_brightness=round(mean_b, 1),
            contrast_std=round(std_b, 1),
            width=w,
            height=h,
            is_adequate_resolution=is_adequate
        )

    @staticmethod
    def deskew_plate(image: np.ndarray, max_angle: float = 35.0) -> np.ndarray:
        """
        Straightens rotated or slanted license plates using minimum area bounding box.
        Operates on edges to find plate orientation angle.
        """
        if image is None or image.size == 0 or image.shape[0] < 14 or image.shape[1] < 28:
            return image

        h, w = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image

        # Edge detection
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150, apertureSize=3)

        # Find external contours of characters / plate boundary
        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return image

        # Accumulate angles of dominant contours
        angles = []
        for cnt in contours:
            if cv2.contourArea(cnt) > 40:
                rect = cv2.minAreaRect(cnt)
                angle = rect[-1]
                # OpenCV minAreaRect returns angle in [-90, 0)
                if angle < -45:
                    angle = 90 + angle
                if -max_angle <= angle <= max_angle and abs(angle) > 1.5:
                    angles.append(angle)

        if not angles:
            return image

        median_angle = float(np.median(angles))
        if abs(median_angle) < 1.5:
            return image

        # Rotate image around center
        center = (w // 2, h // 2)
        rot_mat = cv2.getRotationMatrix2D(center, median_angle, 1.0)
        deskewed = cv2.warpAffine(image, rot_mat, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        return deskewed

    @staticmethod
    def generate_ocr_variants(plate_crop: np.ndarray) -> List[Tuple[str, np.ndarray]]:
        """
        Generates 7 distinct image passes tailored for sequence OCR:
        1. Enhanced original (cubic upscaled to target height 64px)
        2. Grayscale + CLAHE (contrast enhancement for stamped rivets and HSRP characters)
        3. Bilateral filter (edge-preserving denoised)
        4. Unsharp mask sharpened (high-frequency crisp edges)
        5. Otsu adaptive binarization (standard dark on light)
        6. Inverted binary threshold (for light on dark plates like EV or military)
        7. Morphological gradient filtered
        """
        if plate_crop is None or plate_crop.size == 0:
            return []

        h, w = plate_crop.shape[:2]
        # Target height: 64 to 96 px
        target_h = max(48, min(96, int(max(h, 64))))
        scale = target_h / float(max(1, h))
        target_w = max(96, int(w * scale))

        # Variant 1: Enhanced original upscaled
        v1_upscaled = cv2.resize(plate_crop, (target_w, target_h), interpolation=cv2.INTER_CUBIC)

        gray = cv2.cvtColor(v1_upscaled, cv2.COLOR_BGR2GRAY) if v1_upscaled.ndim == 3 else v1_upscaled.copy()

        # Variant 2: CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        v2_clahe = clahe.apply(gray)

        # Variant 3: Bilateral filter denoised
        v3_bilateral = cv2.bilateralFilter(v2_clahe, 5, 50, 50)

        # Variant 4: Unsharp mask sharpening
        gaussian = cv2.GaussianBlur(v3_bilateral, (0, 0), 2.0)
        v4_sharpened = cv2.addWeighted(v3_bilateral, 1.5, gaussian, -0.5, 0)

        # Variant 5: Otsu threshold
        _, v5_otsu = cv2.threshold(v3_bilateral, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Variant 6: Inverted threshold
        _, v6_inv = cv2.threshold(v3_bilateral, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Variant 7: Morphological opening
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        v7_morph = cv2.morphologyEx(v3_bilateral, cv2.MORPH_OPEN, kernel)

        return [
            ("bilateral", v3_bilateral),
            ("clahe", v2_clahe),
            ("sharpened", v4_sharpened),
            ("upscaled", v1_upscaled),
            ("otsu", v5_otsu),
            ("otsu_inv", v6_inv),
            ("morph", v7_morph)
        ]

    @staticmethod
    def process_multiline_plate(
        plate_crop: np.ndarray,
        aspect_ratio: float,
        vehicle_type: Optional[str] = None
    ) -> Tuple[np.ndarray, bool]:
        """
        Decomposes 2-tier square plates into a stitched horizontal strip.
        In India, Two-Wheelers and Auto-Rickshaws use two-line plates:
        Line 1: State + RTO code (e.g., GJ 01)
        Line 2: Series + 4-digit sequence (e.g., ER 4492)
        """
        vtype = (vehicle_type or "").lower()
        is_two_wheeler = ("motorcycle" in vtype or "scooter" in vtype or "bike" in vtype or "auto" in vtype)

        # Combine geometric aspect ratio heuristic with vehicle type evidence
        is_multiline = (aspect_ratio < 2.3) or (is_two_wheeler and aspect_ratio < 3.0)

        if not is_multiline or plate_crop is None or plate_crop.shape[0] < 24:
            return plate_crop, False

        h, w = plate_crop.shape[:2]
        split_y = int(h * 0.48)  # Split horizontally between upper and lower tier

        top_tier = plate_crop[0:split_y, :]
        bottom_tier = plate_crop[split_y:, :]

        if top_tier.size == 0 or bottom_tier.size == 0:
            return plate_crop, False

        # Match heights
        target_h = max(top_tier.shape[0], bottom_tier.shape[0])
        top_resized = cv2.resize(top_tier, (int(top_tier.shape[1] * (target_h / float(top_tier.shape[0]))), target_h))
        bot_resized = cv2.resize(bottom_tier, (int(bottom_tier.shape[1] * (target_h / float(bottom_tier.shape[0]))), target_h))

        # Horizontal stitch with small white margin
        sep_w = max(8, int(w * 0.04))
        separator = np.full((target_h, sep_w, 3) if plate_crop.ndim == 3 else (target_h, sep_w), 255, dtype=np.uint8)
        stitched = np.hstack([top_resized, separator, bot_resized])

        return stitched, True
