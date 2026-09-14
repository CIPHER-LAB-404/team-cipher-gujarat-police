"""
=============================================================================
Gujarat Police Sentinel - Visual License Plate Category Classifier
=============================================================================
Analyzes the physical visual characteristics of a license plate crop independently
from the OCR character reading:
- Background hue and saturation in HSV color space (White, Yellow, Green, Red, Blue)
- Character text foreground-background contrast
- Geometric aspect ratio (single-line horizontal vs two-tier square)
- Multi-evidence fusion combining visual appearance with OCR syntax and vehicle class
=============================================================================
"""

from dataclasses import dataclass
from typing import Tuple, Optional, Dict, Any
import numpy as np
import cv2


@dataclass
class VisualClassificationResult:
    """Encapsulates the physical visual classification of a cropped plate."""
    dominant_color: str          # "WHITE", "YELLOW", "GREEN", "RED", "BLUE", "UNKNOWN"
    color_confidence: float      # 0.0 to 1.0
    suggested_category: str      # "PRIVATE_NON_TRANSPORT", "POSSIBLE_TRANSPORT",
                                 # "POSSIBLE_ELECTRIC", "POSSIBLE_TEMPORARY_OR_TRADE",
                                 # "POSSIBLE_DIPLOMATIC", "UNKNOWN"
    is_multiline_aspect: bool    # True if aspect ratio < 2.3
    aspect_ratio: float          # width / height
    mean_brightness: float       # 0 to 255
    contrast_std: float          # standard deviation of grayscale pixels


