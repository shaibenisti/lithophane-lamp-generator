#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Image Processor for Lithophane Lamp Generator

Clean, simple processing pipeline:
1. Load image (with HEIC support)
2. Convert to grayscale
3. Process (resize + optional CLAHE)
4. Create thickness map
5. Done!

No AI, no face detection, no rescue systems - just clean processing.
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

logger = logging.getLogger(__name__)


class ImageProcessingError(Exception):
    """Exception raised for image processing errors."""
    pass


class IntelligentImageProcessor:
    """
    Simple and effective image processor for lithophanes.

    Processes images with minimal interference, preserving natural tonal range.
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

        # Set OpenCV threads
        cv2.setNumThreads(settings.opencv_threads)

        self.logger.info("Image processor initialized (simplified pipeline)")

    def process_image_for_lithophane(self, image_path: str) -> np.ndarray:
        """
        Complete processing pipeline: image file → thickness map.

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

            # Step 3: Get target dimensions from settings
            target_width, target_height, _, _ = self.settings.get_lithophane_dimensions()
            target_size = (target_width, target_height)

            # Step 4: Process image (resize + optional CLAHE)
            processed = self.processor.process(image, target_size)

            # Step 5: Create thickness map
            thickness_map = self.thickness_mapper.create_thickness_map(processed)

            self.logger.info("✓ Image processing completed successfully")
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
        Load image with HEIC support and convert to grayscale.

        Args:
            image_path: Path to image file

        Returns:
            Grayscale image (uint8)

        Raises:
            ImageProcessingError: If loading fails
        """
        try:
            # Load with HEIC support
            image = load_image_with_heic_support(image_path)
            if image is None:
                raise ImageProcessingError(f"Cannot load image from: {image_path}")

            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

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

    def get_processing_info(self) -> Dict[str, Any]:
        """
        Get information about the processing pipeline.

        Returns:
            Dictionary with processing configuration
        """
        return {
            'pipeline': 'simplified',
            'contrast_enhancement': True,
            'min_thickness': self.settings.min_thickness,
            'max_thickness': self.settings.max_thickness,
            'gamma': self.thickness_mapper.gamma,
            'cylinder_coverage': self.settings.lithophane_coverage_angle,
            'resolution': self.settings.resolution
        }
