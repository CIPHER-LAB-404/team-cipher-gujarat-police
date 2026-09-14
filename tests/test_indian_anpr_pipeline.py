"""
=============================================================================
Gujarat Police Sentinel - Indian ANPR Multi-Tier Verification Suite
=============================================================================
Tier A: Indian Registration Rule Engine & State Registry Unit Tests
Tier B: Visual Category Classifier & HSV Chromatic Tests
Tier C: Preprocessing, Deskewing & Multi-Line Slicing Tests
Tier D: Temporal Tracklet Aggregator & End-to-End Pipeline Stream Tests
=============================================================================
"""

import os
import sys
import unittest
import numpy as np
import cv2

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.anpr_pipeline.postprocess.state_registry import IndianStateRegistry
from backend.anpr_pipeline.postprocess.syntax_validator import (
    IndianPlateSyntaxValidator,
    PlateValidationResult,
    FancyPatternEvaluator
)
from backend.anpr_pipeline.category_classifier import PlateVisualClassifier, VisualClassificationResult
from backend.anpr_pipeline.preprocessing import PlatePreprocessor
from backend.anpr_pipeline.aggregation import MultiFrameAggregator, PlateTracklet, Observation
from backend.anpr_pipeline.pipeline import ANPRTwoStagePipeline, ANPRFrameOutput


class TestTierA_RegistrationRuleEngine(unittest.TestCase):
    """Tier A: Tests the RTO MoRTH rule engine, legacy states, BH series, fancy patterns, and noise rejection."""

    def setUp(self):
        self.validator = IndianPlateSyntaxValidator()

    def test_01_active_state_registration(self):
        """Active state registrations must be VALID with correct state metadata."""
        res = self.validator.correct_and_validate("GJ01AB1234", initial_confidence=0.95)
        self.assertEqual(res.validation_status, "VALID")
        self.assertEqual(res.validated_plate, "GJ01AB1234")
        self.assertEqual(res.state_code, "GJ")
        self.assertEqual(res.state_name, "Gujarat")
        self.assertFalse(res.is_legacy_state)
        self.assertEqual(res.plate_category, "STANDARD_PRIVATE")

    def test_02_delhi_one_digit_rto(self):
        """Delhi single-digit RTO (DL 1C AB 1234) must be recognized as VALID."""
        res = self.validator.correct_and_validate("DL1CAB1234", initial_confidence=0.90)
        self.assertEqual(res.validation_status, "VALID")
        self.assertEqual(res.state_code, "DL")
        self.assertEqual(res.state_name, "Delhi")

    def test_03_legacy_state_codes_tolerated_as_plausible(self):
        """Historical codes (UA, OR) from recorded footage must be PLAUSIBLE, not active."""
        res_ua = self.validator.correct_and_validate("UA07A1234", initial_confidence=0.88)
        self.assertEqual(res_ua.validation_status, "PLAUSIBLE")
        self.assertTrue(res_ua.is_legacy_state)
        self.assertEqual(res_ua.state_code, "UA")
        self.assertIn("Uttarakhand", res_ua.state_name)

        res_or = self.validator.correct_and_validate("OR02B5678", initial_confidence=0.85)
        self.assertEqual(res_or.validation_status, "PLAUSIBLE")
        self.assertTrue(res_or.is_legacy_state)
        self.assertEqual(res_or.state_code, "OR")

    def test_04_bharat_series_variations(self):
        """BH series plates in various formats (spaces, dashes, compact) must normalize and be VALID."""
        samples = ["22BH5678AB", "21 BH 1234 AA", "23-BH-0001-ZZ", "24bh9999xy"]
        for sample in samples:
            res = self.validator.correct_and_validate(sample, initial_confidence=0.92)
            self.assertEqual(res.validation_status, "VALID", f"Failed on BH sample: {sample}")
            self.assertEqual(res.plate_category, "BHARAT_SERIES", f"Failed category for: {sample}")

    def test_05_position_aware_character_disambiguation(self):
        """Ambiguity disambiguation must be position-aware (e.g. letter 'I' in RTO slot -> '1')."""
        # In GJ0IAB1234, the 4th char is in the 2-digit RTO slot, so 'I' -> '1'
        res = self.validator.correct_and_validate("GJ0IAB1234", initial_confidence=0.85)
        self.assertEqual(res.validated_plate, "GJ01AB1234")
        self.assertEqual(res.raw_plate, "GJ0IAB1234")  # Raw OCR preserved!
        self.assertIn("RTO slot", " ".join(res.corrections_made))

    def test_06_non_temporary_series_not_misclassified(self):
        """Ordinary series like GJ01TR1234 must NOT be classified as TEMPORARY merely due to 'TR'."""
        res = self.validator.correct_and_validate("GJ01TR1234", initial_confidence=0.90)
        self.assertEqual(res.validation_status, "VALID")
        self.assertNotEqual(res.plate_category, "TEMPORARY")
        self.assertEqual(res.plate_category, "STANDARD_PRIVATE")

    def test_07_choice_fancy_number_classification(self):
        """Distinctive numbers (0001, 7777, 1234) must be tagged CHOICE_FANCY_PATTERN with a cautious label."""
        res_0001 = self.validator.correct_and_validate("GJ01AA0001", initial_confidence=0.95)
        self.assertEqual(res_0001.number_type, "CHOICE_FANCY_PATTERN")
        self.assertTrue(res_0001.fancy_pattern_description.startswith("Pattern appears special/fancy"))
        self.assertEqual(res_0001.validated_plate, "GJ01AA0001")  # Plate text untouched!

        res_7777 = self.validator.correct_and_validate("MH02CD7777", initial_confidence=0.92)
        self.assertEqual(res_7777.number_type, "CHOICE_FANCY_PATTERN")
        self.assertIn("quad repetition", res_7777.fancy_pattern_description.lower())

    def test_08_diplomatic_and_consular_marks(self):
        """Diplomatic (CD) and Consular (CC) marks must be parsed under diplomatic rules."""
        res_cd = self.validator.correct_and_validate("77CD1234", initial_confidence=0.90)
        self.assertEqual(res_cd.validation_status, "VALID")
        self.assertEqual(res_cd.plate_category, "DIPLOMATIC")

        res_cc = self.validator.correct_and_validate("55CC9876", initial_confidence=0.88)
        self.assertEqual(res_cc.validation_status, "VALID")
        self.assertEqual(res_cc.plate_category, "CONSULAR")

    def test_09_noise_rejection(self):
        """Arbitrary roadside text or bumper stickers must be classified as INVALID."""
        noise_samples = ["SALE 50%", "STOP", "NO PARKING", "SPEED 40", "HONK OK PLEASE"]
        for sample in noise_samples:
            res = self.validator.correct_and_validate(sample, initial_confidence=0.50)
            self.assertEqual(res.validation_status, "INVALID", f"Expected INVALID for: {sample}")

    def test_10_four_tier_validation_states(self):
        """Validator must support all 4 distinct validation tiers: VALID, PLAUSIBLE, UNCERTAIN, INVALID."""
        res_valid = self.validator.correct_and_validate("GJ01ER4492")
        self.assertEqual(res_valid.validation_status, "VALID")

        res_plausible = self.validator.correct_and_validate("UA01AB1234")
        self.assertEqual(res_plausible.validation_status, "PLAUSIBLE")

        res_uncertain = self.validator.correct_and_validate("GJ01A", initial_confidence=0.4)
        self.assertEqual(res_uncertain.validation_status, "UNCERTAIN")

        res_invalid = self.validator.correct_and_validate("SUPER FAST CAR")
        self.assertEqual(res_invalid.validation_status, "INVALID")