class PlateVisualClassifier:
    """
    Physical appearance analyzer for Indian vehicle number plates.
    Extracts color cues to assist category classification WITHOUT overriding
    the actual OCR character sequence.
    """

    @classmethod
    def classify_plate_appearance(
        cls,
        plate_crop: np.ndarray,
        vehicle_type: Optional[str] = None
    ) -> VisualClassificationResult:
        """
        Classifies plate physical appearance using HSV chromatic analysis.
        Filters out dark character strokes to measure true plate background color.
        """
        if plate_crop is None or plate_crop.size == 0 or plate_crop.shape[0] < 6 or plate_crop.shape[1] < 12:
            return VisualClassificationResult(
                dominant_color="UNKNOWN",
                color_confidence=0.0,
                suggested_category="UNKNOWN",
                is_multiline_aspect=False,
                aspect_ratio=1.0,
                mean_brightness=0.0,
                contrast_std=0.0
            )

        h, w = plate_crop.shape[:2]
        aspect_ratio = round(float(w) / max(1, float(h)), 2)
        is_multiline = aspect_ratio < 2.3

        # Grayscale stats for brightness and contrast
        gray = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY) if plate_crop.ndim == 3 else plate_crop
        mean_brightness = round(float(np.mean(gray)), 1)
        contrast_std = round(float(np.std(gray)), 1)

        # Convert to HSV color space
        hsv = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2HSV) if plate_crop.ndim == 3 else cv2.cvtColor(cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR), cv2.COLOR_BGR2HSV)

        # Mask out very dark pixels (character text / border rivets)
        # Background pixels typically have Value > 60
        v_channel = hsv[:, :, 2]
        bg_mask = v_channel > 60

        if np.count_nonzero(bg_mask) < 20:
            # Entire crop is very dark or unreadable
            return VisualClassificationResult(
                dominant_color="UNKNOWN",
                color_confidence=0.2,
                suggested_category="UNKNOWN",
                is_multiline_aspect=is_multiline,
                aspect_ratio=aspect_ratio,
                mean_brightness=mean_brightness,
                contrast_std=contrast_std
            )

        h_vals = hsv[:, :, 0][bg_mask]
        s_vals = hsv[:, :, 1][bg_mask]
        v_vals = hsv[:, :, 2][bg_mask]

        total_bg_pixels = float(len(h_vals))

        # 1. White Background: Low saturation (< 45) and High Value (> 120)
        white_count = np.count_nonzero((s_vals < 45) & (v_vals > 110))

        # 2. Yellow Background (Commercial / Transport): Hue 18 to 36, Saturation >= 50, Value >= 100
        yellow_count = np.count_nonzero((h_vals >= 18) & (h_vals <= 36) & (s_vals >= 50) & (v_vals >= 90))

        # 3. Green Background (Electric Vehicle): Hue 38 to 88, Saturation >= 45, Value >= 60
        green_count = np.count_nonzero((h_vals >= 38) & (h_vals <= 88) & (s_vals >= 45) & (v_vals >= 60))

        # 4. Red Background (Temporary / Trade): Hue in [0, 12] or [168, 180], Saturation >= 65
        red_count = np.count_nonzero(((h_vals <= 12) | (h_vals >= 168)) & (s_vals >= 65) & (v_vals >= 70))

        # 5. Blue Background (Diplomatic / Consular / UN): Hue 95 to 135, Saturation >= 60
        blue_count = np.count_nonzero((h_vals >= 95) & (h_vals <= 135) & (s_vals >= 60) & (v_vals >= 65))

        color_fractions = {
            "WHITE": white_count / total_bg_pixels,
            "YELLOW": yellow_count / total_bg_pixels,
            "GREEN": green_count / total_bg_pixels,
            "RED": red_count / total_bg_pixels,
            "BLUE": blue_count / total_bg_pixels
        }

        dominant_color = max(color_fractions, key=color_fractions.get)
        max_fraction = color_fractions[dominant_color]

        # Require at least 25% background pixel consensus for color assignment
        if max_fraction < 0.25:
            dominant_color = "WHITE" if white_count > yellow_count else "YELLOW"
            color_conf = 0.50
        else:
            color_conf = round(min(0.95, float(max_fraction) * 1.1), 2)

        # Suggest category based on physical appearance and optional vehicle type context
        vtype_lower = (vehicle_type or "").lower()
        if dominant_color == "YELLOW":
            suggested = "POSSIBLE_TRANSPORT"
        elif dominant_color == "GREEN":
            suggested = "POSSIBLE_ELECTRIC"
        elif dominant_color == "RED":
            suggested = "POSSIBLE_TEMPORARY_OR_TRADE"
        elif dominant_color == "BLUE":
            suggested = "POSSIBLE_DIPLOMATIC"
        else:
            # White background
            # If vehicle is a Bus or Commercial Truck, yellow plates are often dirty or washed out in harsh sun
            if "bus" in vtype_lower or "truck" in vtype_lower:
                suggested = "POSSIBLE_TRANSPORT"
            else:
                suggested = "PRIVATE_NON_TRANSPORT"

        return VisualClassificationResult(
            dominant_color=dominant_color,
            color_confidence=color_conf,
            suggested_category=suggested,
            is_multiline_aspect=is_multiline,
            aspect_ratio=aspect_ratio,
            mean_brightness=mean_brightness,
            contrast_std=contrast_std
        )

    @classmethod
    def fuse_category(
        cls,
        syntax_category: str,
        visual_res: VisualClassificationResult,
        vehicle_type: Optional[str] = None
    ) -> Tuple[str, float]:
        """
        Fuses OCR registration syntax with visual plate appearance and vehicle type.
        Priority Hierarchy:
        1. Special Syntax (DEFENSE, DIPLOMATIC, CONSULAR, BHARAT_SERIES) takes precedence
        2. Visual EV (Green) -> ELECTRIC_NON_TRANSPORT or ELECTRIC_TRANSPORT
        3. Visual Commercial (Yellow) or Heavy Vehicle -> TRANSPORT_COMMERCIAL
        4. Visual Red -> TEMPORARY or DEALER_TRADE based on syntax evidence
        5. Standard State syntax -> PRIVATE_NON_TRANSPORT
        """
        v_cat = visual_res.suggested_category
        vtype = (vehicle_type or "").lower()

        # Rule 1: Special mission marks override civilian color classifications
        if syntax_category in ["DEFENSE", "DIPLOMATIC", "CONSULAR", "SPECIAL_MISSION", "BHARAT_SERIES", "LEGACY"]:
            return syntax_category, 0.95

        # Rule 2: Green plate visual evidence -> EV category
        if v_cat == "POSSIBLE_ELECTRIC" or visual_res.dominant_color == "GREEN":
            if "bus" in vtype or "truck" in vtype or "taxi" in vtype or v_cat == "POSSIBLE_TRANSPORT":
                return "ELECTRIC_TRANSPORT", 0.90
            return "ELECTRIC_NON_TRANSPORT", 0.92

        # Rule 3: Red plate visual evidence -> Temporary or Dealer Trade
        if v_cat == "POSSIBLE_TEMPORARY_OR_TRADE" or visual_res.dominant_color == "RED":
            # If OCR has 'TC' (Trade Certificate), dealer trade
            if "TC" in syntax_category:
                return "DEALER_TRADE", 0.88
            return "TEMPORARY", 0.85

        # Rule 4: Yellow plate visual evidence or commercial vehicle class
        if v_cat == "POSSIBLE_TRANSPORT" or visual_res.dominant_color == "YELLOW" or "bus" in vtype or "truck" in vtype:
            return "TRANSPORT_COMMERCIAL", 0.90

        # Rule 5: Default to civilian private registration
        if syntax_category == "STANDARD_PRIVATE":
            return "PRIVATE_NON_TRANSPORT", 0.94

        return syntax_category, 0.80
