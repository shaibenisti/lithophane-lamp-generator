#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple Thickness Mapper for Lithophane Lamp Generator

Converts grayscale images to thickness values for 3D printing.
The fundamental principle: Dark = thick (blocks light), Bright = thin (allows light).
"""

import cv2
import numpy as np
import logging
from ..core.settings import Settings

logger = logging.getLogger(__name__)


class ThicknessMapper:
    """
    Simple thickness mapper.

    Converts pixel brightness to wall thickness:
    - Black (0) → max_thickness (2.2mm) → blocks light → dark
    - White (255) → min_thickness (0.5mm) → allows light → bright
    - Gray → proportional thickness in between

    Optional gamma correction for tonal adjustment.
    """

    def __init__(self, settings: Settings):
        """
        Initialize thickness mapper.

        Args:
            settings: Application settings with thickness range
        """
        self.settings = settings
        self.logger = logging.getLogger(__name__)

        self.min_thickness = settings.min_thickness  # 0.5mm (bright)
        self.max_thickness = settings.max_thickness  # 2.2mm (dark)

        # Gamma for tonal adjustment (1.0 = linear, <1.0 = brighter, >1.0 = darker)
        self.gamma = 1.0 if settings.gamma_override is None else settings.gamma_override

    def create_thickness_map(self, image: np.ndarray) -> np.ndarray:
        """
        Convert grayscale image to thickness map.

        Args:
            image: Processed grayscale image (uint8)

        Returns:
            Thickness map in millimeters (float32)
        """
        self.logger.info(f"Creating thickness map: {image.shape[1]}×{image.shape[0]}")

        # Step 1: Normalize to 0-1 range
        normalized = image.astype(np.float32) / 255.0

        # Step 2: Apply gamma correction (adjust tonal curve)
        # gamma < 1.0 brightens (reduces thickness)
        # gamma > 1.0 darkens (increases thickness)
        if self.gamma != 1.0:
            gamma_corrected = np.power(normalized, self.gamma)
            self.logger.info(f"Applied gamma correction: {self.gamma}")
        else:
            gamma_corrected = normalized
            self.logger.info("No gamma correction (linear mapping)")

        # Step 3: Map to thickness range
        # Invert: bright pixels → thin walls, dark pixels → thick walls
        inverted = 1.0 - gamma_corrected
        thickness_range = self.max_thickness - self.min_thickness
        thickness_map = self.min_thickness + (inverted * thickness_range)

        # Step 4: Apply edge blending for wrap-around smoothness
        thickness_map = self._apply_edge_blending(thickness_map)

        self.logger.info(f"Thickness map created: {self.min_thickness:.1f}mm to {self.max_thickness:.1f}mm")
        return thickness_map.astype(np.float32)

    def _apply_edge_blending(self, thickness_map: np.ndarray) -> np.ndarray:
        """
        Blend left and right edges for smooth wrap-around on cylinder.

        Args:
            thickness_map: Raw thickness map

        Returns:
            Thickness map with blended edges
        """
        height, width = thickness_map.shape
        blend_width = int(self.settings.edge_blend_width)  # pixels (default 4)

        if blend_width <= 0 or blend_width >= width // 4:
            return thickness_map  # Skip if blend width invalid

        # Create blend mask (0 at edges, 1 in center)
        blend_mask = np.ones((height, width), dtype=np.float32)

        # Blend left edge
        for x in range(blend_width):
            blend_factor = x / blend_width
            blend_mask[:, x] = blend_factor

        # Blend right edge
        for x in range(blend_width):
            blend_mask[:, -(x + 1)] = x / blend_width

        # Calculate average thickness at edges for smooth transition
        left_edge = float(thickness_map[:, :blend_width].mean())
        right_edge = float(thickness_map[:, -blend_width:].mean())
        average_edge = (left_edge + right_edge) / 2

        # Apply blending
        blended = thickness_map * blend_mask + average_edge * (1 - blend_mask)

        self.logger.info(f"Applied edge blending: {blend_width}px")
        return blended

    def get_thickness_stats(self, thickness_map: np.ndarray) -> dict:
        """
        Get statistics about thickness map.

        Args:
            thickness_map: Thickness map array

        Returns:
            Dictionary with min, max, mean, std thickness values
        """
        return {
            'min_thickness': float(np.min(thickness_map)),
            'max_thickness': float(np.max(thickness_map)),
            'mean_thickness': float(np.mean(thickness_map)),
            'std_thickness': float(np.std(thickness_map)),
            'thickness_range': float(np.max(thickness_map) - np.min(thickness_map))
        }
