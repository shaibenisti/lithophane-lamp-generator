#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Lithophane Optimizer - Single-pass image optimization for lithophane quality.

This module replaces the complex multi-stage enhancement pipeline with a simple,
focused approach optimized specifically for lithophane visibility (backlit appearance)
rather than photo quality.

Key principles:
- NO smoothing (preserves facial features)
- Face-aware processing (different treatment for faces vs background)
- Single enhancement pass (no fighting layers)
- Edge preservation (critical for feature visibility)
- Lithophane-first optimization
"""

import cv2
import numpy as np
import logging
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger(__name__)


class LithophaneOptimizer:
    """
    Optimizes images specifically for lithophane quality.

    Replaces the old enhancement + smoothing pipeline with a clean single-pass
    approach that preserves facial details while preparing the image for
    thickness mapping.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def optimize(self, image: np.ndarray,
                 characteristics: Dict[str, Any],
                 target_size: Tuple[int, int]) -> np.ndarray:
        """
        Main optimization entry point.

        Args:
            image: Input grayscale image (uint8 or float64)
            characteristics: Image analysis results (from ImageAnalyzer)
            target_size: (width, height) for final lithophane

        Returns:
            Optimized image ready for thickness mapping
        """
        # Ensure float64 for processing
        if image.dtype != np.float64:
            image = image.astype(np.float64)

        has_faces = characteristics.get('has_faces', False)
        faces = characteristics.get('faces', [])

        if has_faces and len(faces) > 0:
            self.logger.info("Applying portrait-optimized processing")
            optimized = self._optimize_portrait(image, faces, target_size)
        else:
            self.logger.info("Applying general image optimization")
            optimized = self._optimize_general(image, target_size)

        return np.clip(optimized, 0, 255).astype(np.uint8)

    def _optimize_portrait(self, image: np.ndarray,
                          faces: List[Tuple[int, int, int, int]],
                          target_size: Tuple[int, int]) -> np.ndarray:
        """
        Portrait-specific optimization pipeline.

        Steps:
        1. Aggressive face contrast boost (make features distinct)
        2. Face tonal range stretch (use full 0-255)
        3. Resize to target dimensions
        4. Light edge sharpening (preserve features)

        NO smoothing - smoothing destroys the details we just enhanced!
        """
        enhanced = image.copy()

        # Step 1: Boost face contrast aggressively
        enhanced = self._boost_face_contrast(enhanced, faces)

        # Step 2: Stretch face tonal range
        enhanced = self._stretch_face_range(enhanced, faces)

        # Step 3: Resize with detail preservation
        resized = self._resize_preserve_detail(enhanced, target_size)

        # Step 4: Light sharpening for edge clarity
        sharpened = self._sharpen_edges(resized)

        self.logger.info("Portrait optimization complete")
        return sharpened

    def _optimize_general(self, image: np.ndarray,
                         target_size: Tuple[int, int]) -> np.ndarray:
        """
        General image optimization (no faces).

        Steps:
        1. Histogram normalization
        2. Resize
        3. Light sharpen
        """
        # Normalize histogram
        normalized = self._normalize_histogram(image)

        # Resize
        resized = self._resize_preserve_detail(normalized, target_size)

        # Light sharpen
        sharpened = self._sharpen_edges(resized)

        self.logger.info("General optimization complete")
        return sharpened

    def _boost_face_contrast(self, image: np.ndarray,
                            faces: List[Tuple[int, int, int, int]]) -> np.ndarray:
        """
        Aggressively boost contrast in face regions.

        This is CRITICAL for lithophanes - facial features need strong local
        contrast to be visible when backlit. We use small CLAHE tiles to
        enhance fine details like eyes, nose, mouth.
        """
        enhanced = image.copy()

        for (x, y, w, h) in faces:
            # Extract face region with small padding
            padding = int(min(w, h) * 0.05)
            x1 = max(0, x - padding)
            y1 = max(0, y - padding)
            x2 = min(image.shape[1], x + w + padding)
            y2 = min(image.shape[0], y + h + padding)

            face_roi = enhanced[y1:y2, x1:x2].copy()

            # Aggressive local CLAHE with SMALL tiles for fine detail
            # Small tiles (4x4) = captures eyes, nose, mouth separately
            # ClipLimit=3.5 = strong but not over-processed
            clahe = cv2.createCLAHE(clipLimit=3.5, tileGridSize=(4, 4))
            face_boosted = clahe.apply(face_roi.astype(np.uint8))

            # Additional unsharp mask for edge definition
            # This makes eyes/eyebrows/nose/mouth edges crisp
            gaussian = cv2.GaussianBlur(face_boosted, (0, 0), 1.5)
            face_sharpened = cv2.addWeighted(face_boosted, 1.6, gaussian, -0.6, 0)

            # Put enhanced face back
            enhanced[y1:y2, x1:x2] = np.clip(face_sharpened, 0, 255)

            face_contrast_before = np.std(face_roi)
            face_contrast_after = np.std(face_sharpened)
            self.logger.info(f"Face contrast: {face_contrast_before:.1f} → {face_contrast_after:.1f}")

        return enhanced

    def _stretch_face_range(self, image: np.ndarray,
                           faces: List[Tuple[int, int, int, int]]) -> np.ndarray:
        """
        Stretch tonal range specifically in face regions.

        If face has limited tonal range (e.g., mid-tones only), stretch it
        to use more of 0-255 range for better thickness variation in lithophane.
        """
        enhanced = image.copy()

        for (x, y, w, h) in faces:
            face_roi = enhanced[y:y+h, x:x+w].copy()

            # Check face tonal range
            face_min = np.percentile(face_roi, 2)
            face_max = np.percentile(face_roi, 98)
            face_range = face_max - face_min

            # If limited range, stretch it
            if face_range < 120:
                self.logger.info(f"Stretching limited face range: {face_min:.0f}-{face_max:.0f}")

                # Stretch to use 20-220 range (avoid extreme blacks/whites)
                if face_max > face_min:
                    stretched = ((face_roi - face_min) / (face_max - face_min)) * 200 + 20
                    enhanced[y:y+h, x:x+w] = np.clip(stretched, 0, 255)

                    self.logger.info(f"Face range stretched to: {np.min(stretched):.0f}-{np.max(stretched):.0f}")

        return enhanced

    def _normalize_histogram(self, image: np.ndarray) -> np.ndarray:
        """
        Simple histogram normalization for general images.
        """
        img_uint8 = image.astype(np.uint8)

        # Calculate percentiles
        p2 = np.percentile(img_uint8, 2)
        p98 = np.percentile(img_uint8, 98)

        # Stretch to use 10-245 range
        if p98 > p2:
            normalized = ((image - p2) / (p98 - p2)) * 235 + 10
            return np.clip(normalized, 0, 255)

        return image

    def _resize_preserve_detail(self, image: np.ndarray,
                                target_size: Tuple[int, int]) -> np.ndarray:
        """
        Resize while preserving fine details.

        Uses Lanczos interpolation for high quality.
        """
        width, height = target_size

        img_uint8 = image.astype(np.uint8)

        # Use Lanczos for best quality
        resized = cv2.resize(img_uint8, (width, height),
                            interpolation=cv2.INTER_LANCZOS4)

        self.logger.info(f"Resized to {width}×{height} with detail preservation")
        return resized.astype(np.float64)

    def _sharpen_edges(self, image: np.ndarray) -> np.ndarray:
        """
        Light edge sharpening to preserve facial features.

        This is LIGHT sharpening - just enough to keep edges crisp,
        not aggressive enough to create halos or artifacts.
        """
        img_uint8 = image.astype(np.uint8)

        # Light unsharp mask
        # radius=1.2 = subtle
        # amount=0.4 = light strengthening
        gaussian = cv2.GaussianBlur(img_uint8, (0, 0), 1.2)
        sharpened = cv2.addWeighted(img_uint8, 1.4, gaussian, -0.4, 0)

        self.logger.info("Applied light edge sharpening")
        return np.clip(sharpened, 0, 255).astype(np.float64)


# Convenience function for easy integration
def optimize_for_lithophane(image: np.ndarray,
                           characteristics: Dict[str, Any],
                           target_size: Tuple[int, int]) -> np.ndarray:
    """
    Convenience function to optimize image for lithophane.

    Args:
        image: Input grayscale image
        characteristics: Analysis results from ImageAnalyzer
        target_size: (width, height) for final lithophane

    Returns:
        Optimized image ready for thickness mapping
    """
    optimizer = LithophaneOptimizer()
    return optimizer.optimize(image, characteristics, target_size)
