#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Image Utility Functions for Lithophane Lamp Generator
Shared utility functions for image processing tasks.
"""

import cv2
import numpy as np
from typing import Tuple
from ..core import constants as const


def calculate_histogram_distribution(image: np.ndarray) -> Tuple[float, float, float]:
    """
    Calculate histogram distribution (shadows, midtones, highlights).

    Shared utility to avoid code duplication across multiple modules.

    Args:
        image: Grayscale image array (uint8)

    Returns:
        Tuple of (shadows_ratio, midtones_ratio, highlights_ratio)
    """
    # Calculate histogram
    hist = cv2.calcHist([image], [0], None, [const.HISTOGRAM_BINS], const.HISTOGRAM_RANGE)
    hist_normalized = hist.flatten() / hist.sum()

    # Calculate distribution ratios
    shadows = np.sum(hist_normalized[:const.HISTOGRAM_SHADOW_CUTOFF])
    highlights = np.sum(hist_normalized[const.HISTOGRAM_HIGHLIGHT_CUTOFF:])
    midtones = np.sum(hist_normalized[const.HISTOGRAM_SHADOW_CUTOFF:const.HISTOGRAM_HIGHLIGHT_CUTOFF])

    return shadows, midtones, highlights
