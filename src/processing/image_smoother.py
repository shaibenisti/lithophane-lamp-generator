#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import numpy as np
import logging
from typing import Dict, Any

from ..core import constants as const

logger = logging.getLogger(__name__)


class ImageSmoother:

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def apply_lithophane_smoothing(self, image: np.ndarray,
                                   characteristics: Dict[str, Any]) -> np.ndarray:
        image_type = characteristics['image_type']
        has_faces = characteristics.get('has_faces', False)

        if has_faces or image_type in ["portrait", "portrait_low_contrast"]:
            self.logger.info("Applying HEAVY portrait smoothing for lithophane (noise reduction)")

            smoothed = cv2.bilateralFilter(image, d=const.LITHO_PORTRAIT_BILATERAL_D_1,
                                          sigmaColor=const.LITHO_PORTRAIT_BILATERAL_SIGMA_COLOR_1,
                                          sigmaSpace=const.LITHO_PORTRAIT_BILATERAL_SIGMA_SPACE_1)

            smoothed = cv2.bilateralFilter(smoothed, d=const.LITHO_PORTRAIT_BILATERAL_D_2,
                                          sigmaColor=const.LITHO_PORTRAIT_BILATERAL_SIGMA_COLOR_2,
                                          sigmaSpace=const.LITHO_PORTRAIT_BILATERAL_SIGMA_SPACE_2)

            smoothed = cv2.bilateralFilter(smoothed, d=const.LITHO_PORTRAIT_BILATERAL_D_3,
                                          sigmaColor=const.LITHO_PORTRAIT_BILATERAL_SIGMA_COLOR_3,
                                          sigmaSpace=const.LITHO_PORTRAIT_BILATERAL_SIGMA_SPACE_3)

            smoothed = cv2.GaussianBlur(smoothed, const.LITHO_PORTRAIT_GAUSSIAN_KERNEL,
                                       const.LITHO_PORTRAIT_GAUSSIAN_SIGMA)

            result = (smoothed * const.LITHO_PORTRAIT_BLEND_SMOOTH +
                     image.astype(np.float32) * const.LITHO_PORTRAIT_BLEND_ORIGINAL).astype(np.uint8)

        else:
            self.logger.info("Applying strong smoothing for lithophane")

            smoothed = cv2.bilateralFilter(image, d=const.LITHO_GENERAL_BILATERAL_D_1,
                                          sigmaColor=const.LITHO_GENERAL_BILATERAL_SIGMA_COLOR_1,
                                          sigmaSpace=const.LITHO_GENERAL_BILATERAL_SIGMA_SPACE_1)

            smoothed = cv2.bilateralFilter(smoothed, d=const.LITHO_GENERAL_BILATERAL_D_2,
                                          sigmaColor=const.LITHO_GENERAL_BILATERAL_SIGMA_COLOR_2,
                                          sigmaSpace=const.LITHO_GENERAL_BILATERAL_SIGMA_SPACE_2)

            smoothed = cv2.GaussianBlur(smoothed, const.LITHO_GENERAL_GAUSSIAN_KERNEL,
                                       const.LITHO_GENERAL_GAUSSIAN_SIGMA)

            result = (smoothed * const.LITHO_GENERAL_BLEND_SMOOTH +
                     image.astype(np.float32) * const.LITHO_GENERAL_BLEND_ORIGINAL).astype(np.uint8)

        self.logger.info(f"Heavy lithophane smoothing applied (type: {image_type}, faces: {has_faces})")
        return result
