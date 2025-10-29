#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import numpy as np
import logging
from typing import Dict, Any, List, Tuple

from ..core import constants as const

logger = logging.getLogger(__name__)


class ImageEnhancer:

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def enhance_portrait(self, image: np.ndarray, characteristics: Dict[str, Any]) -> np.ndarray:
        enhanced = image.copy()

        if characteristics['has_faces']:
            enhanced = self._apply_face_aware_clahe(enhanced, characteristics['faces'])
        else:
            clahe = cv2.createCLAHE(clipLimit=const.PORTRAIT_CLAHE_CLIP_LIMIT,
                                   tileGridSize=const.PORTRAIT_CLAHE_TILE_SIZE)
            enhanced = clahe.apply(enhanced.astype(np.uint8)).astype(np.float64)

        return enhanced

    def _apply_face_aware_clahe(self, image: np.ndarray,
                               faces: List[Tuple[int, int, int, int]]) -> np.ndarray:
        enhanced = image.copy()

        for (x, y, w, h) in faces:
            face_roi = enhanced[y:y+h, x:x+w]

            clahe_face = cv2.createCLAHE(clipLimit=const.FACE_CLAHE_CLIP_LIMIT,
                                        tileGridSize=const.FACE_CLAHE_TILE_SIZE)
            enhanced_face = clahe_face.apply(face_roi.astype(np.uint8)).astype(np.float64)

            enhanced[y:y+h, x:x+w] = (face_roi * const.FACE_ORIGINAL_BLEND_WEIGHT +
                                      enhanced_face * const.FACE_ENHANCED_BLEND_WEIGHT)

        clahe_general = cv2.createCLAHE(clipLimit=const.GENERAL_CLAHE_CLIP_LIMIT,
                                       tileGridSize=const.GENERAL_CLAHE_TILE_SIZE)
        enhanced = clahe_general.apply(enhanced.astype(np.uint8)).astype(np.float64)

        return enhanced

    def correct_underexposure(self, image: np.ndarray) -> np.ndarray:
        normalized = image / 255.0
        corrected = np.power(normalized, const.UNDEREXPOSURE_GAMMA)
        shadow_mask = normalized < const.UNDEREXPOSURE_SHADOW_THRESHOLD
        corrected[shadow_mask] += const.UNDEREXPOSURE_SHADOW_BOOST * (const.UNDEREXPOSURE_SHADOW_THRESHOLD - normalized[shadow_mask])
        return corrected * 255.0

    def recover_highlights(self, image: np.ndarray) -> np.ndarray:
        normalized = image / 255.0
        highlight_mask = normalized > const.OVEREXPOSURE_HIGHLIGHT_THRESHOLD
        compressed = np.power(normalized, const.OVEREXPOSURE_GAMMA)
        compressed[highlight_mask] = const.OVEREXPOSURE_HIGHLIGHT_THRESHOLD + (normalized[highlight_mask] - const.OVEREXPOSURE_HIGHLIGHT_THRESHOLD) * const.OVEREXPOSURE_HIGHLIGHT_COMPRESS
        return compressed * 255.0

    def enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        clahe = cv2.createCLAHE(clipLimit=const.CONTRAST_ENHANCE_CLAHE_CLIP, tileGridSize=const.CONTRAST_ENHANCE_CLAHE_TILE_SIZE)
        enhanced = clahe.apply(image.astype(np.uint8))
        return enhanced.astype(np.float64)

    def lift_shadows(self, image: np.ndarray) -> np.ndarray:
        normalized = image / 255.0
        shadow_mask = normalized < const.SHADOW_LIFT_THRESHOLD
        enhanced = normalized.copy()
        enhanced[shadow_mask] = np.power(normalized[shadow_mask], const.SHADOW_LIFT_GAMMA)
        return enhanced * 255.0

    def compress_highlights(self, image: np.ndarray) -> np.ndarray:
        normalized = image / 255.0
        highlight_mask = normalized > const.HIGHLIGHT_COMPRESS_THRESHOLD
        compressed = normalized.copy()
        compressed[highlight_mask] = const.HIGHLIGHT_COMPRESS_THRESHOLD + (normalized[highlight_mask] - const.HIGHLIGHT_COMPRESS_THRESHOLD) * const.HIGHLIGHT_COMPRESS_FACTOR
        return compressed * 255.0

    def apply_universal_enhancement(self, image: np.ndarray,
                                   characteristics: Dict[str, Any]) -> np.ndarray:
        denoised = cv2.bilateralFilter(image.astype(np.uint8), d=const.BILATERAL_D_FIRST,
                                       sigmaColor=const.BILATERAL_SIGMA_COLOR_FIRST,
                                       sigmaSpace=const.BILATERAL_SIGMA_SPACE_FIRST)
        denoised = cv2.bilateralFilter(denoised, d=const.BILATERAL_D_SECOND,
                                       sigmaColor=const.BILATERAL_SIGMA_COLOR_SECOND,
                                       sigmaSpace=const.BILATERAL_SIGMA_SPACE_SECOND)

        image_type = characteristics.get('image_type', 'balanced')
        is_portrait = image_type in ["portrait", "portrait_low_contrast"]

        if is_portrait:
            enhanced = denoised.astype(np.float64)
        else:
            enhanced = denoised.astype(np.float64)

        return enhanced

    def _professional_sharpening(self, image: np.ndarray) -> np.ndarray:
        gaussian_1 = cv2.GaussianBlur(image, (0, 0), 1.0)
        gaussian_2 = cv2.GaussianBlur(image, (0, 0), 3.0)

        detail_mask = image - gaussian_1
        structure_mask = gaussian_1 - gaussian_2

        sharpened = image + (detail_mask * const.SHARPENING_DETAIL_WEIGHT) + (structure_mask * const.SHARPENING_STRUCTURE_WEIGHT)
        return sharpened
