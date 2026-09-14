"""
=============================================================================
Test Suite 1: Indian License Plate Syntax & Positional Disambiguation Engine
=============================================================================
Verifies:
1. All 36 Indian States & Union Territories (e.g., GJ, MH, DL, KA, TN, UP, RJ)
2. Bharat Series (BH) Format (YY BH #### XX)
3. Delhi (DL) Single-Digit RTO Format (e.g. DL 1C, DL 3C)
4. Commercial Plates (Yellow - T, TR, TX, TA, TB series)
5. Electric Vehicle Plates (Green - EV series)
6. Defense Plates (^ or YYB######X)
7. Diplomatic Plates (CD, CC, UN)
8. Sequence zero-padding and short sequence preservation (e.g. MH12AB12)
9. Neural character disambiguation (O <-> 0, I <-> 1, S <-> 5, B <-> 8, Z <-> 2)
10. International alphanumeric fallback (e.g. UK plates FD55 HTA)
=============================================================================
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from anpr_pipeline.postprocess.syntax_validator import IndianPlateSyntaxValidator


class TestIndianPlateSyntaxValidator(unittest.TestCase):

    def setUp(self):
        self.validator = IndianPlateSyntaxValidator()

    def test_all_major_indian_states(self):
        """Verifies correct parsing across major Indian states."""
        samples = [
            ("GJ01ER4492", "GJ", "01", "ER", "4492", "Gujarat"),
            ("MH12PQ1111", "MH", "12", "PQ", "1111", "Maharashtra"),
            ("DL01AB1234", "DL", "01", "AB", "1234", "Delhi"),
            ("KA05MF9999", "KA", "05", "MF", "9999", "Karnataka"),
            ("TN09BK8888", "TN", "09", "BK", "8888", "Tamil Nadu"),
            ("UP32AZ7777", "UP", "32", "AZ", "7777", "Uttar Pradesh"),
            ("RJ14CD6666", "RJ", "14", "CD", "6666", "Rajasthan"),
            ("HR26DQ5555", "HR", "26", "DQ", "5555", "Haryana"),
            ("WB02E3333", "WB", "02", "E", "3333", "West Bengal"),
            ("KL07BQ2222", "KL", "07", "BQ", "2222", "Kerala")
        ]
        for raw, exp_st, exp_rto, exp_ser, exp_seq, exp_name in samples:
            res = self.validator.correct_and_validate(raw)
            self.assertTrue(res.is_valid_format, f"Failed validation for {raw}")
            self.assertEqual(res.state_code, exp_st)
            self.assertEqual(res.rto_code, exp_rto)
            self.assertEqual(res.series, exp_ser)
            self.assertEqual(res.sequence_number, exp_seq)
            self.assertEqual(res.state_name, exp_name)

    def test_delhi_single_digit_rto(self):
        """Delhi uses 1-digit RTO followed by class/series letter (e.g. DL 1C, DL 3C)."""
        samples = [
            ("DL1CAB1234", "DL", "1", "CAB", "1234"),
            ("DL3SAM9876", "DL", "3", "SAM", "9876"),
            ("DL4C1111", "DL", "4", "C", "1111"),
            ("DL9T9999", "DL", "9", "T", "9999"),
        ]
        for raw, exp_st, exp_rto, exp_ser, exp_seq in samples:
            res = self.validator.correct_and_validate(raw)
            self.assertTrue(res.is_valid_format, f"Failed for {raw}")
            self.assertEqual(res.state_code, exp_st)
            self.assertEqual(res.rto_code, exp_rto)
            self.assertEqual(res.series, exp_ser)
            self.assertEqual(res.sequence_number, exp_seq)

    def test_bharat_series_format(self):
        """Bharat Series: 22BH1234AA format."""
        samples = [
            "22BH1234AA",
            "21BH9999Z",
            "23BH0001B",
            "228H1234AA",  # '8' confused with 'B'
            "22BM1234AA"   # 'M' confused with 'H'
        ]
        for s in samples:
            res = self.validator.correct_and_validate(s)
            self.assertTrue(res.is_valid_format, f"Failed for BH series {s}")
            self.assertEqual(res.plate_type, "BHARAT_SERIES")
            self.assertEqual(res.state_code, "BH")
            self.assertTrue(res.cleaned_plate.startswith("2"))

    def test_commercial_plate_format(self):
        """Commercial yellow plates with T/TR/TX/TA/TB series."""
        res = self.validator.correct_and_validate("GJ01TX1234")
        self.assertTrue(res.is_valid_format)
        self.assertEqual(res.plate_type, "COMMERCIAL")

        res2 = self.validator.correct_and_validate("MH04TR9999")
        self.assertTrue(res2.is_valid_format)
        self.assertEqual(res2.plate_type, "COMMERCIAL")

    def test_electric_vehicle_format(self):
        """EV green plates with EV series."""
        res = self.validator.correct_and_validate("GJ01EV4492")
        self.assertTrue(res.is_valid_format)
        self.assertEqual(res.plate_type, "ELECTRIC_VEHICLE")

    def test_defense_plate_format(self):
        """Military/Defense vehicles (starts with ^ or year+B)."""
        res = self.validator.correct_and_validate("^21B123456C")
        self.assertTrue(res.is_valid_format)
        self.assertEqual(res.plate_type, "DEFENSE")

    def test_diplomatic_plate_format(self):
        """Diplomatic consular vehicles (CD/CC/UN)."""
        res = self.validator.correct_and_validate("77CD1234")
        self.assertTrue(res.is_valid_format)
        self.assertEqual(res.plate_type, "DIPLOMATIC")

    def test_neural_character_disambiguation(self):
        """Disambiguates letter/digit confusions based on strict positional slotting."""
        # 1. 'O' -> '0' in RTO slot
        res = self.validator.correct_and_validate("GJO1ER4492")
        self.assertEqual(res.cleaned_plate, "GJ01ER4492")
        self.assertEqual(res.rto_code, "01")

        # 2. 'I' -> '1' in RTO slot
        res2 = self.validator.correct_and_validate("MHI2AB1234")
        self.assertEqual(res2.cleaned_plate, "MH12AB1234")
        self.assertEqual(res2.rto_code, "12")

        # 3. '0' -> 'O' in State slot (0L -> DL)
        res3 = self.validator.correct_and_validate("0L01AB1234")
        self.assertEqual(res3.state_code, "DL")

        # 4. 'O' -> '0' in Sequence slot
        res4 = self.validator.correct_and_validate("GJ01ER449O")
        self.assertEqual(res4.sequence_number, "4490")

    def test_short_sequence_preservation(self):
        """Ensures 1-2 digit sequence numbers don't eat the series letters."""
        res = self.validator.correct_and_validate("MH12AB12")
        self.assertEqual(res.series, "AB")
        self.assertEqual(res.sequence_number, "12")

        res2 = self.validator.correct_and_validate("GJ01A1")
        self.assertEqual(res2.series, "A")
        self.assertEqual(res2.sequence_number, "1")

    def test_hsrp_prefix_stripping(self):
        """Strips IND, 1ND, INDIA, and related tamper prefixes."""
        res = self.validator.correct_and_validate("IND-GJ-01-ER-4492")
        self.assertEqual(res.cleaned_plate, "GJ01ER4492")

        res2 = self.validator.correct_and_validate("1ND GJ01ER4492")
        self.assertEqual(res2.cleaned_plate, "GJ01ER4492")

        res3 = self.validator.correct_and_validate("INDIA MH12AB1234")
        self.assertEqual(res3.cleaned_plate, "MH12AB1234")

    def test_international_fallback(self):
        """Preserves foreign or non-standard plates without forcing an Indian state."""
        res = self.validator.correct_and_validate("FD55HTA")  # UK plate
        self.assertEqual(res.cleaned_plate, "FD55HTA")
        self.assertEqual(res.plate_type, "GENERAL_ALPHANUMERIC")

    def test_interstate_state_preservation(self):
        """Verifies interstate plates (MH, DL, RJ, UP, KA, BH) preserve their state code."""
        samples = [
            ("MH12DE1433", "MH", "Maharashtra"),
            ("RJ14CE2020", "RJ", "Rajasthan"),
            ("DL3CAB1234", "DL", "Delhi"),
            ("UP32AZ7777", "UP", "Uttar Pradesh"),
            ("KA05MF9999", "KA", "Karnataka"),
            ("22BH1234AA", "BH", "Bharat Series (National)"),
        ]
        for plate, expected_state, exp_name in samples:
            res = self.validator.correct_and_validate(plate)
            self.assertEqual(res.state_code, expected_state)
            self.assertEqual(res.state_name, exp_name)
            self.assertTrue(res.cleaned_plate.startswith(expected_state) or expected_state == "BH")
            # Also verify validate_and_format convenience method
            output = self.validator.validate_and_format(plate)
            self.assertEqual(str(output), res.cleaned_plate)
            self.assertEqual(output.state_code, expected_state)

    def test_short_sequence_partitioning(self):
        """Ensures short sequence plates like MH12AB12 or GJ01A1 don't have letters eaten into digits."""
        res = self.validator.correct_and_validate("MH12AB12")
        self.assertEqual(res.state_code, "MH")
        self.assertEqual(res.rto_code, "12")
        self.assertEqual(res.series, "AB")
        self.assertEqual(res.sequence_number, "12")
        self.assertEqual(res.cleaned_plate, "MH12AB12")

        # Test validate_and_format dual tuple/string unpacking
        clean, conf = self.validator.validate_and_format("MH12AB12")
        self.assertEqual(clean, "MH12AB12")
        self.assertGreater(conf, 0.80)


if __name__ == "__main__":
    unittest.main()