class TestTierB_VisualCategoryClassifier(unittest.TestCase):
    """Tier B: Tests physical plate appearance classification (Color & Aspect Ratio) in HSV space."""

    def test_01_white_plate_classification(self):
        """Synthetic white plate image (BGR ~ 240, 240, 240) must classify as WHITE / PRIVATE."""
        white_img = np.full((50, 150, 3), 235, dtype=np.uint8)
        res = PlateVisualClassifier.classify_plate_appearance(white_img, vehicle_type="Car")
        self.assertEqual(res.dominant_color, "WHITE")
        self.assertEqual(res.suggested_category, "PRIVATE_NON_TRANSPORT")

    def test_02_yellow_plate_classification(self):
        """Synthetic yellow plate (BGR [20, 210, 230]) must classify as YELLOW / POSSIBLE_TRANSPORT."""
        yellow_img = np.zeros((50, 150, 3), dtype=np.uint8)
        yellow_img[:, :] = (25, 215, 240)
        res = PlateVisualClassifier.classify_plate_appearance(yellow_img, vehicle_type="Truck")
        self.assertEqual(res.dominant_color, "YELLOW")
        self.assertEqual(res.suggested_category, "POSSIBLE_TRANSPORT")

    def test_03_green_ev_plate_classification(self):
        """Synthetic green plate must classify as GREEN / POSSIBLE_ELECTRIC."""
        green_img = np.zeros((50, 150, 3), dtype=np.uint8)
        green_img[:, :] = (40, 180, 50)  # BGR green
        res = PlateVisualClassifier.classify_plate_appearance(green_img, vehicle_type="Car")
        self.assertEqual(res.dominant_color, "GREEN")
        self.assertEqual(res.suggested_category, "POSSIBLE_ELECTRIC")

        # Fusion check: EV is NOT inserted into registration number!
        fused_cat, _ = PlateVisualClassifier.fuse_category("STANDARD_PRIVATE", res, vehicle_type="Car")
        self.assertEqual(fused_cat, "ELECTRIC_NON_TRANSPORT")

    def test_04_red_trade_temporary_classification(self):
        """Synthetic red plate must classify as RED / POSSIBLE_TEMPORARY_OR_TRADE."""
        red_img = np.zeros((50, 150, 3), dtype=np.uint8)
        red_img[:, :] = (30, 30, 220)  # BGR red
        res = PlateVisualClassifier.classify_plate_appearance(red_img)
        self.assertEqual(res.dominant_color, "RED")
        self.assertEqual(res.suggested_category, "POSSIBLE_TEMPORARY_OR_TRADE")


