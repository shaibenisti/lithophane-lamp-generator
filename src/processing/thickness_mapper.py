#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import numpy as np
import logging
from typing import Dict, Any

from ..core.settings import Settings
from ..core import constants as const

logger = logging.getLogger(__name__)


class ThicknessMapper:

    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)

    def create_thickness_map(self, processed_image: np.ndarray,
                            characteristics: Dict[str, Any], smoothed_image: np.ndarray) -> np.ndarray:
        # Apply face-aware processing if faces detected
        if characteristics.get('has_faces', False) and len(characteristics.get('faces', [])) > 0:
            self.logger.info("Applying face-priority thickness mapping")
            return self._create_face_priority_thickness_map(smoothed_image, characteristics)
        else:
            # Original processing for non-portrait images
            return self._create_standard_thickness_map(smoothed_image, characteristics)

    def _create_standard_thickness_map(self, image: np.ndarray,
                                      characteristics: Dict[str, Any]) -> np.ndarray:
        """Original thickness mapping for non-portrait images."""
        normalized_image = self._adaptive_histogram_normalization(image, characteristics)

        normalized = normalized_image.astype(np.float64) / 255.0

        gamma = self.settings.get_gamma_value(characteristics['image_type'])
        gamma_corrected = np.power(normalized, gamma)

        thickness_range = self.settings.max_thickness - self.settings.min_thickness
        base_thickness = self.settings.min_thickness + (gamma_corrected * thickness_range)

        blended_thickness = self._apply_cylindrical_blending(base_thickness)

        return blended_thickness

    def _create_face_priority_thickness_map(self, image: np.ndarray,
                                           characteristics: Dict[str, Any]) -> np.ndarray:
        """
        Face-priority thickness mapping.

        Strategy:
        1. Create priority mask (1.0 for faces, <1.0 for background)
        2. Apply face-region histogram stretching
        3. Compress non-face regions to narrower thickness range
        4. Result: Faces "pop" with full detail, uniform/background fades
        """
        faces = characteristics['faces']
        img_height, img_width = image.shape[:2]

        # Step 1: Create face priority mask
        priority_mask = self._create_face_priority_mask(img_height, img_width, faces)

        # Step 2: Face-aware histogram normalization
        face_normalized = self._face_aware_histogram_normalization(image, faces, priority_mask)

        # Step 3: Apply gamma correction
        normalized = face_normalized.astype(np.float64) / 255.0
        gamma = self.settings.get_gamma_value(characteristics['image_type'])
        gamma_corrected = np.power(normalized, gamma)

        # Step 4: Create base thickness with full range
        thickness_range = self.settings.max_thickness - self.settings.min_thickness
        base_thickness = self.settings.min_thickness + (gamma_corrected * thickness_range)

        # Step 5: Apply priority-weighted compression
        # Face regions keep full range, non-face regions get compressed
        mean_thickness = (self.settings.max_thickness + self.settings.min_thickness) / 2
        compressed_thickness = mean_thickness + (base_thickness - mean_thickness) * priority_mask

        # Step 6: Apply cylindrical blending
        blended_thickness = self._apply_cylindrical_blending(compressed_thickness)

        self.logger.info(f"Face-priority mapping applied for {len(faces)} face(s)")
        return blended_thickness

    def _create_face_priority_mask(self, height: int, width: int,
                                   faces: list) -> np.ndarray:
        """
        Create a priority mask where:
        - Face regions: 1.0 (full detail)
        - Near face: 0.6-0.9 (moderate detail with smooth falloff)
        - Far from face: 0.2-0.4 (heavily suppressed)
        """
        # Start with low priority everywhere
        mask = np.full((height, width), 0.25, dtype=np.float32)

        for (fx, fy, fw, fh) in faces:
            # Calculate face center and size
            face_center_x = fx + fw // 2
            face_center_y = fy + fh // 2
            face_size = max(fw, fh)

            # Create coordinate grids
            y_coords, x_coords = np.ogrid[:height, :width]

            # Calculate distance from face center
            dist_from_face = np.sqrt(
                ((x_coords - face_center_x) / face_size) ** 2 +
                ((y_coords - face_center_y) / face_size) ** 2
            )

            # Create smooth falloff mask
            # 0.0-0.7 distance: priority 1.0 (face region)
            # 0.7-1.5 distance: priority 1.0 -> 0.5 (smooth falloff)
            # 1.5-3.0 distance: priority 0.5 -> 0.3 (body/near region)
            # 3.0+ distance: priority 0.25 (background)

            face_priority = np.ones((height, width), dtype=np.float32)

            # Core face region
            core_mask = dist_from_face < 0.7
            face_priority[core_mask] = 1.0

            # Smooth falloff around face
            falloff_mask = (dist_from_face >= 0.7) & (dist_from_face < 1.5)
            falloff_factor = (1.5 - dist_from_face[falloff_mask]) / 0.8
            face_priority[falloff_mask] = 0.5 + 0.5 * falloff_factor

            # Body region
            body_mask = (dist_from_face >= 1.5) & (dist_from_face < 3.0)
            body_factor = (3.0 - dist_from_face[body_mask]) / 1.5
            face_priority[body_mask] = 0.3 + 0.2 * body_factor

            # Background
            bg_mask = dist_from_face >= 3.0
            face_priority[bg_mask] = 0.25

            # Take maximum priority across all faces
            mask = np.maximum(mask, face_priority)

        # Smooth the mask to avoid hard transitions
        mask = cv2.GaussianBlur(mask, (51, 51), 15)

        return mask

    def _face_aware_histogram_normalization(self, image: np.ndarray, faces: list,
                                           priority_mask: np.ndarray) -> np.ndarray:
        """
        Normalize histogram with face-region priority.

        Strategy:
        - Calculate histogram percentiles ONLY from face regions
        - Stretch face tonal range to use full 0-255
        - Non-face regions follow along but get compressed
        """
        # Create binary face mask
        face_mask = priority_mask > 0.7

        if np.sum(face_mask) > 100:  # If we have enough face pixels
            # Calculate histogram only for face region
            face_pixels = image[face_mask]
            hist = cv2.calcHist([face_pixels.astype(np.uint8)], [0], None, [256], [0, 256])
            cumsum = np.cumsum(hist)
            cumsum_normalized = cumsum / cumsum[-1]

            # Find face region's tonal range
            p2 = np.searchsorted(cumsum_normalized, 0.02)
            p98 = np.searchsorted(cumsum_normalized, 0.98)

            current_range = p98 - p2

            self.logger.info(f"Face region tonal range: {p2}-{p98} (span: {current_range})")

            # If face region has limited tonal range, stretch it
            if current_range < 180:
                img_float = image.astype(np.float64)

                # Clip to face region range
                img_clipped = np.clip(img_float, p2, p98)

                # Stretch to full range
                if p98 > p2:
                    normalized = ((img_clipped - p2) / (p98 - p2)) * 235 + 10
                else:
                    normalized = img_float

                # Blend with original based on priority mask
                # High priority areas (face) get more of the normalized version
                blended = (normalized * priority_mask + img_float * (1 - priority_mask * 0.7))

                return np.clip(blended, 0, 255).astype(np.uint8)

        # Fallback to standard normalization
        return self._adaptive_histogram_normalization(image, {'image_type': 'portrait'})

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
