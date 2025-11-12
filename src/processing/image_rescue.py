#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Image Rescue System for Lithophane Lamp Generator
Automatically detects and fixes problematic images (low-res, dark, compressed, etc.)
"""

import cv2
import numpy as np
import logging
from typing import Dict, Any, Tuple, Optional
from enum import Enum

from .ai_upscaler import get_ai_upscaler

logger = logging.getLogger(__name__)


class ImageQualityTier(Enum):
    """Image quality classification for business decisions."""
    EXCELLENT = "excellent"      # 2000+ px, perfect for lithophane
    GOOD = "good"                # 1200-2000px, minor enhancement
    ACCEPTABLE = "acceptable"    # 800-1200px, needs upscaling
    POOR = "poor"                # 400-800px, heavy AI processing needed
    VERY_POOR = "very_poor"      # 200-400px, warn customer
    UNUSABLE = "unusable"        # <200px, reject


class DarknessLevel(Enum):
    """Image darkness classification."""
    NORMAL = "normal"            # 80-180 brightness
    SLIGHTLY_DARK = "slightly_dark"  # 50-80 brightness
    DARK = "dark"                # 30-50 brightness
    VERY_DARK = "very_dark"      # 10-30 brightness
    EXTREMELY_DARK = "extremely_dark"  # <10 brightness


class ImageRescueSystem:
    """
    Intelligent image rescue system that detects and fixes common problems.

    Handles:
    - Low resolution (upscaling)
    - Dark images (brightness correction)
    - Low contrast (histogram stretching)
    - Compression artifacts (denoising)
    """

    # Resolution thresholds (based on minimum dimension)
    RESOLUTION_EXCELLENT = 2000
    RESOLUTION_GOOD = 1200
    RESOLUTION_ACCEPTABLE = 800
    RESOLUTION_POOR = 400
    RESOLUTION_VERY_POOR = 200

    # Darkness thresholds
    BRIGHTNESS_NORMAL_MIN = 80
    BRIGHTNESS_NORMAL_MAX = 180
    BRIGHTNESS_SLIGHTLY_DARK = 50
    BRIGHTNESS_DARK = 30
    BRIGHTNESS_VERY_DARK = 10

    def __init__(self):
        """Initialize rescue system."""
        self.logger = logging.getLogger(__name__)

        # Initialize AI upscaler for high quality upscaling
        self.ai_upscaler = get_ai_upscaler()
        if self.ai_upscaler.is_available():
            self.logger.info(f"AI upscaling available on {self.ai_upscaler.get_device().upper()}")
        else:
            self.logger.info("AI upscaling not available, using traditional methods")

    def analyze_and_rescue(self, image: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Analyze image for problems and automatically fix them.

        Args:
            image: Input grayscale image

        Returns:
            Tuple of (rescued_image, rescue_report)
        """
        self.logger.info("Starting image rescue analysis...")

        # Initialize rescue report
        rescue_report = {
            'original_size': image.shape,
            'problems_detected': [],
            'fixes_applied': [],
            'quality_tier': None,
            'darkness_level': None,
            'customer_warning': None,
            'quality_score': 0,
            'expected_lithophane_quality': '?/10'
        }

        # Analyze problems
        quality_tier = self._classify_resolution(image)
        darkness_level = self._classify_darkness(image)
        contrast_level = self._assess_contrast(image)
        artifact_severity = self._detect_compression_artifacts(image)

        rescue_report['quality_tier'] = quality_tier.value
        rescue_report['darkness_level'] = darkness_level.value
        rescue_report['contrast_level'] = contrast_level
        rescue_report['artifact_severity'] = artifact_severity

        # Start rescue process
        rescued = image.copy()

        # Fix 1: Resolution rescue (if needed)
        if quality_tier in [ImageQualityTier.POOR, ImageQualityTier.VERY_POOR]:
            rescued, upscale_report = self._rescue_low_resolution(rescued, quality_tier)
            rescue_report['problems_detected'].append(f"Low resolution: {image.shape[1]}x{image.shape[0]}")
            rescue_report['fixes_applied'].append(upscale_report)

        # Fix 2: Darkness rescue (if needed)
        if darkness_level != DarknessLevel.NORMAL:
            rescued, darkness_report = self._rescue_darkness(rescued, darkness_level)
            rescue_report['problems_detected'].append(f"Dark image: brightness={np.mean(image):.1f}")
            rescue_report['fixes_applied'].append(darkness_report)

        # Fix 3: Contrast rescue (if needed)
        if contrast_level < 25:
            rescued, contrast_report = self._rescue_low_contrast(rescued, contrast_level)
            rescue_report['problems_detected'].append(f"Low contrast: {contrast_level:.1f}")
            rescue_report['fixes_applied'].append(contrast_report)

        # Fix 4: Compression artifact rescue (if needed)
        if artifact_severity > 50:
            rescued, artifact_report = self._rescue_compression_artifacts(rescued, artifact_severity)
            rescue_report['problems_detected'].append(f"JPEG compression artifacts detected")
            rescue_report['fixes_applied'].append(artifact_report)

        # Calculate final quality score and customer communication
        rescue_report['quality_score'] = self._calculate_rescue_quality_score(rescue_report)
        rescue_report['expected_lithophane_quality'] = self._estimate_lithophane_quality(rescue_report)
        rescue_report['customer_warning'] = self._generate_customer_message(rescue_report)

        # Log summary
        self.logger.info(
            f"Rescue complete: {len(rescue_report['problems_detected'])} problems detected, "
            f"{len(rescue_report['fixes_applied'])} fixes applied, "
            f"quality score: {rescue_report['quality_score']}/100"
        )

        return rescued, rescue_report

    def _classify_resolution(self, image: np.ndarray) -> ImageQualityTier:
        """Classify image resolution quality tier."""
        height, width = image.shape[:2]
        min_dimension = min(width, height)

        if min_dimension >= self.RESOLUTION_EXCELLENT:
            return ImageQualityTier.EXCELLENT
        elif min_dimension >= self.RESOLUTION_GOOD:
            return ImageQualityTier.GOOD
        elif min_dimension >= self.RESOLUTION_ACCEPTABLE:
            return ImageQualityTier.ACCEPTABLE
        elif min_dimension >= self.RESOLUTION_POOR:
            return ImageQualityTier.POOR
        elif min_dimension >= self.RESOLUTION_VERY_POOR:
            return ImageQualityTier.VERY_POOR
        else:
            return ImageQualityTier.UNUSABLE

    def _classify_darkness(self, image: np.ndarray) -> DarknessLevel:
        """Classify image darkness level."""
        mean_brightness = np.mean(image)

        if self.BRIGHTNESS_NORMAL_MIN <= mean_brightness <= self.BRIGHTNESS_NORMAL_MAX:
            return DarknessLevel.NORMAL
        elif mean_brightness >= self.BRIGHTNESS_SLIGHTLY_DARK:
            return DarknessLevel.SLIGHTLY_DARK
        elif mean_brightness >= self.BRIGHTNESS_DARK:
            return DarknessLevel.DARK
        elif mean_brightness >= self.BRIGHTNESS_VERY_DARK:
            return DarknessLevel.VERY_DARK
        else:
            return DarknessLevel.EXTREMELY_DARK

    def _assess_contrast(self, image: np.ndarray) -> float:
        """Assess image contrast level."""
        return float(np.std(image))

    def _detect_compression_artifacts(self, image: np.ndarray) -> float:
        """
        Detect JPEG compression artifacts.

        Returns:
            Artifact severity score (0-100, higher = worse)
        """
        # Look for 8x8 block patterns characteristic of JPEG
        laplacian = cv2.Laplacian(image, cv2.CV_64F)
        edges = np.abs(laplacian)

        # High frequency noise indicates compression
        high_freq_noise = np.std(edges)

        # Blocking artifacts (8x8 grid pattern)
        block_score = 0
        if image.shape[0] > 64 and image.shape[1] > 64:
            # Sample grid positions for discontinuities
            for y in range(8, image.shape[0] - 8, 8):
                for x in range(8, image.shape[1] - 8, 8):
                    # Check discontinuity at block boundaries
                    boundary_diff = abs(float(image[y, x]) - float(image[y-1, x]))
                    if boundary_diff > 5:
                        block_score += 1

        # Combine metrics
        artifact_score = min(100, high_freq_noise * 2 + (block_score / 10))

        return artifact_score

    def _rescue_low_resolution(self, image: np.ndarray,
                               quality_tier: ImageQualityTier) -> Tuple[np.ndarray, str]:
        """
        Rescue low-resolution images using AI-powered upscaling.

        Args:
            image: Input image
            quality_tier: Quality classification

        Returns:
            Tuple of (upscaled_image, report_message)
        """
        height, width = image.shape[:2]

        # Determine target resolution based on quality tier
        if quality_tier == ImageQualityTier.VERY_POOR:
            # Need aggressive upscaling (4-6x)
            target_min = 1200
        elif quality_tier == ImageQualityTier.POOR:
            # Need significant upscaling (2-4x)
            target_min = 1000
        else:
            # Minor upscaling (1.5-2x)
            target_min = 1200

        self.logger.info(f"Upscaling image from {width}x{height} to minimum {target_min}px")

        # Try AI upscaling first for best quality
        if self.ai_upscaler.is_available():
            try:
                upscaled, method = self.ai_upscaler.upscale_to_target_size(image, target_min)
                report = f"{method}: {width}x{height} → {upscaled.shape[1]}x{upscaled.shape[0]}"
                return upscaled, report
            except Exception as e:
                self.logger.warning(f"AI upscaling failed: {e}. Falling back to traditional method.")

        # Fallback to traditional upscaling
        current_min = min(width, height)
        upscale_factor = target_min / current_min
        upscale_factor = min(upscale_factor, 6)  # Cap at 6x

        if upscale_factor >= 2:
            # Use advanced multi-stage upscaling for large factors
            upscaled = self._advanced_upscale(image, upscale_factor)
            method = "Advanced multi-stage upscaling"
        else:
            # Use single-stage for minor upscaling
            new_width = int(width * upscale_factor)
            new_height = int(height * upscale_factor)
            upscaled = cv2.resize(image, (new_width, new_height),
                                interpolation=cv2.INTER_LANCZOS4)
            method = "Lanczos4 upscaling"

        report = f"{method}: {width}x{height} → {upscaled.shape[1]}x{upscaled.shape[0]} ({upscale_factor:.1f}x)"

        return upscaled, report

    def _advanced_upscale(self, image: np.ndarray, factor: float) -> np.ndarray:
        """
        Advanced upscaling using edge-preserving techniques.

        This is a fallback implementation. For production, consider:
        - Real-ESRGAN (best quality, requires GPU)
        - waifu2x (good quality, slower)
        - OpenCV DNN super-resolution models
        """
        # Multi-stage upscaling for better quality
        current = image.copy()
        remaining_factor = factor

        while remaining_factor > 1.5:
            # Upscale by 2x per stage
            stage_factor = min(2, remaining_factor)
            h, w = current.shape[:2]
            new_w = int(w * stage_factor)
            new_h = int(h * stage_factor)

            # Use Lanczos for each stage
            current = cv2.resize(current, (new_w, new_h),
                               interpolation=cv2.INTER_LANCZOS4)

            # Apply edge-preserving smoothing to reduce artifacts
            current = cv2.bilateralFilter(current, d=5, sigmaColor=10, sigmaSpace=10)

            remaining_factor /= stage_factor

        # Final stage if needed
        if remaining_factor > 1.01:
            h, w = current.shape[:2]
            new_w = int(w * remaining_factor)
            new_h = int(h * remaining_factor)
            current = cv2.resize(current, (new_w, new_h),
                               interpolation=cv2.INTER_LANCZOS4)

        # Subtle sharpening to recover detail
        gaussian = cv2.GaussianBlur(current, (0, 0), 1.0)
        sharpened = cv2.addWeighted(current, 1.5, gaussian, -0.5, 0)

        return np.clip(sharpened, 0, 255).astype(np.uint8)

    def _rescue_darkness(self, image: np.ndarray,
                        darkness_level: DarknessLevel) -> Tuple[np.ndarray, str]:
        """
        Rescue dark images with adaptive brightening.

        Args:
            image: Input image
            darkness_level: Darkness classification

        Returns:
            Tuple of (brightened_image, report_message)
        """
        current_brightness = np.mean(image)

        # Determine brightening strategy based on darkness level
        if darkness_level == DarknessLevel.EXTREMELY_DARK:
            # Aggressive brightening needed
            gamma = 0.4
            shadow_boost = 0.3
            method = "Aggressive brightening"
        elif darkness_level == DarknessLevel.VERY_DARK:
            # Strong brightening
            gamma = 0.5
            shadow_boost = 0.2
            method = "Strong brightening"
        elif darkness_level == DarknessLevel.DARK:
            # Moderate brightening
            gamma = 0.65
            shadow_boost = 0.15
            method = "Moderate brightening"
        else:  # SLIGHTLY_DARK
            # Gentle brightening
            gamma = 0.85
            shadow_boost = 0.08
            method = "Gentle brightening"

        # Apply gamma correction
        normalized = image.astype(np.float64) / 255.0
        gamma_corrected = np.power(normalized, gamma)

        # Boost shadows specifically
        shadow_mask = normalized < 0.3
        gamma_corrected[shadow_mask] += shadow_boost * (0.3 - normalized[shadow_mask])

        # Apply adaptive histogram equalization for local contrast
        brightened = (gamma_corrected * 255).astype(np.uint8)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(brightened)

        # Blend: 70% CLAHE, 30% gamma corrected (preserve naturalness)
        result = cv2.addWeighted(enhanced, 0.7, brightened, 0.3, 0)

        new_brightness = np.mean(result)

        report = (f"{method}: brightness {current_brightness:.1f} → {new_brightness:.1f} "
                 f"(gamma={gamma}, shadow_boost={shadow_boost})")

        return result, report

    def _rescue_low_contrast(self, image: np.ndarray,
                            contrast_level: float) -> Tuple[np.ndarray, str]:
        """
        Rescue low-contrast images.

        Args:
            image: Input image
            contrast_level: Current contrast (std deviation)

        Returns:
            Tuple of (enhanced_image, report_message)
        """
        # Use adaptive histogram equalization
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(image)

        # Calculate new contrast
        new_contrast = np.std(enhanced)

        # Blend with original to avoid over-processing
        if contrast_level < 15:
            # Very low contrast, use more enhancement
            result = cv2.addWeighted(enhanced, 0.8, image, 0.2, 0)
            method = "Strong contrast enhancement"
        else:
            # Moderate low contrast
            result = cv2.addWeighted(enhanced, 0.6, image, 0.4, 0)
            method = "Moderate contrast enhancement"

        final_contrast = np.std(result)

        report = f"{method}: contrast {contrast_level:.1f} → {final_contrast:.1f}"

        return result, report

    def _rescue_compression_artifacts(self, image: np.ndarray,
                                     artifact_severity: float) -> Tuple[np.ndarray, str]:
        """
        Rescue images with compression artifacts.

        Args:
            image: Input image
            artifact_severity: Severity score (0-100)

        Returns:
            Tuple of (denoised_image, report_message)
        """
        if artifact_severity > 70:
            # Heavy artifacts - aggressive denoising
            denoised = cv2.fastNlMeansDenoising(image, None, h=15,
                                               templateWindowSize=7,
                                               searchWindowSize=21)
            method = "Aggressive artifact removal"
        elif artifact_severity > 50:
            # Moderate artifacts
            denoised = cv2.fastNlMeansDenoising(image, None, h=10,
                                               templateWindowSize=7,
                                               searchWindowSize=21)
            method = "Moderate artifact removal"
        else:
            # Light artifacts
            denoised = cv2.bilateralFilter(image, d=5, sigmaColor=30, sigmaSpace=30)
            method = "Light artifact removal"

        report = f"{method}: artifact severity {artifact_severity:.1f}/100"

        return denoised, report

    def _calculate_rescue_quality_score(self, rescue_report: Dict[str, Any]) -> int:
        """
        Calculate overall quality score after rescue.

        Returns:
            Quality score 0-100
        """
        score = 100

        # Penalize based on original problems
        quality_tier = rescue_report['quality_tier']
        if quality_tier == 'very_poor':
            score -= 30
        elif quality_tier == 'poor':
            score -= 20
        elif quality_tier == 'acceptable':
            score -= 10

        darkness_level = rescue_report['darkness_level']
        if darkness_level == 'extremely_dark':
            score -= 25
        elif darkness_level == 'very_dark':
            score -= 20
        elif darkness_level == 'dark':
            score -= 15
        elif darkness_level == 'slightly_dark':
            score -= 5

        if rescue_report['contrast_level'] < 15:
            score -= 20
        elif rescue_report['contrast_level'] < 25:
            score -= 10

        if rescue_report['artifact_severity'] > 70:
            score -= 15
        elif rescue_report['artifact_severity'] > 50:
            score -= 10

        return max(0, min(100, score))

    def _estimate_lithophane_quality(self, rescue_report: Dict[str, Any]) -> str:
        """
        Estimate final lithophane quality rating.

        Returns:
            Quality rating string (e.g., "7/10")
        """
        quality_score = rescue_report['quality_score']

        if quality_score >= 90:
            return "9-10/10 (Excellent)"
        elif quality_score >= 75:
            return "8/10 (Very Good)"
        elif quality_score >= 60:
            return "7/10 (Good)"
        elif quality_score >= 45:
            return "6/10 (Acceptable)"
        elif quality_score >= 30:
            return "5/10 (Fair - issues may be visible)"
        else:
            return "3-4/10 (Poor - significant issues)"

    def _generate_customer_message(self, rescue_report: Dict[str, Any]) -> Optional[str]:
        """
        Generate customer-facing warning/info message.

        Returns:
            Message string or None if no warning needed
        """
        problems = rescue_report['problems_detected']
        quality_score = rescue_report['quality_score']
        expected_quality = rescue_report['expected_lithophane_quality']

        if not problems:
            return None

        if quality_score >= 70:
            # Good outcome despite issues
            message = f"✓ Your image had some issues but we fixed them:\n"
            for problem in problems:
                message += f"  • {problem}\n"
            message += f"\nExpected lithophane quality: {expected_quality}"
            message += "\n\nThe lithophane should look great!"

        elif quality_score >= 50:
            # Acceptable outcome
            message = f"⚠ Your image had several issues that we corrected:\n"
            for problem in problems:
                message += f"  • {problem}\n"
            message += f"\nExpected lithophane quality: {expected_quality}"
            message += "\n\nFor best results, please provide:"
            message += "\n  • Higher resolution original file (if available)"
            message += "\n  • Uncompressed version from camera/phone"
            message += "\n\nProceed with current image? Quality will be acceptable but not perfect."

        else:
            # Poor outcome - strong warning
            message = f"⚠️ WARNING: Your image has significant quality issues:\n"
            for problem in problems:
                message += f"  • {problem}\n"
            message += f"\nExpected lithophane quality: {expected_quality}"
            message += "\n\n🔴 RECOMMENDATION: Please provide a better image for optimal results!"
            message += "\n\nLook for:"
            message += "\n  • Original file from camera (not screenshot)"
            message += "\n  • Higher resolution version"
            message += "\n  • Better lit photo of the same people"
            message += "\n\nWe can still process this image, but the result may disappoint you."

        return message