class TestTierC_PreprocessingAndDeskewing(unittest.TestCase):
    """Tier C: Tests blur assessment, aspect ratio heuristics, and multi-line row decomposition."""

    def test_01_quality_metrics(self):
        """Sharp high-contrast image must yield higher Laplacian variance than blurred image."""
        sharp = np.zeros((60, 200, 3), dtype=np.uint8)
        cv2.putText(sharp, "GJ01AB1234", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        q_sharp = PlatePreprocessor.assess_quality(sharp)
        self.assertFalse(q_sharp.is_blurry)

        blurred = cv2.GaussianBlur(sharp, (15, 15), 5)
        q_blurred = PlatePreprocessor.assess_quality(blurred)
        self.assertTrue(q_blurred.is_blurry)
        self.assertLess(q_blurred.laplacian_variance, q_sharp.laplacian_variance)

    def test_02_multiline_plate_slicing(self):
        """Two-tier motorcycle plate (aspect < 2.3) must be horizontally stitched."""
        multiline_crop = np.full((100, 120, 3), 255, dtype=np.uint8)  # Aspect ratio 1.2
        cv2.putText(multiline_crop, "GJ01", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
        cv2.putText(multiline_crop, "ER4492", (10, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)

        stitched, was_split = PlatePreprocessor.process_multiline_plate(multiline_crop, aspect_ratio=1.2, vehicle_type="Motorcycle")
        self.assertTrue(was_split)
        self.assertGreater(stitched.shape[1], multiline_crop.shape[1])  # Stitched width is wider!


class TestTierD_TemporalAggregationAndPipeline(unittest.TestCase):
    """Tier D: Tests multi-frame consensus slot voting and pipeline execution graph."""

    def test_01_tracklet_state_transitions(self):
        """Tracklet must transition DETECTED -> CANDIDATE -> STABILIZING -> CONFIRMED."""
        aggregator = MultiFrameAggregator()
        dummy_crop = np.full((30, 100, 3), 200, dtype=np.uint8)

        # Frame 1: Single observation
        tlet = aggregator.update_tracklet(
            track_id=101,
            vehicle_type="Car",
            frame_idx=1,
            plate_text="GJ01AB1234",
            raw_ocr="GJ01AB1234",
            ocr_conf=0.88,
            det_conf=0.92,
            sharpness=120.0,
            plate_crop=dummy_crop,
            full_frame=None,
            vehicle_bbox=(50, 50, 300, 250),
            plate_bbox=(120, 180, 220, 210),
            validation_result=None,
            visual_result=None
        )
        self.assertEqual(tlet.state, "CANDIDATE")

        # Frame 2: Second observation
        tlet = aggregator.update_tracklet(
            track_id=101,
            vehicle_type="Car",
            frame_idx=2,
            plate_text="GJ01AB1234",
            raw_ocr="GJ01AB1234",
            ocr_conf=0.91,
            det_conf=0.93,
            sharpness=130.0,
            plate_crop=dummy_crop,
            full_frame=None,
            vehicle_bbox=(52, 50, 302, 250),
            plate_bbox=(122, 180, 222, 210),
            validation_result=None,
            visual_result=None
        )
        self.assertEqual(tlet.state, "STABILIZING")

        # Frame 3: Third consistent observation -> CONFIRMED
        tlet = aggregator.update_tracklet(
            track_id=101,
            vehicle_type="Car",
            frame_idx=3,
            plate_text="GJ01AB1234",
            raw_ocr="GJ01AB1234",
            ocr_conf=0.94,
            det_conf=0.95,
            sharpness=140.0,
            plate_crop=dummy_crop,
            full_frame=None,
            vehicle_bbox=(54, 50, 304, 250),
            plate_bbox=(124, 180, 224, 210),
            validation_result=None,
            visual_result=None
        )
        self.assertEqual(tlet.state, "CONFIRMED")
        self.assertEqual(tlet.consensus_plate, "GJ01AB1234")

    def test_02_pipeline_frame_execution(self):
        """ANPRTwoStagePipeline must process a frame and generate structured ANPRFrameOutput with HUD overlay."""
        pipeline = ANPRTwoStagePipeline()
        dummy_frame = np.full((480, 640, 3), 80, dtype=np.uint8)

        output = pipeline.process_frame(dummy_frame, camera_id="CAM-TEST", annotate=True)
        self.assertIsInstance(output, ANPRFrameOutput)
        self.assertEqual(output.camera_id, "CAM-TEST")
        self.assertIsNotNone(output.annotated_frame)
        self.assertGreaterEqual(output.telemetry.total_pipeline_ms, 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
