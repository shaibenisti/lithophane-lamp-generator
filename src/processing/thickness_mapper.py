#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import numpy as np
import logging
from typing import Dict, Any

from ..core.settings import PremiumSettings
from ..core import constants as const

logger = logging.getLogger(__name__)


class ThicknessMapper:

    def __init__(self, settings: PremiumSettings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)

    def create_thickness_map(self, processed_image: np.ndarray,
                            characteristics: Dict[str, Any], smoothed_image: np.ndarray) -> np.ndarray:
        normalized_image = self._adaptive_histogram_normalization(smoothed_image, characteristics)

        normalized = normalized_image.astype(np.float64) / 255.0

        gamma = self.settings.get_gamma_value(characteristics['image_type'])
        gamma_corrected = np.power(normalized, gamma)

        thickness_range = self.settings.max_thickness - self.settings.min_thickness
        base_thickness = self.settings.min_thickness + (gamma_corrected * thickness_range)

        blended_thickness = self._apply_cylindrical_blending(base_thickness)

        return blended_thickness

    def _adaptive_histogram_normalization(self, image: np.ndarray,
                                         characteristics: Dict[str, Any]) -> np.ndarray:
        hist = cv2.calcHist([image.astype(np.uint8)], [0], None, [256], [0, 256])
        cumsum = np.cumsum(hist)
        cumsum_normalized = cumsum / cumsum[-1]

        p2 = np.searchsorted(cumsum_normalized, const.HISTOGRAM_NORMALIZATION_PERCENTILE_LOW)
        p98 = np.searchsorted(cumsum_normalized, const.HISTOGRAM_NORMALIZATION_PERCENTILE_HIGH)

        current_range = p98 - p2

        if current_range < const.HISTOGRAM_NORMALIZATION_MIN_RANGE:
            self.logger.info(f"Applying histogram normalization (current range: {current_range})")

            img_float = image.astype(np.float64)

            img_clipped = np.clip(img_float, p2, p98)

            if p98 > p2:
                target_range = const.HISTOGRAM_NORMALIZATION_TARGET_MAX - const.HISTOGRAM_NORMALIZATION_TARGET_MIN
                normalized = ((img_clipped - p2) / (p98 - p2)) * target_range + const.HISTOGRAM_NORMALIZATION_TARGET_MIN
            else:
                normalized = img_float

            blended = (normalized * const.HISTOGRAM_NORMALIZATION_BLEND_NORMALIZED +
                      img_float * const.HISTOGRAM_NORMALIZATION_BLEND_ORIGINAL)

            return np.clip(blended, 0, 255).astype(np.uint8)
        else:
            self.logger.info(f"Skipping histogram normalization (good range: {current_range})")
            return image

    def _apply_cylindrical_blending(self, thickness_map: np.ndarray) -> np.ndarray:
        height, width = thickness_map.shape
        blend_pixels = max(const.CYLINDRICAL_BLEND_MIN_PIXELS, int(self.settings.edge_blend_width / self.settings.resolution))

        blend_mask = np.ones_like(thickness_map)

        for i in range(blend_pixels):
            factor = (i + 1) / blend_pixels
            if i < height:
                blend_mask[i, :] = np.minimum(blend_mask[i, :], factor)
                blend_mask[-(i+1), :] = np.minimum(blend_mask[-(i+1), :], factor)
            if i < width:
                blend_mask[:, i] = np.minimum(blend_mask[:, i], factor)
                blend_mask[:, -(i+1)] = np.minimum(blend_mask[:, -(i+1)], factor)

        blended = (thickness_map * blend_mask +
                  self.settings.min_thickness * (1 - blend_mask))

        return blended
