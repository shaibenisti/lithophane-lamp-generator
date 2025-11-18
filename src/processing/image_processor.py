#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Image Processor for Lithophane Lamp Generator

Smart processing pipeline:
1. Load image (with HEIC support)
2. Convert to perceptual luminance (Rec. 709)
3. Detect faces
4. Enhance face regions (if detected)
5. Calculate optimal gamma
6. Process (resize + CLAHE + bilateral filter)
7. Create thickness map

Features: Face detection, perceptual luminance, adaptive gamma.
"""

import cv2
import numpy as np
import logging
from typing import Dict, Any

from ..core.settings import Settings
from ..utils.validation import ImageValidator, ValidationError
from ..utils.heic_loader import load_image_with_heic_support
from .simple_processor import SimpleImageProcessor
from .thickness_mapper import ThicknessMapper
from .face_handler import FaceHandler, FaceDetectionResult

logger = logging.getLogger(__name__)


class ImageProcessingError(Exception):
    """Exception raised for image processing errors."""
    pass


class IntelligentImageProcessor:
    """
    Smart and effective image processor for lithophanes.

    Analyzes images and applies adaptive processing:
    - Detects and enhances faces
    - Lifts shadows for better visibility
    - Preserves natural tonal range
    """

    def __init__(self, settings: Settings):
        """
        Initialize image processor.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.logger = logging.getLogger(__name__)

        # Initialize processing components
        self.processor = SimpleImageProcessor(enable_contrast_enhancement=True)
        self.thickness_mapper = ThicknessMapper(settings)
        self.face_handler = FaceHandler()

        # Set OpenCV threads
        cv2.setNumThreads(settings.opencv_threads)

        self.logger.info("Image processor initialized (smart pipeline with face detection)")

    def _calculate_smart_gamma(self, image: np.ndarray,
                               face_result: FaceDetectionResult) -> float:
        """
        Calculate optimal gamma based on image characteristics.

        Gamma < 1.0 brightens midtones (good for portraits and dark images)
        Gamma > 1.0 darkens midtones (rarely needed for lithophanes)
        Gamma = 1.0 linear (faithful to original)

        Args:
            image: Input grayscale image
            face_result: Face detection results

        Returns:
            Optimal gamma value
        """
        # If user explicitly set gamma, always use that
        if self.settings.gamma_override is not None:
            gamma = self.settings.gamma_override
            self.logger.info(f"Using manual gamma override: {gamma}")
            return gamma

        # Calculate image brightness
        mean_brightness = float(np.mean(image))
        brightness_pct = mean_brightness / 255.0

        # Smart gamma selection based on image type
        if face_result.has_faces:
            # PORTRAIT MODE: Use gentler gamma to preserve facial details
            if brightness_pct < 0.35:
                # Very dark portrait
                gamma = 0.80
                reason = "dark portrait"
            elif brightness_pct < 0.50:
                # Moderately dark portrait
                gamma = 0.85
                reason = "portrait with shadows"
            else:
                # Well-lit portrait
                gamma = 0.90
                reason = "well-lit portrait"
        else:
            # GENERAL IMAGE MODE
            if brightness_pct < 0.30:
                # Very dark image
                gamma = 0.85
                reason = "very dark image"
            elif brightness_pct < 0.45:
                # Moderately dark
                gamma = 0.92
                reason = "moderately dark image"
            elif brightness_pct > 0.75:
                # Very bright image - use linear or slightly darker
                gamma = 1.0
                reason = "bright image (linear)"
            else:
                # Normal brightness
                gamma = 0.95
                reason = "normal brightness"

        self.logger.info(f"Smart gamma selected: {gamma} ({reason}, brightness: {brightness_pct*100:.1f}%)")
        return gamma

    def process_image_for_lithophane(self, image_path: str) -> np.ndarray:
        """
        Complete smart processing pipeline: image file → thickness map.

        Pipeline:
        1. Validate and load image
        2. Convert to perceptual luminance
        3. Detect faces (if any)
        4. Enhance face regions (if faces detected)
        5. Calculate optimal gamma
        6. Resize and enhance contrast
        7. Create thickness map

        Args:
            image_path: Path to input image file

        Returns:
            Thickness map array (float32) ready for 3D cylinder builder

        Raises:
            ImageProcessingError: If processing fails
        """
        try:
            # Step 1: Validate image file
            validation_result = ImageValidator.validate_image_file(image_path)
            self._log_image_info(validation_result)

            # Step 2: Load and convert to grayscale
            image = self._load_and_convert_image(image_path)
            self.logger.info(f"Loaded image: {image.shape[1]}×{image.shape[0]}")

            # Step 3: Detect faces
            self.logger.info("Analyzing image for faces...")
            face_result = self.face_handler.detect_faces(image)

            # Step 4: Apply intelligent pre-processing
            preprocessed = image.copy()

            # Enhance faces if detected
            if face_result.has_faces:
                self.logger.info(f"Enhancing {face_result.face_count} detected face(s)")
                preprocessed = self.face_handler.enhance_face_regions(
                    preprocessed, face_result
                )

            # Step 5: Calculate optimal gamma based on image analysis
            optimal_gamma = self._calculate_smart_gamma(image, face_result)
            # Temporarily override gamma for this image
            original_gamma = self.thickness_mapper.gamma
            self.thickness_mapper.gamma = optimal_gamma

            # Step 6: Get target dimensions from settings
            target_width, target_height, _, _ = self.settings.get_lithophane_dimensions()
            target_size = (target_width, target_height)

            # Step 7: Process image (resize + optional CLAHE + bilateral filter + Gaussian)
            processed = self.processor.process(preprocessed, target_size)

            # Step 7.5: Final texture elimination pass
            # Apply one more gentle Gaussian blur to ensure absolutely no texture
            # survives into the thickness map (this is the last defense)
            final_smoothed = cv2.GaussianBlur(processed, (5, 5), 0)
            self.logger.info("Applied final texture elimination pass")

            # Step 8: Create thickness map with optimal gamma
            thickness_map = self.thickness_mapper.create_thickness_map(final_smoothed)

            # Restore original gamma
            self.thickness_mapper.gamma = original_gamma

            self.logger.info("✓ Smart image processing completed successfully")
            self._log_processing_summary(face_result)

            return thickness_map

        except ValidationError as e:
            raise ImageProcessingError(f"Image validation failed: {e}")
        except (IOError, OSError) as e:
            self.logger.error(f"File I/O error: {e}", exc_info=True)
            raise ImageProcessingError(f"Failed to read image file: {e}")
        except cv2.error as e:
            self.logger.error(f"OpenCV error: {e}", exc_info=True)
            raise ImageProcessingError(f"Image processing error: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}", exc_info=True)
            raise ImageProcessingError(f"Unexpected error during processing: {e}")

    def _load_and_convert_image(self, image_path: str) -> np.ndarray:
        """
        Load image with HEIC support and convert to perceptual luminance.

        Uses Rec. 709 standard for perceptual luminance conversion which handles
        colored lighting and skin tones better than simple grayscale conversion.

        Args:
            image_path: Path to image file

        Returns:
            Perceptual luminance image (uint8)

        Raises:
            ImageProcessingError: If loading fails
        """
        try:
            # Load with HEIC support
            image = load_image_with_heic_support(image_path)
            if image is None:
                raise ImageProcessingError(f"Cannot load image from: {image_path}")

            # Convert to perceptual luminance using Rec. 709 standard
            if len(image.shape) == 3:
                # Handle alpha channel (RGBA/BGRA images)
                if image.shape[2] == 4:
                    # Convert BGRA to BGR (drop alpha channel)
                    image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
                    self.logger.info("Removed alpha channel from RGBA image")

                # Rec. 709 luma coefficients: Y = 0.2126*R + 0.7152*G + 0.0722*B
                # OpenCV uses BGR, so we need: Y = 0.0722*B + 0.7152*G + 0.2126*R
                b, g, r = cv2.split(image)

                # Calculate perceptual luminance
                luminance = (
                    0.0722 * b.astype(np.float32) +
                    0.7152 * g.astype(np.float32) +
                    0.2126 * r.astype(np.float32)
                )

                # Convert back to uint8
                gray = np.clip(luminance, 0, 255).astype(np.uint8)
                self.logger.info("Converted to perceptual luminance (Rec. 709)")
            else:
                gray = image.copy()
                self.logger.info("Image already grayscale")

            return gray

        except Exception as e:
            raise ImageProcessingError(f"Failed to load image: {e}")

    def _log_image_info(self, validation_result: Dict[str, Any]) -> None:
        """
        Log image information from validation.

        Args:
            validation_result: Validation results dictionary
        """
        quality = validation_result['quality_metrics']
        self.logger.info(
            f"Image: {validation_result['width']}×{validation_result['height']}, "
            f"{validation_result['file_size_mb']:.1f}MB, "
            f"quality score: {quality['quality_score']:.1f}/100"
        )

        if quality['warnings']:
            for warning in quality['warnings']:
                self.logger.warning(f"Image quality: {warning}")

    def _log_processing_summary(self, face_result: FaceDetectionResult) -> None:
        """
        Log summary of intelligent processing applied.

        Args:
            face_result: Face detection results
        """
        if face_result.has_faces:
            self.logger.info(f"Smart processing applied: {face_result.face_count} face(s) enhanced")
        else:
            self.logger.info("Processing complete (no faces detected)")

    def get_processing_info(self) -> Dict[str, Any]:
        """
        Get information about the processing pipeline.

        Returns:
            Dictionary with processing configuration
        """
        return {
            'pipeline': 'smart',
            'features': ['face_detection', 'perceptual_luminance', 'adaptive_enhancement'],
            'contrast_enhancement': True,
            'min_thickness': self.settings.min_thickness,
            'max_thickness': self.settings.max_thickness,
            'gamma': self.thickness_mapper.gamma,
            'cylinder_coverage': self.settings.lithophane_coverage_angle,
            'resolution': self.settings.resolution
        }
