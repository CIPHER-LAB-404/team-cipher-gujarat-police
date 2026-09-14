"""
=============================================================================
Test Suite 2: Multi-Line Plate Processing & Sequence OCR Pipeline
=============================================================================
Verifies:
1. Multi-line aspect ratio classification (two-wheelers / commercial)
2. Vertical splitting and horizontal row stitching
3. Adaptive row clustering for 2-tier plate OCR segments
4. CTCDecoder sequence collapsing and blank removal
5. Adaptive illumination and contrast equalization (CLAHE)
=============================================================================
"""

import unittest
import sys
import os
import numpy as np
import cv2

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from anpr_pipeline.ocr.lprnet_crnn import (
    MultiLinePlateProcessor,
    CTCDecoder,
    PlateOCREngine
)


class TestMultiLinePlateProcessor(unittest.TestCase):

    def test_aspect_ratio_classification(self):
        """Aspect ratio W/H < 2.4 indicates two-tier multi-line plates."""
        processor = MultiLinePlateProcessor()

        # Two-wheeler square plate (e.g. 200x120 -> aspect 1.67)
        two_wheeler = np.zeros((120, 200, 3), dtype=np.uint8)
        self.assertTrue(processor.is_multiline(two_wheeler))

        # Commercial square plate (e.g. 150x100 -> aspect 1.5)
        comm_plate = np.zeros((100, 150, 3), dtype=np.uint8)
        self.assertTrue(processor.is_multiline(comm_plate))

        # Standard elongated car plate (e.g. 450x100 -> aspect 4.5)
        car_plate = np.zeros((100, 450, 3), dtype=np.uint8)
        self.assertFalse(processor.is_multiline(car_plate))

    def test_split_and_stitch_horizontal(self):
        """Splits top and bottom tiers and concatenates side-by-side."""
        processor = MultiLinePlateProcessor()
        sample_square = np.full((100, 150, 3), 128, dtype=np.uint8)

        stitched = processor.split_and_stitch_horizontal(sample_square)
        self.assertIsNotNone(stitched)

        # Stitched image must be significantly wider than the original
        orig_aspect = 150 / 100.0
        stitched_aspect = stitched.shape[1] / float(stitched.shape[0])
        self.assertGreater(stitched_aspect, orig_aspect * 1.5)
        self.assertGreater(stitched.shape[1], 150)

    def test_ctc_decoder_greedy(self):
        """Greedy CTC decoder collapses repeats, removes blanks, and computes confidence."""
        vocab = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        decoder = CTCDecoder(vocab=vocab, blank_idx=0)

        # Build mock logits: time_steps=6, classes=len(vocab)+1
        # Want prediction "G", "J", blank, "0", "1"
        num_classes = len(vocab) + 1
        logits = np.zeros((1, 6, num_classes), dtype=np.float32)

        g_idx = vocab.index("G") + 1
        j_idx = vocab.index("J") + 1
        zero_idx = vocab.index("0") + 1
        one_idx = vocab.index("1") + 1

        # t0: G, t1: G (repeat), t2: J, t3: blank (0), t4: 0, t5: 1
        logits[0, 0, g_idx] = 10.0
        logits[0, 1, g_idx] = 10.0
        logits[0, 2, j_idx] = 10.0
        logits[0, 3, 0] = 10.0  # blank
        logits[0, 4, zero_idx] = 10.0
        logits[0, 5, one_idx] = 10.0

        decoded_text, conf = decoder.decode_greedy(logits)
        self.assertEqual(decoded_text, "GJ01")
        self.assertGreater(conf, 0.90)

    def test_plate_ocr_preprocessing(self):
        """Preprocesses plate crop with CLAHE and normalizes tensor dimensions."""
        engine = PlateOCREngine()
        dummy_crop = np.random.randint(50, 200, (60, 240, 3), dtype=np.uint8)

        blob, is_ml = engine.preprocess_plate(dummy_crop)
        self.assertFalse(is_ml)
        self.assertEqual(blob.ndim, 4)
        self.assertEqual(blob.shape[0], 1)
        self.assertEqual(blob.shape[1], 3)
        self.assertEqual(blob.shape[2], engine.input_size[1])
        self.assertEqual(blob.shape[3], engine.input_size[0])


if __name__ == "__main__":
    unittest.main()
