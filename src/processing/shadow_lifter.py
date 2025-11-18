#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Shadow Lifter for Lithophane Lamp Generator

Intelligently lifts shadows in images to prevent overly thick lithophane areas.
Preserves natural tonal range while ensuring shadow details are visible.
"""

import cv2
import numpy as np
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class ShadowAnalysis:
    """Results from shadow analysis."""

    def __init__(self, has_heavy_shadows: bool, shadow_ratio: float,
                 mean_brightness: float, shadow_mask: Optional[np.ndarray] = None):
        self.has_heavy_shadows = has_heavy_shadows
        self.shadow_ratio = shadow_ratio  # 0.0 to 1.0
        self.mean_brightness = mean_brightness  # 0 to 255
        self.shadow_mask = shadow_mask  # Binary mask of shadow areas


class ShadowLifter:
    """
    Intelligent shadow lifting for lithophane images.

    Detects and lifts shadow areas without over-brightening the entire image.
    Uses local tone mapping to preserve contrast while making shadows visible.
    """

    # Shadow detection thresholds
    SHADOW_THRESHOLD = 60  # Pixels below this are considered shadows
    HEAVY_SHADOW_RATIO = 0.25  # If >25% of image is shadows, needs fixing

    # Shadow lift parameters
    SHADOW_LIFT_STRENGTH = 40  # How much to lift shadows (0-100)
    SHADOW_BLEND_SIGMA = 50  # Smoothness of shadow boundary blending

    def __init__(self, shadow_threshold: int = SHADOW_THRESHOLD,
                 lift_strength: int = SHADOW_LIFT_STRENGTH):
        """
        Initialize shadow lifter.

        Args:
            shadow_threshold: Pixel value below which is considered shadow (0-255)
            lift_strength: How aggressively to lift shadows (0-100)
        """
        self.shadow_threshold = shadow_threshold
        self.lift_strength = lift_strength
        self.logger = logging.getLogger(__name__)

    def analyze_shadows(self, image: np.ndarray) -> ShadowAnalysis:
        """
        Analyze image for shadow content.

        Args:
            image: Grayscale image (uint8)

        Returns:
            ShadowAnalysis object with shadow information
        """
        # Ensure grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Calculate mean brightness
        mean_brightness = float(np.mean(gray))

        # Create shadow mask (pixels below threshold)
        shadow_mask = gray < self.shadow_threshold
        shadow_ratio = float(np.sum(shadow_mask)) / gray.size

        # Determine if shadows are heavy enough to need correction
        has_heavy_shadows = shadow_ratio > self.HEAVY_SHADOW_RATIO

        self.logger.info(f"Shadow analysis: {shadow_ratio*100:.1f}% shadows, "
                        f"mean brightness: {mean_brightness:.1f}")

        return ShadowAnalysis(
            has_heavy_shadows=has_heavy_shadows,
            shadow_ratio=shadow_ratio,
            mean_brightness=mean_brightness,
            shadow_mask=shadow_mask
        )

    def lift_shadows(self, image: np.ndarray, analysis: Optional[ShadowAnalysis] = None) -> np.ndarray:
        """
        Lift shadows in image using local tone mapping.

        Args:
            image: Grayscale image (uint8)
            analysis: Optional pre-computed shadow analysis

        Returns:
            Image with lifted shadows (uint8)
        """
        # Ensure grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Analyze if not provided
        if analysis is None:
            analysis = self.analyze_shadows(gray)

        # Skip if no heavy shadows
        if not analysis.has_heavy_shadows:
            self.logger.info("No heavy shadows detected, skipping shadow lift")
            return gray

        self.logger.info(f"Lifting shadows (strength: {self.lift_strength})")

        # Method: Adaptive histogram equalization on shadow areas only
        # Step 1: Create a soft shadow mask (0-1 float)
        shadow_mask_float = analysis.shadow_mask.astype(np.float32)

        # Blur the mask for smooth transitions
        shadow_mask_blurred = cv2.GaussianBlur(shadow_mask_float, (0, 0),
                                                sigmaX=self.SHADOW_BLEND_SIGMA)

        # Step 2: Calculate shadow lift map
        # Lift amount is proportional to how dark the pixel is
        darkness = (self.shadow_threshold - gray.astype(np.float32)).clip(0, self.shadow_threshold)
        lift_amount = (darkness / self.shadow_threshold) * self.lift_strength

        # Apply mask to only lift in shadow regions
        lift_amount_masked = lift_amount * shadow_mask_blurred

        # Step 3: Apply the lift
        lifted = gray.astype(np.float32) + lift_amount_masked
        lifted = np.clip(lifted, 0, 255).astype(np.uint8)

        # Calculate how much we improved
        improvement = float(np.mean(lifted)) - float(np.mean(gray))
        self.logger.info(f"Shadows lifted: +{improvement:.1f} brightness")

        return lifted

    def process_with_face_preservation(self, image: np.ndarray,
                                       face_regions: list) -> np.ndarray:
        """
        Lift shadows while giving extra attention to face regions.

        Args:
            image: Grayscale image (uint8)
            face_regions: List of (x, y, w, h) face rectangles

        Returns:
            Image with lifted shadows, faces enhanced (uint8)
        """
        # First, lift shadows globally
        lifted = self.lift_shadows(image)

        # Then, give extra lift to face regions if they're still dark
        if face_regions:
            self.logger.info(f"Applying extra shadow lift to {len(face_regions)} face(s)")

            for (x, y, w, h) in face_regions:
                # Extract face region
                face_roi = lifted[y:y+h, x:x+w]

                # Check if face is still dark
                face_brightness = float(np.mean(face_roi))

                if face_brightness < 100:  # Face is still too dark
                    # Apply gentle additional lift
                    extra_lift = (100 - face_brightness) * 0.3  # Gentle boost
                    face_roi_lifted = np.clip(face_roi.astype(np.float32) + extra_lift,
                                             0, 255).astype(np.uint8)

                    # Blend back smoothly
                    lifted[y:y+h, x:x+w] = face_roi_lifted
                    self.logger.info(f"Applied extra face lift: +{extra_lift:.1f}")

        return lifted


def quick_shadow_lift(image: np.ndarray, strength: int = 40) -> np.ndarray:
    """
    Quick one-line shadow lifting function.

    Args:
        image: Grayscale image (uint8)
        strength: Lift strength (0-100)

    Returns:
        Image with lifted shadows
    """
    lifter = ShadowLifter(lift_strength=strength)
    return lifter.lift_shadows(image)
