"""
=============================================================================
Gujarat Police Sentinel - Indian Motor Vehicle Registration Rule Engine
=============================================================================
Modular, rule-based registration validation engine for Indian Motor Vehicles.
Implements official Ministry of Road Transport and Highways (MoRTH) & CMVR rules.

Differentiates:
1. Physical plate detection
2. Raw OCR textual content
3. Plausibility under Indian Motor Vehicle rules
4. Registration category classification
5. Choice / Fancy number pattern evaluation

Supported Validation Statuses:
- VALID: Strictly adheres to official active MoRTH syntax specifications.
- PLAUSIBLE: Unusual or legacy registration that is legally or historically viable.
- UNCERTAIN: Potential plate text with ambiguous or incomplete character evidence.
- INVALID: Clearly non-plate noise (bumper stickers, road signs, random words).
=============================================================================
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

from .state_registry import IndianStateRegistry, StateRecord


@dataclass
class PlateValidationResult:
    """Encapsulates the complete result of Indian registration rule validation."""
    raw_plate: str
    normalized_plate: str
    validated_plate: str
    is_valid_format: bool
    validation_status: str  # "VALID", "PLAUSIBLE", "UNCERTAIN", "INVALID"
    plate_category: str     # "STANDARD_PRIVATE", "BHARAT_SERIES", "TRANSPORT_COMMERCIAL", "ELECTRIC_VEHICLE",
                            # "TEMPORARY", "DEALER_TRADE", "DIPLOMATIC", "CONSULAR", "SPECIAL_MISSION",
                            # "DEFENSE", "LEGACY", "UNKNOWN_SPECIAL"
    number_type: str        # "GENERAL", "CHOICE_FANCY_PATTERN", "UNKNOWN"
    fancy_pattern_description: str  # e.g. "Pattern appears special/fancy (single digit / repeating)"
    state_code: str
    state_name: str
    is_legacy_state: bool
    rto_code: str
    series: str
    sequence_number: str
    confidence: float
    corrections_made: List[str]
    reason: str

    # Backward compatibility properties
    @property
    def cleaned_plate(self) -> str:
        return self.validated_plate

    @property
    def plate_type(self) -> str:
        return self.plate_category


class FancyPatternEvaluator:
    """
    Evaluates numeric sequences for distinctive, choice, or reserved patterns.
    NOTE: In India, VIP/Choice numbers do NOT have a unique plate syntax.
    They are valid numbers in standard series that appear distinctive.
    This evaluator labels them as 'Pattern appears special/fancy' without modifying OCR.
    """

    # Well-known distinctive pattern types
    SPECIAL_PATTERNS = {
        "0001": "Chief Executive / Single digit sequence 0001",
        "0007": "Single digit James Bond sequence 0007",
        "1111": "Full quad repetition 1111",
        "2222": "Full quad repetition 2222",
        "3333": "Full quad repetition 3333",
        "4444": "Full quad repetition 4444",
        "5555": "Full quad repetition 5555",
        "6666": "Full quad repetition 6666",
        "7777": "Full quad repetition 7777",
        "8888": "Full quad repetition 8888",
        "9999": "Full quad repetition 9999",
        "1234": "Sequential ascending 1234",
        "4321": "Sequential descending 4321",
        "0786": "Special religious / choice allocation 0786",
        "0100": "Century round number 0100",
        "1000": "Millennium round number 1000",
    }

    @classmethod
    def evaluate(cls, sequence_num: str) -> Tuple[str, str]:
        """
        Evaluates numeric sequence.
        Returns: (number_type, description)
        """
        if not sequence_num or not sequence_num.isdigit():
            return "GENERAL", ""

        seq = sequence_num.strip()
        padded_4 = seq.zfill(4)

        # 1. Exact match in catalog
        if padded_4 in cls.SPECIAL_PATTERNS:
            return "CHOICE_FANCY_PATTERN", f"Pattern appears special/fancy: {cls.SPECIAL_PATTERNS[padded_4]}"

        # 2. Leading zeros (0002 - 0009)
        if len(padded_4) == 4 and padded_4.startswith("000") and padded_4[-1] != "0":
            return "CHOICE_FANCY_PATTERN", f"Pattern appears special/fancy: Single digit {seq}"

        # 3. Triple repeating (e.g. 0777, 7770, 9991)
        if len(padded_4) == 4:
            d0, d1, d2, d3 = padded_4
            if (d0 == d1 == d2) or (d1 == d2 == d3):
                return "CHOICE_FANCY_PATTERN", "Pattern appears special/fancy: Triple repeating digits"
            # Symmetric palindromes (e.g. 1221, 5005, 8008)
            if d0 == d3 and d1 == d2:
                return "CHOICE_FANCY_PATTERN", "Pattern appears special/fancy: Palindromic sequence"
            # Dual pair repetition (e.g. 1212, 6969, 4545)
            if d0 == d2 and d1 == d3:
                return "CHOICE_FANCY_PATTERN", "Pattern appears special/fancy: Dual alternating pair"

        return "GENERAL", ""


class IndianPlateSyntaxValidator:
    """
    Expert Rule Engine for Indian Vehicle Registrations.
    Separates syntax rules into distinct evaluators for:
    - Standard State/UT civilian registrations
    - Bharat Series (BH)
    - Temporary registrations (evidence-based)
    - Dealer / Trade registrations
    - Diplomatic, Consular & Special Missions
    - Ministry of Defence armed forces marks
    - Legacy / Historical administrative codes
    """

    def __init__(self, config: Optional[Any] = None):
        self.config = config
        self.registry = IndianStateRegistry

        # Contextual confusion mappings (strictly position-dependent)
        self.digit_to_letter = {
            '0': 'O', '1': 'I', '2': 'Z', '3': 'E', '4': 'A',
            '5': 'S', '6': 'G', '7': 'T', '8': 'B', '9': 'P'
        }
        self.letter_to_digit = {
            'O': '0', 'D': '0', 'Q': '0',
            'I': '1', 'L': '1', 'T': '1',
            'Z': '2',
            'E': '3',
            'A': '4',
            'S': '5',
            'G': '6',
            'B': '8',
            'P': '9'
        }

        # Common OCR state candidate confusions that map cleanly to valid states
        self.state_ocr_corrections = {
            "G0": "GJ", "GI": "GJ", "GL": "GJ", "CJ": "GJ", "OJ": "GJ", "QJ": "GJ", "6J": "GJ",
            "M0": "MH", "MI": "MH", "NH": "MH", "VH": "MH", "M8": "MH",
            "D1": "DL", "DI": "DL", "0L": "DL", "OL": "DL",
            "R1": "RJ", "RI": "RJ", "R0": "RJ",
            "M9": "MP", "U0": "UP",
            "K4": "KA", "K0": "KA", "KI": "KL",
            "T0": "TN", "T1": "TS", "H0": "HR", "H1": "HR", "P8": "PB"
        }

    @staticmethod
    def clean_text(raw_text: str) -> str:
        """
        Normalizes OCR string by removing whitespace, punctuation,
        and leading High Security Registration Plate (HSRP) 'IND' emblems.
        Preserves essential characters.
        """
        if not raw_text:
            return ""
        text = str(raw_text).upper().strip()
        # Remove common HSRP country stamp prefixes (IND / INDIA variants)
        text = re.sub(r'^(?:IND|1ND|LND|TND|1N0|IN0|INDIA|ND|1N|IN|ID|1D)[\s\.\-_]+', '', text)
        text = re.sub(r'^(?:IND|1ND|LND|TND|1N0|IN0|INDIA)[\s\.\-_]*', '', text)
        cleaned = re.sub(r"[^A-Z0-9\^↑]", "", text)
        cleaned = re.sub(r'^(?:IND|1ND|LND|TND|1N0|IN0|INDIA)', '', cleaned)
        # If leading 2 characters are IN/1N and next 2 form a known Indian state (e.g. INGJ01 -> GJ01)
        if len(cleaned) >= 6 and cleaned[:2] in ['IN', '1N', 'ID', '1D']:
            cand = cleaned[2:4]
            if IndianStateRegistry.get_state(cand) is not None:
                cleaned = cleaned[2:]
        return cleaned

    def correct_and_validate(
        self,
        raw_ocr_text: str,
        initial_confidence: float = 0.90,
        visual_category_hint: Optional[str] = None
    ) -> PlateValidationResult:
        """
        Executes rule-driven evaluation of an OCR string.
        Prioritizes:
        1. Defence Armed Forces Rule
        2. Diplomatic / Consular / UN Rule
        3. Bharat Series (BH) Rule
        4. Standard State / UT Rule (Active and Legacy)
        5. Trade / Temporary evidence-based validation
        6. Non-Plate Noise Rejection
        """
        raw_clean = self.clean_text(raw_ocr_text)
        corrections: List[str] = []
        penalty = 0.0

        if not raw_clean or len(raw_clean) < 4:
            return PlateValidationResult(
                raw_plate=raw_ocr_text,
                normalized_plate=raw_clean,
                validated_plate=raw_clean,
                is_valid_format=False,
                validation_status="INVALID",
                plate_category="UNKNOWN_SPECIAL",
                number_type="UNKNOWN",
                fancy_pattern_description="",
                state_code="",
                state_name="Invalid / Insufficient Length",
                is_legacy_state=False,
                rto_code="",
                series="",
                sequence_number="",
                confidence=round(max(0.1, initial_confidence * 0.3), 3),
                corrections_made=["Length < 4 characters"],
                reason="String too short to represent any valid Indian registration"
            )

        # ---------------------------------------------------------------------
        # Rule Branch 1: Defence / Military Armed Forces Registrations
        # Official format: Upward Arrow (broad arrow) + 2-digit Year of induction + Base/Class Letter + 5-6 digits + Letter
        # e.g., ^21B123456C or 21B123456C
        # ---------------------------------------------------------------------
        def_res = self._evaluate_defence_rules(raw_clean, raw_ocr_text, initial_confidence)
        if def_res is not None:
            return def_res

        # ---------------------------------------------------------------------
        # Rule Branch 2: Diplomatic / Consular / Special Mission (CD / CC / UN)
        # Formats: e.g. 77 CD 1234 (Embassy), 19 CC 5678 (Consulate), 55 UN 7890 (United Nations)
        # Note: Must NOT be forced into Civilian State+RTO logic.
        # ---------------------------------------------------------------------
        dip_res = self._evaluate_diplomatic_rules(raw_clean, raw_ocr_text, initial_confidence)
        if dip_res is not None:
            return dip_res

        # ---------------------------------------------------------------------
        # Rule Branch 3: Bharat Series (BH) Registrations
        # Structure: YY BH #### XX (2 digits Year + 'BH' + 4 digits Sequence + 1-2 letters Series)
        # ---------------------------------------------------------------------
        bh_res = self._evaluate_bharat_series_rules(raw_clean, raw_ocr_text, initial_confidence)
        if bh_res is not None:
            return bh_res

        # ---------------------------------------------------------------------
        # Rule Branch 4: Standard State / UT Civilian Registrations
        # Structure: [State 2L] + [RTO 1-2D] + [Series 0-3L] + [Sequence 1-4D]
        # Supports active codes + legacy codes (UA, OR, DD, DN)
        # ---------------------------------------------------------------------
        state_res = self._evaluate_state_rules(raw_clean, raw_ocr_text, initial_confidence, visual_category_hint)
        if state_res is not None:
            return state_res

        # ---------------------------------------------------------------------
        # Rule Branch 5: General Alphanumeric / Unclassified Plausible vs Noise
        # ---------------------------------------------------------------------
        # Detect roadside advertising, traffic signage, bumper text noise
        non_plate_keywords = {
            "SALE", "STOP", "SHOP", "EXIT", "PARKING", "SPEED", "FAST", "OFFER",
            "SUPER", "DISCOUNT", "HONK", "PLEASE", "HOTEL", "ROOMS", "FLAT", "ROAD"
        }
        is_noise = any(kw in raw_clean for kw in non_plate_keywords)

        has_letters = any(c.isalpha() for c in raw_clean)
        has_digits = any(c.isdigit() for c in raw_clean)
        
        if is_noise or not has_letters or not has_digits or len(raw_clean) < 4:
            status = "INVALID"
            category = "NON_PLATE_NOISE"
            reason = "Text matches non-plate noise keywords or lacks valid alphanumeric structure"
        elif len(raw_clean) >= 6 and initial_confidence >= 0.60:
            status = "PLAUSIBLE"
            category = "UNKNOWN_SPECIAL"
            reason = "Alphanumeric pattern does not match official State, BH, or Special registers"
        else:
            status = "UNCERTAIN"
            category = "UNCERTAIN_FRAGMENT"
            reason = "Crop contains partial or unverified character sequence"

        return PlateValidationResult(
            raw_plate=raw_ocr_text,
            normalized_plate=raw_clean,
            validated_plate=raw_clean,
            is_valid_format=False,
            validation_status=status,
            plate_category=category,
            number_type="GENERAL",
            fancy_pattern_description="",
            state_code="",
            state_name="Unclassified / General",
            is_legacy_state=False,
            rto_code="",
            series="",
            sequence_number=raw_clean,
            confidence=round(initial_confidence * 0.5 if status == "PLAUSIBLE" else (initial_confidence * 0.3 if status == "UNCERTAIN" else initial_confidence * 0.1), 3),
            corrections_made=[],
            reason=reason
        )

    def _evaluate_defence_rules(
        self,
        cleaned: str,
        raw_text: str,
        initial_conf: float
    ) -> Optional[PlateValidationResult]:
        """Validates Indian Armed Forces / Ministry of Defence registrations."""
        # Check for explicit broad arrow symbol (^ or ↑)
        has_arrow = cleaned.startswith('^') or cleaned.startswith('↑') or '^' in cleaned or '↑' in cleaned
        norm = cleaned.replace('^', '').replace('↑', '')

        # Standard military plate: 2 digits (year) + 1 letter (base/category) + 5 to 6 digits + 1 check letter
        # e.g., 21B123456C
        def_pattern = re.compile(r"^[0-9]{2}[A-Z][0-9]{5,6}[A-Z]$")
        if def_pattern.match(norm) or (has_arrow and len(norm) >= 7):
            fancy_type, fancy_desc = FancyPatternEvaluator.evaluate(norm[3:-1])
            validated = f"^{norm}" if has_arrow else norm
            return PlateValidationResult(
                raw_plate=raw_text,
                normalized_plate=norm,
                validated_plate=validated,
                is_valid_format=True,
                validation_status="VALID",
                plate_category="DEFENSE",
                number_type=fancy_type,
                fancy_pattern_description=fancy_desc,
                state_code="DEF",
                state_name="Ministry of Defence (Armed Forces)",
                is_legacy_state=False,
                rto_code="",
                series=norm[2] if len(norm) > 2 else "",
                sequence_number=norm[3:-1] if len(norm) > 4 else norm[3:],
                confidence=round(min(0.98, initial_conf + 0.04), 3),
                corrections_made=["Defence broad arrow / military sequence validated"],
                reason="Compliant Indian Defence Ministry registration specification"
            )
        return None

    def _evaluate_diplomatic_rules(
        self,
        cleaned: str,
        raw_text: str,
        initial_conf: float
    ) -> Optional[PlateValidationResult]:
        """Validates foreign diplomatic, consular, and international mission registrations."""
        # Patterns: [1-3 digits country code] [CD|CC|UN] [1-4 digits vehicle sequence]
        # or [CD|CC|UN] [1-4 digits]
        dip_match = re.match(r"^([0-9]{1,3})?(CD|CC|UN)([0-9]{1,4})$", cleaned)
        if dip_match:
            country_code = dip_match.group(1) or ""
            corp_type = dip_match.group(2)
            seq = dip_match.group(3)

            cat_map = {
                "CD": ("DIPLOMATIC", "Diplomatic Corps (Embassy)"),
                "CC": ("CONSULAR", "Consular Corps (Consulate)"),
                "UN": ("SPECIAL_MISSION", "United Nations Mission")
            }
            cat_name, full_name = cat_map.get(corp_type, ("DIPLOMATIC", "Foreign Mission"))
            fancy_type, fancy_desc = FancyPatternEvaluator.evaluate(seq)

            return PlateValidationResult(
                raw_plate=raw_text,
                normalized_plate=cleaned,
                validated_plate=cleaned,
                is_valid_format=True,
                validation_status="VALID",
                plate_category=cat_name,
                number_type=fancy_type,
                fancy_pattern_description=fancy_desc,
                state_code="DIP",
                state_name=full_name,
                is_legacy_state=False,
                rto_code=country_code,
                series=corp_type,
                sequence_number=seq,
                confidence=round(initial_conf, 3),
                corrections_made=[],
                reason=f"Valid {full_name} mark with mission code {country_code or 'HQ'}"
            )
        return None

    def _evaluate_bharat_series_rules(
        self,
        cleaned: str,
        raw_text: str,
        initial_conf: float
    ) -> Optional[PlateValidationResult]:
        """
        Validates official Bharat Series (BH) registrations.
        Specification: YY BH #### XX
        where YY = year of registration (e.g. 21, 22, 23, 24, 25, 26)
              BH = Bharat Series literal identifier
              #### = 4-digit sequence (0001 - 9999)
              XX = 1 or 2 letter suffix (excluding I and O in official series)
        """
        n = len(cleaned)
        chars = list(cleaned)

        # Check if candidate has BH indicator (or OCR noise like 8H, BM, 8M at slots 2-3)
        has_bh = (
            n >= 9 and (
                (''.join(chars[2:4]) == "BH") or
                (chars[0].isdigit() and chars[1].isdigit() and chars[2] in ['B', '8'] and chars[3] in ['H', 'M', 'N'])
            )
        )
        if not has_bh:
            return None

        corrections = []
        penalty = 0.0

        # Slot 0-1: Year (must be 2 digits, e.g. 21-29)
        for i in [0, 1]:
            if chars[i] in self.letter_to_digit:
                c_fix = self.letter_to_digit[chars[i]]
                corrections.append(f"BH Year slot {i}: '{chars[i]}' -> '{c_fix}'")
                chars[i] = c_fix
                penalty += 0.02

        # Slot 2-3: Must be literal 'BH'
        if chars[2] != 'B':
            corrections.append(f"BH Mark slot 2: '{chars[2]}' -> 'B'")
            chars[2] = 'B'
            penalty += 0.02
        if chars[3] != 'H':
            corrections.append(f"BH Mark slot 3: '{chars[3]}' -> 'H'")
            chars[3] = 'H'
            penalty += 0.02

        # Slot 4-7: Sequence number (must be 4 digits)
        for i in range(4, min(8, n)):
            if chars[i] in self.letter_to_digit:
                c_fix = self.letter_to_digit[chars[i]]
                corrections.append(f"BH Sequence slot {i}: '{chars[i]}' -> '{c_fix}'")
                chars[i] = c_fix
                penalty += 0.02

        # Slot 8+: Series suffix (1-2 letters)
        for i in range(8, n):
            if chars[i] in self.digit_to_letter:
                c_fix = self.digit_to_letter[chars[i]]
                corrections.append(f"BH Series slot {i}: '{chars[i]}' -> '{c_fix}'")
                chars[i] = c_fix
                penalty += 0.02

        fixed = "".join(chars)
        bh_regex = re.compile(r"^[0-9]{2}BH[0-9]{4}[A-Z]{1,2}$")
        is_valid = bool(bh_regex.match(fixed))

        seq_num = fixed[4:8] if len(fixed) >= 8 else ""
        fancy_type, fancy_desc = FancyPatternEvaluator.evaluate(seq_num)

        final_conf = max(0.80, initial_conf - penalty)
        if is_valid:
            final_conf = min(0.99, final_conf + 0.05)

        return PlateValidationResult(
            raw_plate=raw_text,
            normalized_plate=cleaned,
            validated_plate=fixed,
            is_valid_format=is_valid,
            validation_status="VALID" if is_valid else "PLAUSIBLE",
            plate_category="BHARAT_SERIES",
            number_type=fancy_type,
            fancy_pattern_description=fancy_desc,
            state_code="BH",
            state_name="Bharat Series (National)",
            is_legacy_state=False,
            rto_code=fixed[:2],
            series="BH",
            sequence_number=seq_num,
            confidence=round(final_conf, 3),
            corrections_made=corrections,
            reason="Verified National Bharat Series (BH) registration mark"
        )

    def _evaluate_state_rules(
        self,
        cleaned: str,
        raw_text: str,
        initial_conf: float,
        visual_category_hint: Optional[str] = None
    ) -> Optional[PlateValidationResult]:
        """
        Validates civilian state / UT registration marks.
        Executes:
        - State code lookup (active and legacy)
        - Delhi 1-digit RTO branch vs standard 2-digit RTO branch
        - Candidate partitioning across RTO, Series, and Sequence slots
        - Contextual slot disambiguation
        - Choice / Fancy number evaluation
        """
        chars = list(cleaned)
        n = len(chars)
        corrections: List[str] = []
        penalty = 0.0

        # Step 1: Disambiguate state prefix (slots 0-1)
        # Context rule: In state slots, digits should be letters
        for i in [0, 1]:
            if chars[i].isdigit() and chars[i] in self.digit_to_letter:
                c_fix = self.digit_to_letter[chars[i]]
                corrections.append(f"State slot {i}: '{chars[i]}' -> '{c_fix}'")
                chars[i] = c_fix
                penalty += 0.02

        cand_state = "".join(chars[:2])

        # Check OCR state corrections table (e.g. G0 -> GJ, M0 -> MH, D1 -> DL)
        if cand_state in self.state_ocr_corrections:
            fixed_st = self.state_ocr_corrections[cand_state]
            corrections.append(f"State code disambiguation: '{cand_state}' -> '{fixed_st}'")
            chars[0] = fixed_st[0]
            chars[1] = fixed_st[1]
            cand_state = fixed_st
            penalty += 0.02

        # Look up state record in centralized registry
        state_rec = self.registry.get_state(cand_state)
        if state_rec is None:
            return None  # Not a recognized Indian state code

        is_legacy = state_rec.is_legacy
        state_name = state_rec.name
        rem = "".join(chars[2:])
        rem_len = len(rem)

        if rem_len < 2:
            return None

        # Step 2: Candidate Partitioning across (RTO, Series, Sequence)
        # Partition rules:
        # - Delhi (DL): Allows 1-digit RTO (DL 1C 1234, DL 3SAM 9876) or 2-digit RTO
        # - Other States: Prefer 2-digit RTO (01-99), allow 1-digit RTO for vintage/legacy
        # - Series: 0 to 3 letters
        # - Sequence: 1 to 4 digits
        allowed_rto_lengths = [1, 2] if cand_state == "DL" or is_legacy else [2, 1]

        best_score = -999.0
        best_partition = None

        for r_len in allowed_rto_lengths:
            for s_len in range(0, 4):
                q_len = rem_len - r_len - s_len
                if q_len < 1 or q_len > 4:
                    continue

                r_raw = rem[:r_len]
                s_raw = rem[r_len:r_len + s_len]
                q_raw = rem[r_len + s_len:]

                part_corrections = []
                part_pen = 0.0
                score = 10.0

                # Score RTO slot (context: expected numeric)
                r_fixed = []
                for c in r_raw:
                    if c.isdigit():
                        r_fixed.append(c)
                    elif c in self.letter_to_digit:
                        c_fix = self.letter_to_digit[c]
                        r_fixed.append(c_fix)
                        part_pen += 0.02
                        score -= 0.5
                        part_corrections.append(f"RTO slot '{c}' -> '{c_fix}'")
                    else:
                        r_fixed.append(c)
                        score -= 2.0

                # Score Series slot (context: expected alphabetic)
                s_fixed = []
                for c in s_raw:
                    if c.isalpha():
                        s_fixed.append(c)
                    elif c in self.digit_to_letter:
                        c_fix = self.digit_to_letter[c]
                        s_fixed.append(c_fix)
                        part_pen += 0.02
                        score -= 0.5
                        part_corrections.append(f"Series slot '{c}' -> '{c_fix}'")
                    else:
                        s_fixed.append(c)
                        score -= 2.0

                # Score Sequence slot (context: expected numeric)
                q_fixed = []
                for c in q_raw:
                    if c.isdigit():
                        q_fixed.append(c)
                    elif c in self.letter_to_digit:
                        c_fix = self.letter_to_digit[c]
                        q_fixed.append(c_fix)
                        part_pen += 0.02
                        score -= 0.5
                        part_corrections.append(f"Sequence slot '{c}' -> '{c_fix}'")
                    else:
                        q_fixed.append(c)
                        score -= 2.0

                # Delhi specific prior: DL 1C, DL 3S, etc. where class letter is C, S, B, R, T, P, V, A
                if cand_state == "DL" and r_len == 1:
                    if s_len >= 1 and s_fixed and s_fixed[0] in ['C', 'S', 'B', 'R', 'T', 'P', 'V', 'A']:
                        score += 3.0
                    else:
                        score += 1.0
                elif r_len == 2:
                    score += 2.0

                # Sequence length preference: 4 digits is standard, 1-3 digits is vintage/choice
                if q_len == 4:
                    score += 2.0
                elif q_len >= 1:
                    score += 0.5

                if score > best_score:
                    best_score = score
                    best_partition = ("".join(r_fixed), "".join(s_fixed), "".join(q_fixed), part_corrections, part_pen)

        if best_partition is None:
            return None

        rto_str, series_str, seq_str, part_corrs, part_pen = best_partition
        corrections.extend(part_corrs)
        penalty += part_pen

        validated_plate = f"{cand_state}{rto_str}{series_str}{seq_str}"

        # Evaluate Choice / Fancy number pattern on sequence
        fancy_type, fancy_desc = FancyPatternEvaluator.evaluate(seq_str)

        # Check official regex compliance
        # Standard civilian format: State (2L) + RTO (1-2D) + Series (0-3L) + Seq (1-4D)
        std_regex = re.compile(r"^[A-Z]{2}[0-9]{1,2}[A-Z]{0,3}[0-9]{1,4}$")
        matches_regex = bool(std_regex.match(validated_plate))

        # Standard Indian civilian registrations require at least 6 characters (e.g. GJ 1 1234 or GJ 01 A 1)
        # Anything shorter (e.g. 5 chars like GJ01A) or low confidence is UNCERTAIN (partial crop)
        if matches_regex and len(validated_plate) >= 6 and initial_conf >= 0.50 and len(seq_str) >= 1:
            status = "PLAUSIBLE" if is_legacy else "VALID"
        else:
            status = "UNCERTAIN"

        # Determine category based on syntax and optional visual hints
        if is_legacy:
            category = "LEGACY"
            reason = f"Valid historical {state_name} registration ({cand_state} replaced by {state_rec.replacement_code or 'modern code'})"
        elif visual_category_hint:
            category = visual_category_hint
            reason = f"Valid {state_name} registration with visual category {visual_category_hint}"
        else:
            category = "STANDARD_PRIVATE"
            reason = f"Verified {state_name} civilian registration mark"

        final_conf = max(0.70, initial_conf - penalty)
        if status == "VALID":
            final_conf = min(0.99, final_conf + 0.04)

        return PlateValidationResult(
            raw_plate=raw_text,
            normalized_plate=cleaned,
            validated_plate=validated_plate,
            is_valid_format=(status == "VALID"),
            validation_status=status,
            plate_category=category,
            number_type=fancy_type,
            fancy_pattern_description=fancy_desc,
            state_code=cand_state,
            state_name=state_name,
            is_legacy_state=is_legacy,
            rto_code=rto_str,
            series=series_str,
            sequence_number=seq_str,
            confidence=round(final_conf, 3),
            corrections_made=corrections,
            reason=reason
        )

    def validate_and_format(
        self,
        raw_ocr_text: str,
        initial_confidence: float = 0.90,
        visual_category_hint: Optional[str] = None
    ) -> "ValidationTuple":
        """Convenience method returning a dual tuple/object representation for backwards compatibility."""
        res = self.correct_and_validate(raw_ocr_text, initial_confidence, visual_category_hint)
        return ValidationTuple(res.validated_plate, res.confidence, res)


class ValidationTuple(tuple):
    """Backwards-compatible tuple and object wrapper."""

    def __new__(cls, cleaned_plate: str, confidence: float, res: PlateValidationResult):
        return super().__new__(cls, (cleaned_plate, confidence))

    def __init__(self, cleaned_plate: str, confidence: float, res: PlateValidationResult):
        self.cleaned_plate = cleaned_plate
        self.confidence = confidence
        self.result = res
        self.is_valid_format = res.is_valid_format
        self.validation_status = res.validation_status
        self.plate_type = res.plate_category
        self.plate_category = res.plate_category
        self.number_type = res.number_type
        self.fancy_pattern_description = res.fancy_pattern_description
        self.state_code = res.state_code
        self.rto_code = res.rto_code
        self.series = res.series
        self.sequence_number = res.sequence_number
        self.state_name = res.state_name
        self.corrections_made = res.corrections_made
        self.reason = res.reason

    def __str__(self) -> str:
        return self.cleaned_plate

    def __repr__(self) -> str:
        return f"('{self.cleaned_plate}', {self.confidence})"

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, str):
            return self.cleaned_plate == other
        return super().__eq__(other)
