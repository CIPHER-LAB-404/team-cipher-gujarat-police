"""
=============================================================================
Stage 3: Sequence-Based Optical Character Recognition (CRNN + CTC / LPRNet)
=============================================================================
- Indian Multi-Line Plate Detection & Row Slicing / Horizontal Stacking
- Geometric Deskewing & Multi-Variant Preprocessing (7 passes)
- Deep Learning EasyOCR Engine with candidate collection & ranking
- Integrated Indian Registration Rule Validation (MoRTH & CMVR)
- Preservation of raw_ocr, normalized_ocr, and validated_plate
=============================================================================
"""

import os
import re
import logging
from typing import List, Tuple, Optional, Dict, Any

import cv2
import numpy as np

try:
    import easyocr
except ImportError:
    easyocr = None

from ..config import ANPRConfig, DEFAULT_CONFIG
from ..preprocessing import PlatePreprocessor, QualityMetrics
from ..postprocess.syntax_validator import IndianPlateSyntaxValidator, PlateValidationResult

logger = logging.getLogger("ANPR_OCR")


class CTCDecoder:
    """
    Decodes raw CTC probability matrices from CRNN / LPRNet models:
    - Collapses consecutive duplicate character predictions
    - Strips the CTC blank token (index 0)
    - Computes average sequence confidence score
    """

    def __init__(self, vocab: str, blank_idx: int = 0):
        self.vocab = vocab
        self.blank_idx = blank_idx
        # Map class index to character (index 0 is reserved for blank)
        self.idx_to_char = {i + 1: char for i, char in enumerate(vocab)}
        self.idx_to_char[blank_idx] = ""

    def decode_greedy(self, logits_or_probs: np.ndarray) -> Tuple[str, float]:
        """
        Greedy Best-Path CTC Decoding:
        Args:
            logits_or_probs: Array of shape [T, C] (time steps, num_classes)
        Returns:
            (decoded_string, average_confidence)
        """
        if logits_or_probs.ndim == 3:
            logits_or_probs = np.squeeze(logits_or_probs, axis=0)

        exp_vals = np.exp(logits_or_probs - np.max(logits_or_probs, axis=-1, keepdims=True))
        probs = exp_vals / np.sum(exp_vals, axis=-1, keepdims=True)

        best_indices = np.argmax(probs, axis=-1)
        best_scores = np.max(probs, axis=-1)

        decoded_chars = []
        character_scores = []
        prev_idx = -1

        for t in range(len(best_indices)):
            idx = int(best_indices[t])
            if idx != prev_idx and idx != self.blank_idx:
                char = self.idx_to_char.get(idx, "")
                if char:
                    decoded_chars.append(char)
                    character_scores.append(float(best_scores[t]))
            prev_idx = idx

        plate_str = "".join(decoded_chars)
        avg_conf = float(np.mean(character_scores)) if character_scores else 0.0
        return plate_str, round(avg_conf, 4)


class OCRResult(tuple):
    """
    Structured OCR result object providing both tuple unpacking (text, conf, is_ml)
    and full attribute access for pipeline stages.
    """

    def __new__(cls, text: str, confidence: float, is_multiline: bool, validation_result: Optional[PlateValidationResult] = None):
        return super().__new__(cls, (text, confidence, is_multiline))

    def __init__(self, text: str, confidence: float, is_multiline: bool, validation_result: Optional[PlateValidationResult] = None):
        self.text = text
        self.confidence = confidence
        self.is_multiline = is_multiline
        self.validation_result = validation_result
        self.raw_text = text if validation_result is None else validation_result.raw_plate
        self.variant_used = "default"


