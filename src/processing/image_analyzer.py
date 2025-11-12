#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import numpy as np
import logging
from typing import Dict, Any, List, Tuple, Optional

from ..core import constants as const
from ..utils.image_utils import calculate_histogram_distribution
from .face_detector import get_face_detector

logger = logging.getLogger(__name__)


class ImageAnalyzer:

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Initialize advanced face detector (MediaPipe or Haar Cascade fallback)
        self._face_detector = get_face_detector()
        if self._face_detector.is_available():
            self.logger.info(f"Face detection available: {self._face_detector.get_method()}")
        else:
            self.logger.warning("Face detection not available")

    def _detect_faces(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces in image using advanced detection.

        Args:
            image: Grayscale or BGR image

        Returns:
            List of face bounding boxes as (x, y, width, height)
        """
        if not self._face_detector.is_available():
            return []

        try:
            faces = self._face_detector.detect_faces(image)
            if faces and len(faces) > 0:
                self.logger.info(f"Detected {len(faces)} face(s) using {self._face_detector.get_method()}")
            return faces

        except Exception as e:
            self.logger.warning(f"Face detection failed: {e}")
            return []

    def _classify_image_type(self, brightness: float, contrast: float,
                           shadows: float, highlights: float, has_faces: bool) -> str:
        if has_faces:
            return "portrait" if contrast > const.CONTRAST_LOW_THRESHOLD else "portrait_low_contrast"
        elif contrast < const.CONTRAST_LOW_THRESHOLD:
            return "low_contrast"
        elif brightness < const.BRIGHTNESS_UNDEREXPOSED_THRESHOLD:
            return "underexposed"
        elif brightness > const.BRIGHTNESS_OVEREXPOSED_THRESHOLD:
            return "overexposed"
        elif shadows > const.SHADOW_HEAVY_RATIO_THRESHOLD:
            return "shadow_heavy"
        elif highlights > const.HIGHLIGHT_HEAVY_RATIO_THRESHOLD:
            return "highlight_heavy"
        else:
            return "balanced"

    def analyze_image_characteristics(self, image: np.ndarray) -> Dict[str, Any]:
        mean_brightness = np.mean(image)
        std_deviation = np.std(image)

        shadows, midtones, highlights = calculate_histogram_distribution(image)

        edges = cv2.Canny(image, const.CANNY_THRESHOLD_LOW, const.CANNY_THRESHOLD_HIGH)
        edge_density = np.sum(edges > 0) / edges.size

        faces = self._detect_faces(image)
        has_faces = len(faces) > 0

        problems = self._detect_problematic_areas(image, faces)

        image_type = self._classify_image_type(
            mean_brightness, std_deviation, shadows, highlights, has_faces
        )

        characteristics = {
            'mean_brightness': mean_brightness,
            'contrast_level': std_deviation,
            'shadow_ratio': shadows,
            'highlight_ratio': highlights,
            'edge_density': edge_density,
            'has_faces': has_faces,
            'face_count': len(faces),
            'faces': faces,
            'problems': problems,
            'image_type': image_type
        }

        self.logger.info(
            f"Image analysis: {image_type}, brightness={mean_brightness:.1f}, "
            f"contrast={std_deviation:.1f}, faces={'yes' if has_faces else 'no'}"
        )

        return characteristics

    def _detect_problematic_areas(self, image: np.ndarray,
                                faces: List[Tuple[int, int, int, int]]) -> Dict[str, Any]:
        problems = {
            'dark_accessories': [],
            'bright_spots': [],
            'text_areas': [],
            'low_detail_areas': [],
            'extreme_contrast_areas': [],
            'needs_special_processing': False
        }

        very_dark_mask = image < 20
        if np.sum(very_dark_mask) > (image.size * 0.02):
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (10, 10))
            dark_regions = cv2.morphologyEx(very_dark_mask.astype(np.uint8), cv2.MORPH_CLOSE, kernel)

            contours, _ = cv2.findContours(dark_regions, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 500:
                    x, y, w, h = cv2.boundingRect(contour)
                    problems['dark_accessories'].append((x, y, w, h))

        very_bright_mask = image > 245
        if np.sum(very_bright_mask) > (image.size * 0.05):
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (8, 8))
            bright_regions = cv2.morphologyEx(very_bright_mask.astype(np.uint8), cv2.MORPH_CLOSE, kernel)

            contours, _ = cv2.findContours(bright_regions, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 300:
                    x, y, w, h = cv2.boundingRect(contour)
                    problems['bright_spots'].append((x, y, w, h))

        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 1))
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 20))

        horizontal_lines = cv2.morphologyEx(image, cv2.MORPH_OPEN, horizontal_kernel)
        vertical_lines = cv2.morphologyEx(image, cv2.MORPH_OPEN, vertical_kernel)
        text_mask = cv2.add(horizontal_lines, vertical_lines)

        if np.sum(text_mask > 0) > (image.size * 0.02):
            contours, _ = cv2.findContours(text_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 200:
                    x, y, w, h = cv2.boundingRect(contour)
                    problems['text_areas'].append((x, y, w, h))

        problems['needs_special_processing'] = (
            len(problems['dark_accessories']) > 1 or
            len(problems['bright_spots']) > 3 or
            len(problems['text_areas']) > 2
        )

        return problems
