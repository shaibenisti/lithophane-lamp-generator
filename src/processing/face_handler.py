#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Face Detection and Enhancement for Lithophane Lamp Generator

Detects faces in images and applies special processing to ensure they're
visible in the final lithophane. Handles facial shadows and preserves features.
"""

import cv2
import numpy as np
import logging
from typing import List, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class FaceDetectionResult:
    """Results from face detection."""

    def __init__(self, has_faces: bool, face_count: int,
                 face_regions: List[Tuple[int, int, int, int]],
                 largest_face: Optional[Tuple[int, int, int, int]] = None):
        self.has_faces = has_faces
        self.face_count = face_count
        self.face_regions = face_regions  # List of (x, y, w, h) rectangles
        self.largest_face = largest_face  # (x, y, w, h) of largest face


class FaceHandler:
    """
    Face detection and enhancement for lithophane images.

    Uses OpenCV Haar Cascade for reliable face detection.
    Applies gentle enhancement to face regions to ensure visibility.
    """

    def __init__(self):
        """Initialize face handler with Haar Cascade classifier."""
        self.logger = logging.getLogger(__name__)
        self.cascade = self._load_cascade()

    def _load_cascade(self) -> Optional[cv2.CascadeClassifier]:
        """
        Load OpenCV Haar Cascade for face detection.

        Returns:
            CascadeClassifier or None if loading fails
        """
        try:
            # Try to load from OpenCV's data directory
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'

            if not Path(cascade_path).exists():
                self.logger.warning(f"Haar cascade not found at: {cascade_path}")
                return None

            cascade = cv2.CascadeClassifier(cascade_path)

            if cascade.empty():
                self.logger.warning("Haar cascade loaded but is empty")
                return None

            self.logger.info("Face detection cascade loaded successfully")
            return cascade

        except Exception as e:
            self.logger.warning(f"Could not load face detection cascade: {e}")
            return None

    def detect_faces(self, image: np.ndarray) -> FaceDetectionResult:
        """
        Detect faces in image.

        Args:
            image: Grayscale image (uint8)

        Returns:
            FaceDetectionResult object
        """
        # If cascade failed to load, return no faces
        if self.cascade is None:
            self.logger.warning("Face detection unavailable (cascade not loaded)")
            return FaceDetectionResult(False, 0, [])

        # Ensure grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Detect faces with balanced parameters
        # scaleFactor: 1.1 = slow but accurate
        # minNeighbors: 5 = balanced (fewer false positives)
        # minSize: 30x30 = ignore very small faces (noise)
        faces = self.cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        # Convert from numpy array to list of tuples
        face_regions = [(int(x), int(y), int(w), int(h)) for (x, y, w, h) in faces]
        face_count = len(face_regions)
        has_faces = face_count > 0

        # Find largest face (usually the main subject)
        largest_face = None
        if has_faces:
            largest_face = max(face_regions, key=lambda f: f[2] * f[3])  # Max area

        self.logger.info(f"Face detection: {face_count} face(s) found")

        return FaceDetectionResult(
            has_faces=has_faces,
            face_count=face_count,
            face_regions=face_regions,
            largest_face=largest_face
        )

    def enhance_face_regions(self, image: np.ndarray,
                            face_result: FaceDetectionResult) -> np.ndarray:
        """
        Apply gentle enhancement to face regions.

        Args:
            image: Grayscale image (uint8)
            face_result: Face detection results

        Returns:
            Image with enhanced faces (uint8)
        """
        if not face_result.has_faces:
            return image.copy()

        self.logger.info(f"Enhancing {face_result.face_count} face region(s)")

        # Work on a copy
        enhanced = image.copy()

        for (x, y, w, h) in face_result.face_regions:
            # Extract face region with some padding (20% on each side)
            pad_x = int(w * 0.2)
            pad_y = int(h * 0.2)

            x1 = max(0, x - pad_x)
            y1 = max(0, y - pad_y)
            x2 = min(image.shape[1], x + w + pad_x)
            y2 = min(image.shape[0], y + h + pad_y)

            face_roi = enhanced[y1:y2, x1:x2]

            if face_roi.size == 0:
                continue

            # Apply gentle CLAHE to face region only
            # This brings out facial features without over-processing
            # Using very large tiles (24x24) to avoid amplifying any skin texture
            clahe = cv2.createCLAHE(clipLimit=1.2, tileGridSize=(24, 24))
            face_enhanced = clahe.apply(face_roi)

            # Apply STRONG Gaussian blur to eliminate skin texture
            # Dramatically increased kernel size to remove all pores, wrinkles, and fine hair
            # This is critical for elderly faces with visible texture
            face_enhanced = cv2.GaussianBlur(face_enhanced, (15, 15), 0)

            # Apply morphological closing to further smooth texture
            # This removes any remaining high-frequency details
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            face_enhanced = cv2.morphologyEx(face_enhanced, cv2.MORPH_CLOSE, kernel)

            # Check if face is dark (shadows on face)
            face_brightness = float(np.mean(face_roi))

            if face_brightness < 90:
                # Face is dark, apply gentle brightening
                # Calculate how much to brighten
                target_brightness = 100
                brightness_boost = (target_brightness - face_brightness) * 0.4

                face_enhanced = np.clip(
                    face_enhanced.astype(np.float32) + brightness_boost,
                    0, 255
                ).astype(np.uint8)

                self.logger.info(f"Face brightened: +{brightness_boost:.1f} "
                               f"(was {face_brightness:.1f})")

            # Blend enhanced face back with smooth edges
            # Create a blend mask (stronger in center, fades to edges)
            mask = np.ones_like(face_roi, dtype=np.float32)
            fade_size = min(pad_x, pad_y)

            if fade_size > 0:
                # Create gradient fade at edges
                for i in range(fade_size):
                    alpha = i / fade_size
                    # Top
                    if i < mask.shape[0]:
                        mask[i, :] *= alpha
                    # Bottom
                    if mask.shape[0] - 1 - i >= 0:
                        mask[mask.shape[0] - 1 - i, :] *= alpha
                    # Left
                    if i < mask.shape[1]:
                        mask[:, i] *= alpha
                    # Right
                    if mask.shape[1] - 1 - i >= 0:
                        mask[:, mask.shape[1] - 1 - i] *= alpha

            # Blend
            blended = (face_enhanced * mask + face_roi * (1 - mask)).astype(np.uint8)
            enhanced[y1:y2, x1:x2] = blended

        self.logger.info("Face enhancement complete")
        return enhanced

    def is_portrait(self, image: np.ndarray, face_result: FaceDetectionResult) -> bool:
        """
        Determine if image is a portrait (face takes up significant portion).

        Args:
            image: Input image
            face_result: Face detection results

        Returns:
            True if this is a portrait image
        """
        if not face_result.has_faces or face_result.largest_face is None:
            return False

        # Calculate face area ratio
        image_area = image.shape[0] * image.shape[1]
        x, y, w, h = face_result.largest_face
        face_area = w * h
        face_ratio = face_area / image_area

        # If face is >10% of image, consider it a portrait
        is_portrait = face_ratio > 0.10

        if is_portrait:
            self.logger.info(f"Portrait detected (face ratio: {face_ratio*100:.1f}%)")
        else:
            self.logger.info(f"Not a portrait (face ratio: {face_ratio*100:.1f}%)")

        return is_portrait


def quick_face_enhance(image: np.ndarray) -> Tuple[np.ndarray, FaceDetectionResult]:
    """
    Quick one-line face detection and enhancement.

    Args:
        image: Grayscale image (uint8)

    Returns:
        Tuple of (enhanced_image, face_detection_result)
    """
    handler = FaceHandler()
    face_result = handler.detect_faces(image)
    enhanced = handler.enhance_face_regions(image, face_result)
    return enhanced, face_result