class PlateOCREngine:
    """
    Production-Grade License Plate OCR Engine.
    Executes sequence character recognition using:
    1. Deskewing and quality assessment
    2. Multi-line 2-tier plate decomposition
    3. Multi-variant preprocessing (CLAHE, bilateral, thresholding)
    4. EasyOCR candidate collection & ranking
    5. Integrated IndianPlateSyntaxValidator evaluation
    """

    def __init__(self, config: Optional[ANPRConfig] = None):
        self.config = config or DEFAULT_CONFIG
        self.input_size = self.config.ocr_input_size
        self.vocab = self.config.ocr_characters
        self.blank_idx = self.config.blank_index

        self.ctc_decoder = CTCDecoder(self.vocab, self.blank_idx)
        self.preprocessor = PlatePreprocessor()
        self.validator = IndianPlateSyntaxValidator(self.config)

        # Initialize EasyOCR Deep Learning Reader
        self.easyocr_reader = None
        if easyocr is not None:
            try:
                use_gpu = getattr(self.config, "device", "cpu") == "cuda"
                self.easyocr_reader = easyocr.Reader(['en'], gpu=use_gpu)
                logger.info(f"Initialized EasyOCR reader in PlateOCREngine (GPU: {use_gpu}).")
            except Exception as e:
                logger.warning(f"Failed to initialize EasyOCR reader: {e}")

        # Also attempt FastPlateOCR if available
        self.fast_recognizer = None
        try:
            from fast_plate_ocr import LicensePlateRecognizer
            self.fast_recognizer = LicensePlateRecognizer(hub_ocr_model="cct-s-v2-global-model", device="cpu")
            logger.info("Initialized FastPlateOCR fallback in PlateOCREngine.")
        except Exception:
            pass

        self._initialize_backend()

    def _initialize_backend(self):
        """Loads ONNX Runtime session or PyTorch model."""
        self.is_mobile_vit = False
        self.mobile_vit_alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_"
        cfg_path = getattr(self.config, "ocr_config_path", "")
        if cfg_path and os.path.exists(cfg_path):
            try:
                import yaml
                with open(cfg_path, "r") as f:
                    ycfg = yaml.safe_load(f)
                    if "alphabet" in ycfg:
                        self.mobile_vit_alphabet = ycfg["alphabet"]
            except Exception:
                pass

        # 1. Try ONNX Model
        if self.config.ocr_model_path.endswith(".onnx") and os.path.exists(self.config.ocr_model_path):
            try:
                import onnxruntime as ort
                providers = []
                if self.config.device in ["cuda", "tensorrt"]:
                    providers.append("CUDAExecutionProvider")
                providers.append("CPUExecutionProvider")

                sess_options = ort.SessionOptions()
                sess_options.intra_op_num_threads = self.config.num_threads
                sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

                self.session = ort.InferenceSession(self.config.ocr_model_path, sess_options, providers=providers)
                self.input_name = self.session.get_inputs()[0].name
                self.output_names = [o.name for o in self.session.get_outputs()]
                self.backend = "onnx"

                in_type = self.session.get_inputs()[0].type
                if "uint8" in in_type or "mobile_vit" in self.config.ocr_model_path.lower():
                    self.is_mobile_vit = True
                    logger.info(f"Loaded MobileViT v2 OCR ONNX model from {self.config.ocr_model_path}")
                else:
                    logger.info(f"Loaded OCR ONNX session from {self.config.ocr_model_path}")
                return
            except Exception as e:
                logger.warning(f"Failed loading OCR ONNX model: {e}")

        # 2. Try PyTorch Model
        if os.path.exists(self.config.ocr_pt_path):
            try:
                import torch
                self.torch_model = torch.load(self.config.ocr_pt_path, map_location=self.config.device)
                self.torch_model.eval()
                self.backend = "torch"
                logger.info(f"Loaded PyTorch OCR model from {self.config.ocr_pt_path}")
                return
            except Exception as e:
                logger.warning(f"Failed loading PyTorch OCR model: {e}")

        self.backend = "mock"
        logger.info("Initialized PlateOCREngine in adaptive multi-variant mode.")

    def _recognize_easyocr_multivariant(
        self,
        plate_crop: np.ndarray,
        is_multiline: bool,
        vehicle_type: Optional[str] = None
    ) -> Optional[Tuple[str, float, str, PlateValidationResult]]:
        """
        Executes EasyOCR across multiple preprocessing variants and returns the best candidate.
        Ranks candidates by combining OCR raw score with Indian registration rule validation.
        """
        if self.easyocr_reader is None or plate_crop is None or plate_crop.size == 0:
            return None

        h, w = plate_crop.shape[:2]
        if h < 8 or w < 16:
            return None

        # Deskew image if slanted
        rectified = PlatePreprocessor.deskew_plate(plate_crop)

        # Multi-line decomposition if aspect ratio < 2.3 or two-wheeler
        aspect = float(w) / max(1, float(h))
        stitched, was_split = PlatePreprocessor.process_multiline_plate(rectified, aspect, vehicle_type)
        is_ml = is_multiline or was_split

        # Generate 7 distinct image passes
        variants = PlatePreprocessor.generate_ocr_variants(stitched)

        candidates = []

        for variant_name, img_variant in variants:
            try:
                dets = self.easyocr_reader.readtext(
                    img_variant,
                    detail=1,
                    paragraph=False,
                    allowlist="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ^↑",
                    width_ths=0.7,
                    height_ths=0.7
                )
                if not dets:
                    continue

                parsed_items = []
                for box, text, conf in dets:
                    clean_seg = re.sub(r'[^A-Z0-9\^↑]', '', str(text).upper().replace("IND", ""))
                    if clean_seg:
                        y_mid = (box[0][1] + box[2][1]) / 2.0
                        x_mid = (box[0][0] + box[1][0]) / 2.0
                        parsed_items.append((y_mid, x_mid, clean_seg, float(conf)))

                if not parsed_items:
                    continue

                # Sort horizontally (or row-by-row if not pre-stitched)
                h_cur = img_variant.shape[0]
                if not was_split and (is_ml or (len(parsed_items) > 1 and max(it[0] for it in parsed_items) - min(it[0] for it in parsed_items) > h_cur * 0.28)):
                    mid_y = h_cur * 0.50
                    tier1 = [it for it in parsed_items if it[0] < mid_y]
                    tier2 = [it for it in parsed_items if it[0] >= mid_y]
                    tier1.sort(key=lambda item: item[1])
                    tier2.sort(key=lambda item: item[1])
                    sorted_items = tier1 + tier2
                else:
                    sorted_items = sorted(parsed_items, key=lambda item: item[1])

                combined_str = "".join([item[2] for item in sorted_items])
                avg_c = float(np.mean([item[3] for item in sorted_items]))

                if len(combined_str) >= 4:
                    # Validate candidate against Indian registration rules
                    v_res = self.validator.correct_and_validate(combined_str, initial_confidence=avg_c)
                    
                    # Compute composite rank score
                    # Priority order: Actual Image Evidence -> OCR Evidence -> Rule Validation
                    composite_score = avg_c * 0.50
                    if v_res.validation_status == "VALID":
                        composite_score += 0.40
                    elif v_res.validation_status == "PLAUSIBLE":
                        composite_score += 0.25
                    elif v_res.validation_status == "UNCERTAIN":
                        composite_score += 0.10

                    if 8 <= len(v_res.validated_plate) <= 10:
                        composite_score += 0.10

                    candidates.append((composite_score, combined_str, avg_c, variant_name, v_res))

                    if v_res.validation_status == "VALID" and avg_c > 0.82:
                        # Early exit on high-confidence valid hit
                        break
            except Exception:
                continue

        if not candidates:
            return None

        # Pick candidate with highest composite score
        candidates.sort(key=lambda c: c[0], reverse=True)
        best_cand = candidates[0]
        _, best_text, best_conf, best_variant, best_vres = best_cand

        return best_text, round(best_conf, 3), best_variant, best_vres

    def recognize(
        self,
        plate_crop: np.ndarray,
        vehicle_type: Optional[str] = None
    ) -> OCRResult:
        """
        Performs OCR on cropped plate image with multi-engine cascade.
        Returns:
            OCRResult object (which also unpacks as (text, confidence, is_multiline))
        """
        if plate_crop is None or plate_crop.size == 0:
            return OCRResult("", 0.0, False)

        h, w = plate_crop.shape[:2]
        aspect = float(w) / max(1, float(h))
        is_multiline = aspect < 2.3

        # 1. Primary: EasyOCR Multi-Variant Pipeline
        if self.easyocr_reader is not None:
            easy_res = self._recognize_easyocr_multivariant(plate_crop, is_multiline, vehicle_type)
            if easy_res is not None:
                text, conf, variant, v_res = easy_res
                res = OCRResult(v_res.validated_plate, conf, is_multiline, v_res)
                res.variant_used = variant
                return res

        # 2. Secondary: FastPlateOCR fallback if available
        if getattr(self, "fast_recognizer", None):
            try:
                pred = self.fast_recognizer.run_one(plate_crop)
                if pred and pred.plate:
                    clean = pred.plate.replace("_", "").strip()
                    if len(clean) >= 4:
                        v_res = self.validator.correct_and_validate(clean, initial_confidence=0.88)
                        res = OCRResult(v_res.validated_plate, 0.88, is_multiline, v_res)
                        res.variant_used = "fast_plate"
                        return res
            except Exception:
                pass

        # 3. Tertiary: CTC ONNX Runtime inference
        if self.backend == "onnx" and getattr(self, "session", None) is not None and not getattr(self, "is_mobile_vit", False):
            try:
                # Preprocess
                target_w, target_h = self.input_size
                resized = cv2.resize(plate_crop, (target_w, target_h), interpolation=cv2.INTER_CUBIC)
                blob = resized.transpose(2, 0, 1).astype(np.float32) / 255.0
                blob = (blob - 0.5) / 0.5
                blob = np.expand_dims(blob, axis=0)

                outputs = self.session.run(self.output_names, {self.input_name: blob})
                raw_plate, conf = self.ctc_decoder.decode_greedy(outputs[0])
                if len(raw_plate) >= 4:
                    v_res = self.validator.correct_and_validate(raw_plate, initial_confidence=conf)
                    res = OCRResult(v_res.validated_plate, conf, is_multiline, v_res)
                    res.variant_used = "onnx_ctc"
                    return res
            except Exception as e:
                logger.warning(f"Error during ONNX OCR inference: {e}")

        # If no characters detected with confidence, return empty result
        return OCRResult("", 0.0, is_multiline)
