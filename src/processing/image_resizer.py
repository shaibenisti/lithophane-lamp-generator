#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import numpy as np
import logging
from typing import Dict, Any

from ..core import constants as const

logger = logging.getLogger(__name__)


class ImageResizer:

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def premium_resize(self, image: np.ndarray, target_width: int, target_height: int,
                      skip_sharpen: bool = False) -> np.ndarray:
        current_height, current_width = image.shape
        max_current = max(current_width, current_height)
        max_target = max(target_width, target_height)

        if max_current > max_target * const.RESIZE_VERY_LARGE_FACTOR:
            scale1 = max_target * const.RESIZE_STAGE1_SCALE_FACTOR / max_current
            temp1 = cv2.resize(image, None, fx=scale1, fy=scale1, interpolation=cv2.INTER_CUBIC)

            scale2 = max_target * const.RESIZE_STAGE2_SCALE_FACTOR / max(temp1.shape[1], temp1.shape[0])
            temp2 = cv2.resize(temp1, None, fx=scale2, fy=scale2, interpolation=cv2.INTER_LANCZOS4)

            final = cv2.resize(temp2, (target_width, target_height), interpolation=cv2.INTER_LANCZOS4)

        elif max_current > max_target * const.RESIZE_MEDIUM_FACTOR:
            intermediate_scale = max_target * const.RESIZE_STAGE3_SCALE_FACTOR / max_current
            temp = cv2.resize(image, None, fx=intermediate_scale, fy=intermediate_scale,
                             interpolation=cv2.INTER_CUBIC)
            final = cv2.resize(temp, (target_width, target_height), interpolation=cv2.INTER_LANCZOS4)

        else:
            final = cv2.resize(image, (target_width, target_height), interpolation=cv2.INTER_LANCZOS4)

        if skip_sharpen:
            return final.astype(np.uint8)

        kernel = np.array([[const.RESIZE_SHARPEN_KERNEL_EDGE, const.RESIZE_SHARPEN_KERNEL_EDGE, const.RESIZE_SHARPEN_KERNEL_EDGE],
                          [const.RESIZE_SHARPEN_KERNEL_EDGE, const.RESIZE_SHARPEN_KERNEL_CENTER, const.RESIZE_SHARPEN_KERNEL_EDGE],
                          [const.RESIZE_SHARPEN_KERNEL_EDGE, const.RESIZE_SHARPEN_KERNEL_EDGE, const.RESIZE_SHARPEN_KERNEL_EDGE]])
        sharpened = cv2.filter2D(final.astype(np.float32), -1, kernel)
        final = np.clip(final.astype(np.float32) * const.RESIZE_SHARPEN_ORIGINAL_WEIGHT +
                       sharpened * const.RESIZE_SHARPEN_ENHANCED_WEIGHT, 0, 255).astype(np.uint8)

        return final

    def fix_problematic_areas(self, image: np.ndarray, problems: Dict[str, Any]) -> np.ndarray:
        fixed_image = image.copy()

        for x, y, w, h in problems['dark_accessories']:
            roi = fixed_image[y:y+h, x:x+w]
            very_dark_mask = roi < 25

            if np.sum(very_dark_mask) > 0:
                surrounding_area = self._get_surrounding_area(fixed_image, x, y, w, h, margin=15)
                if surrounding_area.size > 0:
                    replacement_value = np.mean(surrounding_area[surrounding_area > 50])
                    roi[very_dark_mask] = roi[very_dark_mask] * 0.8 + replacement_value * 0.2

            fixed_image[y:y+h, x:x+w] = roi

        for x, y, w, h in problems['bright_spots']:
            roi = fixed_image[y:y+h, x:x+w]
            very_bright_mask = roi > 240

            if np.sum(very_bright_mask) > 0:
                roi[very_bright_mask] = 240 + (roi[very_bright_mask] - 240) * 0.6

            fixed_image[y:y+h, x:x+w] = roi

        large_text_areas = [(x, y, w, h) for x, y, w, h in problems['text_areas'] if w * h > 1000]
        for x, y, w, h in large_text_areas:
            roi = fixed_image[y:y+h, x:x+w].astype(np.uint8)

            text_mask = np.zeros(roi.shape, dtype=np.uint8)
            text_mask[roi < np.mean(roi) - 1.5 * np.std(roi)] = 255

            if np.sum(text_mask) > 100:
                inpainted = cv2.inpaint(roi, text_mask, 2, cv2.INPAINT_TELEA)
                fixed_image[y:y+h, x:x+w] = roi.astype(np.float64) * 0.7 + inpainted.astype(np.float64) * 0.3

        return np.clip(fixed_image, 0, 255)

    def _get_surrounding_area(self, image: np.ndarray, x: int, y: int, w: int, h: int,
                            margin: int = 15) -> np.ndarray:
        img_h, img_w = image.shape

        x1 = max(0, x - margin)
        y1 = max(0, y - margin)
        x2 = min(img_w, x + w + margin)
        y2 = min(img_h, y + h + margin)

        surrounding = image[y1:y2, x1:x2].copy()

        inner_x1 = max(0, x - x1)
        inner_y1 = max(0, y - y1)
        inner_x2 = min(surrounding.shape[1], inner_x1 + w)
        inner_y2 = min(surrounding.shape[0], inner_y1 + h)

        mask = np.ones(surrounding.shape, dtype=bool)
        mask[inner_y1:inner_y2, inner_x1:inner_x2] = False

        return surrounding[mask]
