#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Input Validation Utilities for Lithophane Lamp Generator
Comprehensive validation for images, files, and settings.
"""

import os
import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List
import logging

from .image_utils import calculate_histogram_distribution
from .heic_loader import get_heic_loader, load_image_with_heic_support


logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class ImageValidator:
    """
    Comprehensive image validation for lithophane processing.
    
    Validates image format, size, quality, and suitability for lithophane creation.
    """
    
    # Supported image formats (including HEIC for iPhone photos)
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif', '.heic', '.heif'}
    
    # Size constraints
    MIN_RESOLUTION = (100, 100)
    MAX_RESOLUTION = (8000, 8000)
    MAX_FILE_SIZE_MB = 50
    
    # Quality thresholds
    MIN_CONTRAST_THRESHOLD = 10
    MIN_SHARPNESS_THRESHOLD = 5
    
    @classmethod
    def validate_image_file(cls, image_path: str) -> Dict[str, Any]:
        """
        Comprehensive image file validation.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary with validation results and image metadata
            
        Raises:
            ValidationError: If image validation fails
        """
        path = Path(image_path)
        
        # Check file existence
        if not path.exists():
            raise ValidationError(f"Image file not found: {image_path}")
        
        # Check file extension
        if path.suffix.lower() not in cls.SUPPORTED_FORMATS:
            raise ValidationError(
                f"Unsupported image format: {path.suffix}. "
                f"Supported formats: {', '.join(cls.SUPPORTED_FORMATS)}"
            )
        
        # Check file size
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > cls.MAX_FILE_SIZE_MB:
            raise ValidationError(
                f"Image file too large: {file_size_mb:.1f}MB. "
                f"Maximum allowed: {cls.MAX_FILE_SIZE_MB}MB"
            )
        
        # Load and validate image (with HEIC support)
        try:
            # Use HEIC-aware loader
            image = load_image_with_heic_support(str(path))
            if image is None:
                raise ValidationError(f"Cannot read image file: {image_path}")
        except Exception as e:
            raise ValidationError(f"Failed to load image: {e}")
        
        # Validate image properties
        height, width = image.shape[:2]
        channels = image.shape[2] if len(image.shape) == 3 else 1
        
        # Check resolution
        if width < cls.MIN_RESOLUTION[0] or height < cls.MIN_RESOLUTION[1]:
            raise ValidationError(
                f"Image resolution too low: {width}x{height}. "
                f"Minimum required: {cls.MIN_RESOLUTION[0]}x{cls.MIN_RESOLUTION[1]}"
            )
        
        if width > cls.MAX_RESOLUTION[0] or height > cls.MAX_RESOLUTION[1]:
            logger.warning(
                f"Large image detected: {width}x{height}. "
                f"Processing may be slow. Consider resizing."
            )
        
        # Convert to grayscale for quality analysis
        if channels == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Quality assessments
        quality_metrics = cls._assess_image_quality(gray)
        
        return {
            'valid': True,
            'path': str(path),
            'width': width,
            'height': height,
            'channels': channels,
            'file_size_mb': file_size_mb,
            'format': path.suffix.lower(),
            'quality_metrics': quality_metrics
        }
    
    @classmethod
    def _assess_image_quality(cls, gray_image: np.ndarray) -> Dict[str, Any]:
        """
        Assess image quality metrics for lithophane suitability.
        
        Args:
            gray_image: Grayscale image array
            
        Returns:
            Dictionary with quality metrics
        """
        # Contrast assessment
        contrast = np.std(gray_image)
        
        # Sharpness assessment using Laplacian variance
        laplacian = cv2.Laplacian(gray_image, cv2.CV_64F)
        sharpness = laplacian.var()
        
        # Brightness distribution
        brightness_mean = np.mean(gray_image)
        brightness_std = np.std(gray_image)

        # Histogram analysis using shared utility
        shadows, midtones, highlights = calculate_histogram_distribution(gray_image)
        
        # Quality warnings
        warnings = []
        if contrast < cls.MIN_CONTRAST_THRESHOLD:
            warnings.append("Low contrast - may result in poor lithophane quality")
        
        if sharpness < cls.MIN_SHARPNESS_THRESHOLD:
            warnings.append("Low sharpness - image may appear blurry")
        
        # Note: Dark images are now handled with increased thickness (up to 2.5mm)
        # so we only warn on EXTREMELY dark images
        if brightness_mean < 25:
            warnings.append("Extremely dark image - will result in thick lithophane areas (up to 2.5mm)")
        elif brightness_mean > 220:
            warnings.append("Very bright image - may lack depth and contrast")
        
        if shadows > 0.7:
            warnings.append("Many dark areas detected - will create dramatic depth (thicker walls)")
        elif highlights > 0.5:
            warnings.append("Many bright areas - ensure sufficient contrast for depth")
        
        return {
            'contrast': contrast,
            'sharpness': sharpness,
            'brightness_mean': brightness_mean,
            'brightness_std': brightness_std,
            'shadows_ratio': shadows,
            'highlights_ratio': highlights,
            'midtones_ratio': midtones,
            'warnings': warnings,
            'quality_score': cls._calculate_quality_score(contrast, sharpness, midtones)
        }
    
    @classmethod
    def _calculate_quality_score(cls, contrast: float, sharpness: float, midtones: float) -> float:
        """
        Calculate overall quality score (0-100).
        
        Args:
            contrast: Contrast value
            sharpness: Sharpness value
            midtones: Midtones ratio
            
        Returns:
            Quality score from 0 to 100
        """
        # Normalize components
        contrast_score = min(100, (contrast / 50) * 100)
        sharpness_score = min(100, (sharpness / 100) * 100)
        midtones_score = midtones * 100  # Higher midtones = better for lithophanes
        
        # Weighted average
        quality_score = (contrast_score * 0.4 + sharpness_score * 0.3 + midtones_score * 0.3)
        
        return min(100, max(0, quality_score))


class FileValidator:
    """Validation utilities for file paths and operations."""
    
    @staticmethod
    def validate_output_path(output_path: str) -> str:
        """
        Validate and normalize output file path.
        
        Args:
            output_path: Desired output path
            
        Returns:
            Validated and normalized path
            
        Raises:
            ValidationError: If path is invalid
        """
        path = Path(output_path)
        
        # Ensure .stl extension
        if not path.suffix.lower() == '.stl':
            path = path.with_suffix('.stl')
        
        # Check parent directory
        parent_dir = path.parent
        if not parent_dir.exists():
            try:
                parent_dir.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                raise ValidationError(f"Cannot create directory: {parent_dir}")
        
        # Check write permissions
        if parent_dir.exists() and not os.access(parent_dir, os.W_OK):
            raise ValidationError(f"No write permission for directory: {parent_dir}")
        
        # Check if file exists and warn
        if path.exists():
            logger.warning(f"Output file already exists and will be overwritten: {path}")
        
        return str(path)
    
    @staticmethod
    def validate_config_path(config_path: str) -> Path:
        """
        Validate configuration file path.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Validated Path object
            
        Raises:
            ValidationError: If path is invalid
        """
        path = Path(config_path)
        
        if path.exists() and not path.is_file():
            raise ValidationError(f"Config path is not a file: {config_path}")
        
        if path.exists() and not os.access(path, os.R_OK):
            raise ValidationError(f"Cannot read config file: {config_path}")
        
        return path


class SettingsValidator:
    """Validation for application settings."""
    
    @staticmethod
    def validate_dimensions(diameter: float, height: float, wall_thickness: float) -> None:
        """
        Validate physical dimensions.
        
        Args:
            diameter: Cylinder diameter
            height: Cylinder height
            wall_thickness: Wall thickness
            
        Raises:
            ValidationError: If dimensions are invalid
        """
        if diameter <= 0:
            raise ValidationError("Cylinder diameter must be positive")
        
        if height <= 0:
            raise ValidationError("Cylinder height must be positive")
        
        if wall_thickness <= 0:
            raise ValidationError("Wall thickness must be positive")
        
        if wall_thickness >= diameter / 2:
            raise ValidationError("Wall thickness cannot exceed cylinder radius")
        
        # Practical limits for 3D printing
        if diameter < 10 or diameter > 200:
            logger.warning(f"Unusual cylinder diameter: {diameter}mm")
        
        if height < 20 or height > 300:
            logger.warning(f"Unusual cylinder height: {height}mm")
        
        if wall_thickness < 0.8 or wall_thickness > 5:
            logger.warning(f"Unusual wall thickness: {wall_thickness}mm")
    
    @staticmethod
    def validate_resolution(resolution: float) -> None:
        """
        Validate resolution setting.
        
        Args:
            resolution: Resolution value
            
        Raises:
            ValidationError: If resolution is invalid
        """
        if not 0.01 <= resolution <= 1.0:
            raise ValidationError("Resolution must be between 0.01 and 1.0")
    
    @staticmethod
    def validate_thickness_range(min_thickness: float, max_thickness: float) -> None:
        """
        Validate thickness range.
        
        Args:
            min_thickness: Minimum thickness
            max_thickness: Maximum thickness
            
        Raises:
            ValidationError: If thickness range is invalid
        """
        if min_thickness <= 0:
            raise ValidationError("Minimum thickness must be positive")
        
        if max_thickness <= min_thickness:
            raise ValidationError("Maximum thickness must be greater than minimum")
        
        if max_thickness - min_thickness < 0.5:
            logger.warning("Small thickness range may reduce detail quality")


def validate_processing_environment() -> Dict[str, Any]:
    """
    Validate processing environment and dependencies.
    
    Returns:
        Dictionary with environment validation results
    """
    results = {
        'opencv_available': False,
        'opencv_version': None,
        'numpy_available': False,
        'trimesh_available': False,
        'memory_available_gb': 0,
        'warnings': []
    }
    
    # Check OpenCV
    try:
        import cv2
        results['opencv_available'] = True
        results['opencv_version'] = cv2.__version__
    except ImportError:
        results['warnings'].append("OpenCV not available")
    
    # Check NumPy
    try:
        import numpy
        results['numpy_available'] = True
    except ImportError:
        results['warnings'].append("NumPy not available")
    
    # Check Trimesh
    try:
        import trimesh
        results['trimesh_available'] = True
    except ImportError:
        results['warnings'].append("Trimesh not available")
    
    # Check memory
    try:
        import psutil
        memory_gb = psutil.virtual_memory().available / (1024**3)
        results['memory_available_gb'] = memory_gb
        
        if memory_gb < 2:
            results['warnings'].append("Low available memory - processing may be slow")
    except ImportError:
        results['warnings'].append("Cannot check memory usage")
    
    return results