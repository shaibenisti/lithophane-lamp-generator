#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple Image Processor for Lithophane Lamp Generator

Clean, minimal processing that preserves the natural tonal range of images.
Philosophy: Let the backlight do the work - don't over-process!
"""

import cv2
import numpy as np
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class SimpleImageProcessor:
    """
    Minimalist image processor for lithophanes.

    Does only what's necessary:
    1. Convert to grayscale
    2. Resize to target dimensions
    3. Optional light contrast enhancement (CLAHE)
    4. That's it!

    No AI, no face detection, no multi-stage enhancement.
    Just clean, predictable processing that respects the original image.
    """

    def __init__(self, enable_contrast_enhancement: bool = True):
        """
        Initialize simple processor.

        Args:
            enable_contrast_enhancement: Apply light CLAHE for better detail (recommended)
        """
        self.enable_contrast_enhancement = enable_contrast_enhancement
        self.logger = logging.getLogger(__name__)

        # CLAHE parameters - very light enhancement to avoid skin texture noise
        self.clahe = cv2.createCLAHE(
            clipLimit=1.5,      # Reduced from 2.0 - less aggressive
            tileGridSize=(8, 8) # Standard tile size
        )

    def process(self, image: np.ndarray, target_size: Tuple[int, int]) -> np.ndarray:
        """
        Process image for lithophane creation.

        Args:
            image: Input grayscale image (uint8)
            target_size: (width, height) for final lithophane

        Returns:
            Processed grayscale image ready for thickness mapping
        """
        self.logger.info(f"Processing image: {image.shape[1]}×{image.shape[0]} → {target_size[0]}×{target_size[1]}")

        # Ensure grayscale
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Step 1: Resize to target dimensions
        # Using Lanczos for high-quality downsampling/upsampling
        resized = cv2.resize(image, target_size, interpolation=cv2.INTER_LANCZOS4)
        self.logger.info(f"Resized to {resized.shape[1]}×{resized.shape[0]}")

        # Step 2: Optional contrast enhancement
        if self.enable_contrast_enhancement:
            enhanced = self.clahe.apply(resized)
            self.logger.info("Applied light contrast enhancement (CLAHE)")
        else:
            enhanced = resized
            self.logger.info("No contrast enhancement applied")

        # Step 3: Done! Return processed image
        self.logger.info("Processing complete")
        return enhanced

    def process_with_info(self, image: np.ndarray, target_size: Tuple[int, int]) -> Tuple[np.ndarray, dict]:
        """
        Process image and return processing info.

        Args:
            image: Input grayscale image
            target_size: Target dimensions

        Returns:
            Tuple of (processed_image, info_dict)
        """
        processed = self.process(image, target_size)

        info = {
            'original_size': (image.shape[1], image.shape[0]),
            'target_size': target_size,
            'contrast_enhanced': self.enable_contrast_enhancement,
            'brightness_mean': float(np.mean(processed)),
            'brightness_std': float(np.std(processed))
        }

        return processed, info


def validate_image_for_processing(image: np.ndarray) -> bool:
    """
    Quick validation that image is suitable for processing.

    Args:
        image: Input image array

    Returns:
        True if image is valid, False otherwise
    """
    if image is None or image.size == 0:
        logger.error("Image is None or empty")
        return False

    # Check minimum dimensions
    min_dimension = min(image.shape[:2])
    if min_dimension < 100:
        logger.error(f"Image too small: {image.shape} (minimum 100px)")
        return False

    # Check maximum dimensions (prevent memory issues)
    max_dimension = max(image.shape[:2])
    if max_dimension > 8000:
        logger.warning(f"Image very large: {image.shape} (may be slow)")

    return True


# Convenience function for quick processing
def quick_process(image: np.ndarray, target_size: Tuple[int, int]) -> np.ndarray:
    """
    Quick one-line processing function.

    Args:
        image: Input grayscale image
        target_size: Target dimensions

    Returns:
        Processed image
    """
    processor = SimpleImageProcessor()
    return processor.process(image, target_size)
