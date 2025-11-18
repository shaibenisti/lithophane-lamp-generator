#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configuration Settings for Lithophane Lamp Generator
Centralized configuration management with validation and type safety.
"""

import math
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
from functools import lru_cache

# Import constants from centralized module
from . import constants as const

# Use constants from the constants module
DEFAULT_CYLINDER_DIAMETER = const.DEFAULT_CYLINDER_DIAMETER
DEFAULT_CYLINDER_HEIGHT = const.DEFAULT_CYLINDER_HEIGHT
DEFAULT_WALL_THICKNESS = const.DEFAULT_WALL_THICKNESS
DEFAULT_NOZZLE_DIAMETER = const.DEFAULT_NOZZLE_DIAMETER
DEFAULT_LAYER_HEIGHT = const.DEFAULT_LAYER_HEIGHT
DEFAULT_MIN_THICKNESS = const.DEFAULT_MIN_THICKNESS
DEFAULT_MAX_THICKNESS = const.DEFAULT_MAX_THICKNESS
DEFAULT_RESOLUTION = const.DEFAULT_RESOLUTION
DEFAULT_LITHOPHANE_COVERAGE_ANGLE = const.DEFAULT_LITHOPHANE_COVERAGE_ANGLE
DEFAULT_TOP_MARGIN = const.DEFAULT_TOP_MARGIN
DEFAULT_BOTTOM_MARGIN = const.DEFAULT_BOTTOM_MARGIN

# Gamma correction - simplified (old portrait/detection modes removed)
# 1.0 = faithful to original image


@dataclass
class Settings:

    cylinder_diameter: float = DEFAULT_CYLINDER_DIAMETER
    cylinder_height: float = DEFAULT_CYLINDER_HEIGHT
    wall_thickness: float = DEFAULT_WALL_THICKNESS

    nozzle_diameter: float = DEFAULT_NOZZLE_DIAMETER
    layer_height: float = DEFAULT_LAYER_HEIGHT
    min_thickness: float = DEFAULT_MIN_THICKNESS
    max_thickness: float = DEFAULT_MAX_THICKNESS

    resolution: float = DEFAULT_RESOLUTION
    mesh_quality_multiplier: float = 1.2
    lithophane_coverage_angle: float = DEFAULT_LITHOPHANE_COVERAGE_ANGLE

    top_margin: float = DEFAULT_TOP_MARGIN
    bottom_margin: float = DEFAULT_BOTTOM_MARGIN

    detail_enhancement: bool = True

    # Manual gamma override (1.0 = no correction)
    gamma_override: Optional[float] = None

    # Number of OpenCV threads (can be overridden from environment at startup)
    opencv_threads: int = 4
    
    def __post_init__(self):
        """Validate settings after initialization."""
        self._validate_settings()
    
    def _validate_settings(self) -> None:
        """
        Validate all settings are within acceptable ranges.

        Raises:
            ValueError: If any setting is invalid
        """
        # Physical dimensions validation
        if self.cylinder_diameter <= 0:
            raise ValueError(f"Cylinder diameter must be positive, got {self.cylinder_diameter}")

        if self.cylinder_height <= 0:
            raise ValueError(f"Cylinder height must be positive, got {self.cylinder_height}")

        if self.wall_thickness <= 0:
            raise ValueError(f"Wall thickness must be positive, got {self.wall_thickness}")

        if self.wall_thickness >= self.cylinder_diameter / 2:
            raise ValueError(f"Wall thickness ({self.wall_thickness}mm) must be less than cylinder radius ({self.cylinder_diameter/2}mm)")

        # Thickness validation
        if self.min_thickness < 0:
            raise ValueError(f"Min thickness must be non-negative, got {self.min_thickness}")

        if self.min_thickness >= self.max_thickness:
            raise ValueError(f"Min thickness ({self.min_thickness}mm) must be less than max thickness ({self.max_thickness}mm)")

        if self.max_thickness > 5.0:
            raise ValueError(f"Max thickness ({self.max_thickness}mm) is too large (max 5.0mm for printability)")

        # Quality settings validation
        if not 0 < self.resolution <= 1.0:
            raise ValueError(f"Resolution must be between 0 and 1.0, got {self.resolution}")

        if not 0 < self.lithophane_coverage_angle <= 360:
            raise ValueError(f"Coverage angle must be between 0 and 360 degrees, got {self.lithophane_coverage_angle}")

        if self.mesh_quality_multiplier <= 0:
            raise ValueError(f"Mesh quality multiplier must be positive, got {self.mesh_quality_multiplier}")

        # Printing parameters validation
        if self.nozzle_diameter <= 0:
            raise ValueError(f"Nozzle diameter must be positive, got {self.nozzle_diameter}")

        if self.layer_height <= 0:
            raise ValueError(f"Layer height must be positive, got {self.layer_height}")

        if self.layer_height > self.nozzle_diameter * 1.2:
            raise ValueError(f"Layer height ({self.layer_height}mm) should not exceed 1.2× nozzle diameter ({self.nozzle_diameter}mm)")

        # Margins validation
        if self.top_margin < 0:
            raise ValueError(f"Top margin must be non-negative, got {self.top_margin}")

        if self.bottom_margin < 0:
            raise ValueError(f"Bottom margin must be non-negative, got {self.bottom_margin}")

        if self.top_margin + self.bottom_margin >= self.cylinder_height:
            raise ValueError(f"Combined margins ({self.top_margin + self.bottom_margin}mm) must be less than cylinder height ({self.cylinder_height}mm)")


        # Performance validation
        if self.opencv_threads <= 0:
            raise ValueError(f"OpenCV threads must be positive, got {self.opencv_threads}")

        # Gamma validation
        if self.gamma_override is not None and not (0.1 <= self.gamma_override <= 3.0):
            raise ValueError(f"Gamma override must be between 0.1 and 3.0, got {self.gamma_override}")
    
    def get_inner_radius(self) -> float:
        """
        Calculate inner radius of the cylinder.
        
        Returns:
            Inner radius in millimeters
        """
        return (self.cylinder_diameter / 2) - self.wall_thickness
    
    def get_lithophane_dimensions(self) -> Tuple[int, int, float, float]:
        """
        Calculate lithophane dimensions based on settings.

        IMPROVED: Higher minimum resolution for premium quality lithophanes.

        Returns:
            Tuple of (width_pixels, height_pixels, arc_length_mm, image_height_mm)
        """
        outer_radius = self.cylinder_diameter / 2
        angle_radians = math.radians(self.lithophane_coverage_angle)
        arc_length = outer_radius * angle_radians
        image_height = self.cylinder_height - self.top_margin - self.bottom_margin

        # INCREASED minimum resolution for ultra-high quality (was 1500×1800)
        # Apply mesh_quality_multiplier to image resolution too
        min_width = int(2000 * self.mesh_quality_multiplier)
        min_height = int(2400 * self.mesh_quality_multiplier)

        base_width = max(min_width, int(arc_length / self.resolution))
        base_height = max(min_height, int(image_height / self.resolution))

        width_pixels = base_width
        height_pixels = base_height

        return width_pixels, height_pixels, arc_length, image_height
    
    def get_mesh_resolution(self) -> Tuple[int, int]:
        """
        Calculate mesh resolution for 3D cylinder generation.

        Now properly applies mesh_quality_multiplier for premium quality.
        Higher multiplier = more segments = smoother mesh = better quality.

        Returns:
            Tuple of (angular_segments, height_segments)
        """
        circumference = math.pi * self.cylinder_diameter

        # Apply mesh_quality_multiplier to resolution calculation
        # This was previously defined but never used!
        # Lower divisor = more segments = higher quality
        effective_resolution = self.resolution * const.MESH_RESOLUTION_MULTIPLIER / self.mesh_quality_multiplier

        angular_segments = int(circumference / effective_resolution)
        angular_segments = max(const.MESH_ANGULAR_SEGMENTS_MIN, min(const.MESH_ANGULAR_SEGMENTS_MAX, angular_segments))

        height_segments = int(self.cylinder_height / effective_resolution)
        height_segments = max(const.MESH_HEIGHT_SEGMENTS_MIN, min(const.MESH_HEIGHT_SEGMENTS_MAX, height_segments))

        return angular_segments, height_segments
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary for serialization."""
        return {
            'cylinder': {
                'diameter': self.cylinder_diameter,
                'height': self.cylinder_height,
                'wall_thickness': self.wall_thickness,
            },
            'printing': {
                'nozzle_diameter': self.nozzle_diameter,
                'layer_height': self.layer_height,
                'min_thickness': self.min_thickness,
                'max_thickness': self.max_thickness,
            },
            'quality': {
                'resolution': self.resolution,
                'mesh_quality_multiplier': self.mesh_quality_multiplier,
                'lithophane_coverage_angle': self.lithophane_coverage_angle,
                'detail_enhancement': self.detail_enhancement,
                'gamma_override': self.gamma_override,
            },
            'margins': {
                'top_margin': self.top_margin,
                'bottom_margin': self.bottom_margin,
            },
            'performance': {
                'opencv_threads': self.opencv_threads,
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Settings':
        """Create settings from dictionary."""
        # Define valid parameter names explicitly
        valid_params = {
            'cylinder_diameter', 'cylinder_height', 'wall_thickness',
            'nozzle_diameter', 'layer_height', 'min_thickness', 'max_thickness',
            'resolution', 'mesh_quality_multiplier', 'lithophane_coverage_angle',
            'top_margin', 'bottom_margin',
            'detail_enhancement', 'opencv_threads', 'gamma_override'
        }

        # Properly flatten nested dictionary
        kwargs = {}

        # Handle nested structure from YAML
        if 'cylinder' in data and isinstance(data['cylinder'], dict):
            kwargs.update(data['cylinder'])

        if 'printing' in data and isinstance(data['printing'], dict):
            kwargs.update(data['printing'])

        if 'quality' in data and isinstance(data['quality'], dict):
            kwargs.update(data['quality'])

        if 'margins' in data and isinstance(data['margins'], dict):
            kwargs.update(data['margins'])

        if 'performance' in data and isinstance(data['performance'], dict):
            kwargs.update(data['performance'])

        # Handle direct key-value pairs (for backwards compatibility)
        for key, value in data.items():
            if key not in ['cylinder', 'printing', 'quality', 'margins', 'performance']:
                kwargs[key] = value

        # Filter out any keys that don't match valid parameters
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_params}

        return cls(**filtered_kwargs)
    
    @classmethod
    def load_from_file(cls, config_path: Path) -> 'Settings':
        """
        Load settings from YAML configuration file.

        Args:
            config_path: Path to configuration file

        Returns:
            Settings instance
        """
        if not config_path.exists():
            return cls()  # Return defaults if no config file
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            return cls.from_dict(data)
        except (FileNotFoundError, yaml.YAMLError) as e:
            raise ValueError(f"Failed to load configuration from {config_path}: {e}")
    
    def save_to_file(self, config_path: Path) -> None:
        """
        Save settings to YAML configuration file.
        
        Args:
            config_path: Path to save configuration
        """
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(self.to_dict(), f, default_flow_style=False, allow_unicode=True)


class ConfigManager:
    """
    Configuration manager for application settings.
    
    Handles loading, saving, and validating configuration files.
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_dir: Directory for configuration files
        """
        if config_dir is None:
            config_dir = Path.cwd() / 'config'
        
        self.config_dir = config_dir
        self.config_file = config_dir / 'settings.yaml'
        self._settings: Optional[Settings] = None
    
    def get_settings(self) -> Settings:
        """
        Get current settings, loading from file if needed.

        Returns:
            Settings instance
        """
        if self._settings is None:
            self._settings = Settings.load_from_file(self.config_file)
        return self._settings
    
    def save_settings(self, settings: Settings) -> None:
        """
        Save settings to file.
        
        Args:
            settings: Settings to save
        """
        settings.save_to_file(self.config_file)
        self._settings = settings
    
    def reset_to_defaults(self) -> Settings:
        """
        Reset settings to defaults.

        Returns:
            Default Settings instance
        """
        self._settings = Settings()
        return self._settings
