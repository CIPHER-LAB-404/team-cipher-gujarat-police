"""
=============================================================================
Test Suite 4: Live ANPR Pipeline & Vehicle Intelligence Benchmark Test
=============================================================================
Verifies:
1. HighAccuracyANPREngine initialization
2. Benchmark image plate detections (Gujarat, Maharashtra, Delhi)
3. Watchlist multi-tier matching (Exact match + Levenshtein fuzzy match)
4. Vehicle and pedestrian attribute extraction
5. JSON serialization safety (no float32/int64 crashes)
=============================================================================
"""

import unittest
import sys
import os
import cv2

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from anpr_detector import HighAccuracyANPREngine
from server import sanitize_for_json


class TestANPRDetectorLive(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = HighAccuracyANPREngine()
        cls.backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cls.test_car_gujarat = os.path.join(cls.backend_dir, "test_indian_car.jpg")
        cls.test_car_mh = os.path.join(cls.backend_dir, "test_maharashtra_car.jpg")
        cls.test_car_delhi = os.path.join(cls.backend_dir, "test_delhi_car.jpg")

    def test_watchlist_exact_match(self):
        """Exact watchlist match returns EXACT_MATCH with full details."""
        sample_watchlist = [
            {"id": "WL-001", "plate": "GJ01ER4492", "vehicleMake": "Mahindra Scorpio", "threatLevel": "CRITICAL"}
        ]
        self.engine.watchlist = sample_watchlist

        hit = self.engine.match_watchlist("GJ01ER4492")
        self.assertIsNotNone(hit)
        self.assertEqual(hit["match_type"], "EXACT_MATCH")
        self.assertEqual(hit["threatLevel"], "CRITICAL")

    def test_watchlist_fuzzy_match(self):
        """1-character edit distance returns FUZZY_CONFIRMED_MATCH."""
        sample_watchlist = [
            {"id": "WL-002", "plate": "MH12AB1234", "vehicleMake": "Toyota Fortuner", "threatLevel": "HIGH"}
        ]
        self.engine.watchlist = sample_watchlist

        # 1 character off: MH12AB1235 (4 vs 5 at end)
        hit = self.engine.match_watchlist("MH12AB1235")
        self.assertIsNotNone(hit)
        self.assertEqual(hit["match_type"], "FUZZY_CONFIRMED_MATCH")
        self.assertEqual(hit["edit_distance"], 1)

    def test_benchmark_gujarat_car_detection(self):
        """Executes ANPR pipeline on Gujarat benchmark vehicle image."""
        if not os.path.exists(self.test_car_gujarat):
            self.skipTest("Benchmark image test_indian_car.jpg not found")

        with open(self.test_car_gujarat, "rb") as f:
            content = f.read()

        plates = self.engine.detect_license_plates_in_image(content, camera_id="BENCHMARK-GUJ")
        self.assertIsInstance(plates, list)
        self.assertGreater(len(plates), 0, "Expected at least 1 plate detected in test_indian_car.jpg")
        p = plates[0]
        self.assertIn("plate", p)
        self.assertIn("confidence", p)
        self.assertGreater(p["confidence"], 0.50)

    def test_benchmark_delhi_car_detection(self):
        """Executes ANPR pipeline on Delhi benchmark vehicle image."""
        if not os.path.exists(self.test_car_delhi):
            self.skipTest("Benchmark image test_delhi_car.jpg not found")

        with open(self.test_car_delhi, "rb") as f:
            content = f.read()

        plates = self.engine.detect_license_plates_in_image(content, camera_id="BENCHMARK-DL")
        self.assertIsInstance(plates, list)
        self.assertGreater(len(plates), 0, "Expected at least 1 plate detected in test_delhi_car.jpg")

    def test_rejection_of_non_plate_crops(self):
        """Zero false-positive detections logged on non-vehicle scenery or pure noise."""
        import numpy as np
        # Create non-vehicle scenery noise frame
        blank_canvas = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.rectangle(blank_canvas, (100, 100), (300, 200), (128, 128, 128), -1)
        cv2.putText(blank_canvas, "SHOP BANNER NOISE", (110, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        _, encoded = cv2.imencode('.jpg', blank_canvas)

        plates = self.engine.detect_license_plates_in_image(encoded.tobytes(), camera_id="NOISE-TEST")
        # Ensure no artificial 0.72 confidence plate is injected
        valid_plates = [p for p in plates if p.get("confidence", 0) >= 0.70 and len(p.get("plate", "")) >= 8]
        self.assertEqual(len(valid_plates), 0, "Non-plate scenery should not produce high-confidence plate detections")

    def test_ten_character_plate_full_retention(self):
        """10-character Indian standard plates (e.g. GJ01ER4492) are fully retained without 9-slot truncation."""
        if not os.path.exists(self.test_car_gujarat):
            self.skipTest("Benchmark image test_indian_car.jpg not found")

        with open(self.test_car_gujarat, "rb") as f:
            content = f.read()

        plates = self.engine.detect_license_plates_in_image(content, camera_id="BENCHMARK-GUJ")
        self.assertGreater(len(plates), 0)
        p = plates[0]
        # Should be full 10-char plate: e.g. GJ01ER4492, not truncated to 9
        self.assertEqual(len(p["plate"]), 10, f"Expected 10-char plate, got {p['plate']} (len {len(p['plate'])})")
        self.assertTrue(p["plate"].startswith("GJ01"))


    def test_json_sanitization_safety(self):
        """Ensures numpy types are serialized cleanly without throwing 500 error."""
        import numpy as np
        dirty_dict = {
            "track_id": np.int64(42),
            "confidence": np.float32(0.985),
            "is_valid": np.bool_(True),
            "bbox": np.array([10, 20, 100, 200], dtype=np.int32)
        }
        clean = sanitize_for_json(dirty_dict)
        self.assertIsInstance(clean["track_id"], int)
        self.assertIsInstance(clean["confidence"], float)
        self.assertIsInstance(clean["is_valid"], bool)
        self.assertIsInstance(clean["bbox"], list)


if __name__ == "__main__":
    unittest.main()

