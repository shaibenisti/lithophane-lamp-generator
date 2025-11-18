#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Cylinder Builder for Lithophane Lamp Generator
High-quality 3D mesh generation for lithophane cylinders.
"""

import math
import logging
import numpy as np
import trimesh
from typing import Tuple
from scipy.interpolate import RegularGridInterpolator
import cv2

from ..core.settings import Settings
from ..core import constants as const


logger = logging.getLogger(__name__)


class CylinderBuildError(Exception):
    """Custom exception for cylinder building errors."""
    pass


class CylinderBuilder:
    """
    High-quality cylinder builder for lithophane lamps.
    
    Creates hollow cylinders with integrated lithophane surfaces
    optimized for 3D printing and LED illumination.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize cylinder builder.
        
        Args:
            settings: Settings configuration
        """
        self.settings = settings
        self.logger = logging.getLogger(__name__)
    
    def create_lithophane_cylinder(self, thickness_map: np.ndarray) -> trimesh.Trimesh:
        """
        Create high quality lithophane cylinder.
        
        Args:
            thickness_map: 2D array of thickness values in millimeters
            
        Returns:
            High-quality trimesh object ready for STL export
            
        Raises:
            CylinderBuildError: If cylinder creation fails
        """
        try:
            self.logger.info("Creating premium lithophane cylinder...")
            
            # Calculate cylinder parameters
            outer_radius = self.settings.cylinder_diameter / 2
            inner_radius = self.settings.get_inner_radius()
            
            # Lithophane coverage parameters
            lithophane_angle_rad = math.radians(self.settings.lithophane_coverage_angle)
            start_angle = -lithophane_angle_rad / 2
            end_angle = lithophane_angle_rad / 2
            
            # Vertical positioning
            lithophane_start_z = self.settings.bottom_margin
            lithophane_end_z = self.settings.cylinder_height - self.settings.top_margin
            
            # Mesh resolution
            angular_segments, height_segments = self.settings.get_mesh_resolution()
            
            self.logger.info(f"Mesh resolution: {angular_segments} × {height_segments} segments")
            
            # Create precision interpolator for smooth thickness mapping
            interpolator = self._create_precision_interpolator(thickness_map)
            
            # Generate vertices with high precision
            vertices = self._generate_premium_vertices(
                interpolator, outer_radius, inner_radius,
                start_angle, end_angle, lithophane_start_z, lithophane_end_z,
                angular_segments, height_segments
            )
            
            # Generate optimized face topology
            faces = self._generate_optimized_faces(angular_segments, height_segments)
            
            # Create and validate mesh
            mesh = self._create_validated_premium_mesh(vertices, faces)
            
            self.logger.info(f"Cylinder completed: {len(vertices)} vertices, {len(faces)} faces")
            
            return mesh
            
        except (ValueError, TypeError, AttributeError) as e:
            self.logger.error(f"Cylinder creation failed (invalid parameters): {e}", exc_info=True)
            raise CylinderBuildError(f"Failed to create cylinder (parameter error): {e}")
        except (ImportError, ModuleNotFoundError) as e:
            self.logger.error(f"Cylinder creation failed (missing dependencies): {e}", exc_info=True)
            raise CylinderBuildError(f"Failed to create cylinder (missing library): {e}")
        except Exception as e:
            self.logger.error(f"Cylinder creation failed (unexpected error): {e}", exc_info=True)
            raise CylinderBuildError(f"Failed to create cylinder: {e}")
    
    def _create_precision_interpolator(self, thickness_map: np.ndarray) -> RegularGridInterpolator:
        """
        Create high-precision interpolator for smooth thickness mapping.
        
        Args:
            thickness_map: Input thickness map
            
        Returns:
            Configured interpolator for smooth thickness values
        """
        img_height, img_width = thickness_map.shape

        # Add minimal padding for interpolation (edge blending removed)
        pad_size = 2  # Minimal padding for interpolator
        padded_map = np.pad(thickness_map, pad_size, mode='edge')

        # Create coordinate arrays
        y_coords = np.linspace(-pad_size, img_height + pad_size - 1, padded_map.shape[0])
        x_coords = np.linspace(-pad_size, img_width + pad_size - 1, padded_map.shape[1])
        
        # Create high-quality interpolator
        return RegularGridInterpolator(
            (y_coords, x_coords), padded_map,
            method='cubic', bounds_error=False,
            fill_value=self.settings.min_thickness
        )
    
    def _generate_premium_vertices(self, interpolator: RegularGridInterpolator,
                                 outer_radius: float, inner_radius: float,
                                 start_angle: float, end_angle: float,
                                 lithophane_start_z: float, lithophane_end_z: float,
                                 angular_segments: int, height_segments: int) -> np.ndarray:
        """
        Generate high-precision vertices for the cylinder mesh.
        
        Args:
            interpolator: Thickness interpolator
            outer_radius: Base outer radius
            inner_radius: Inner radius
            start_angle: Lithophane start angle
            end_angle: Lithophane end angle
            lithophane_start_z: Lithophane start height
            lithophane_end_z: Lithophane end height
            angular_segments: Number of angular segments
            height_segments: Number of height segments
            
        Returns:
            Array of vertex coordinates
        """
        vertices = []
        
        angular_step = 2 * math.pi / angular_segments
        height_step = self.settings.cylinder_height / height_segments
        
        # Get interpolator dimensions for mapping
        img_height, img_width = interpolator.values.shape
        lithophane_angle_range = end_angle - start_angle
        lithophane_height_range = lithophane_end_z - lithophane_start_z
        
        # Generate vertices layer by layer
        for height_idx in range(height_segments + 1):
            z_position = height_idx * height_step

            for angle_idx in range(angular_segments):
                current_angle = angle_idx * angular_step

                # Normalize angle to [-π, π] range
                normalized_angle = current_angle if current_angle <= math.pi else current_angle - 2*math.pi

                # Start with base radii - consistent calculation for both areas
                effective_inner_radius = inner_radius

                # Determine thickness for this position
                # Use wall_thickness as base, or lithophane thickness if in lithophane area
                wall_thickness = outer_radius - inner_radius
                effective_thickness = wall_thickness  # Default for non-lithophane areas

                # Check if this position should have lithophane thickness
                if (lithophane_start_z <= z_position <= lithophane_end_z and
                    start_angle <= normalized_angle <= end_angle):

                    # Map to texture coordinates (with division by zero protection)
                    u_coordinate = (normalized_angle - start_angle) / lithophane_angle_range if lithophane_angle_range > 0 else 0.0
                    v_coordinate = (z_position - lithophane_start_z) / lithophane_height_range if lithophane_height_range > 0 else 0.0

                    # Convert to image coordinates
                    img_x = u_coordinate * (img_width - 1)
                    img_y = (1.0 - v_coordinate) * (img_height - 1)  # Flip Y for correct orientation

                    # Sample thickness from interpolator
                    thickness_value = float(interpolator([img_y, img_x]))

                    # Apply curvature compensation for better light distribution
                    curvature_compensation = 1.0 + const.CURVATURE_COMPENSATION_FACTOR * math.cos(normalized_angle * const.CURVATURE_ANGLE_SCALE)
                    effective_thickness = thickness_value * curvature_compensation

                # FIXED: Consistent radius calculation for both lithophane and non-lithophane areas
                # Inner surface stays constant, outer surface varies based on thickness
                # This ensures no discontinuity at boundaries (prevents non-manifold edges)
                effective_outer_radius = inner_radius + effective_thickness

                # Generate outer vertex
                x_outer = effective_outer_radius * math.cos(current_angle)
                y_outer = effective_outer_radius * math.sin(current_angle)
                vertices.append([x_outer, y_outer, z_position])

                # Generate inner vertex
                x_inner = effective_inner_radius * math.cos(current_angle)
                y_inner = effective_inner_radius * math.sin(current_angle)
                vertices.append([x_inner, y_inner, z_position])
        
        return np.array(vertices)
    
    def _generate_optimized_faces(self, angular_segments: int, height_segments: int) -> np.ndarray:
        """
        Generate optimized face topology for smooth surfaces.
        
        Args:
            angular_segments: Number of angular segments
            height_segments: Number of height segments
            
        Returns:
            Array of face indices
        """
        faces = []
        
        # Generate faces between layers
        for height_idx in range(height_segments):
            for angle_idx in range(angular_segments):
                # Calculate vertex indices
                current_layer_base = height_idx * angular_segments * 2
                next_layer_base = (height_idx + 1) * angular_segments * 2
                
                current_angle_base = angle_idx * 2
                next_angle_base = ((angle_idx + 1) % angular_segments) * 2
                
                # Vertex indices for current quad
                p1_outer = current_layer_base + current_angle_base
                p1_inner = current_layer_base + current_angle_base + 1
                p2_outer = current_layer_base + next_angle_base
                p2_inner = current_layer_base + next_angle_base + 1
                p3_outer = next_layer_base + current_angle_base
                p3_inner = next_layer_base + current_angle_base + 1
                p4_outer = next_layer_base + next_angle_base
                p4_inner = next_layer_base + next_angle_base + 1
                
                # Outer surface faces (counter-clockwise for outward normals)
                faces.extend([
                    [p1_outer, p2_outer, p4_outer],
                    [p1_outer, p4_outer, p3_outer]
                ])
                
                # Inner surface faces (clockwise for inward normals)
                faces.extend([
                    [p1_inner, p3_inner, p4_inner],
                    [p1_inner, p4_inner, p2_inner]
                ])
        
        # Note: No caps needed for hollow cylinder design
        # Caps would be added here if solid cylinder was required

        return np.array(faces)

    def _create_validated_premium_mesh(self, vertices: np.ndarray, faces: np.ndarray) -> trimesh.Trimesh:
        """
        Create and validate high quality mesh.
        
        Args:
            vertices: Vertex array
            faces: Face array
            
        Returns:
            Validated and optimized trimesh object
            
        Raises:
            CylinderBuildError: If mesh validation fails
        """
        try:
            # Create initial mesh
            mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
            
            # Clean up mesh geometry
            mesh.remove_duplicate_faces()
            mesh.remove_degenerate_faces()
            mesh.remove_unreferenced_vertices()
            
            # Fix mesh normals
            mesh.fix_normals()
            
            # Apply smoothing if available and beneficial
            try:
                if hasattr(mesh, 'smoothed'):
                    smoothed_mesh = mesh.smoothed()
                    if (hasattr(smoothed_mesh, 'is_valid') and smoothed_mesh.is_valid and
                        len(smoothed_mesh.vertices) > 0 and len(smoothed_mesh.faces) > 0):
                        mesh = smoothed_mesh
                        self.logger.info("Applied mesh smoothing")
            except Exception as e:
                self.logger.warning(f"Mesh smoothing failed, using original: {e}")
            
            # Try to make mesh watertight
            if not mesh.is_watertight:
                try:
                    mesh.fill_holes()
                    if mesh.is_watertight:
                        self.logger.info("Successfully filled mesh holes")
                except Exception as e:
                    self.logger.warning(f"Failed to fill holes: {e}")
            
            # Final validation
            if len(mesh.vertices) == 0 or len(mesh.faces) == 0:
                raise CylinderBuildError("Generated mesh has no geometry data")
            
            # Check mesh quality
            self._validate_mesh_quality(mesh)
            
            return mesh
            
        except (ValueError, AttributeError) as e:
            raise CylinderBuildError(f"Mesh validation failed (invalid mesh data): {e}")
        except Exception as e:
            self.logger.error(f"Mesh validation failed unexpectedly: {e}", exc_info=True)
            raise CylinderBuildError(f"Mesh validation failed: {e}")
    
    def _validate_mesh_quality(self, mesh: trimesh.Trimesh) -> None:
        """
        Validate mesh quality and log metrics.
        
        Args:
            mesh: Mesh to validate
        """
        # Basic validation
        vertex_count = len(mesh.vertices)
        face_count = len(mesh.faces)

        if vertex_count < const.MESH_MIN_VERTEX_COUNT:
            self.logger.warning("Very low vertex count - mesh may be too simple")
        elif vertex_count > const.MESH_MAX_VERTEX_COUNT:
            self.logger.warning("Very high vertex count - file may be large")
        
        # Check for mesh issues
        if hasattr(mesh, 'is_valid') and not mesh.is_valid:
            self.logger.warning("Mesh validation indicates potential issues")
        
        if hasattr(mesh, 'is_watertight') and not mesh.is_watertight:
            self.logger.warning("Mesh is not watertight - may cause printing issues")
        
        # Calculate and log mesh statistics
        if hasattr(mesh, 'bounds'):
            bounds = mesh.bounds
            dimensions = bounds[1] - bounds[0]
            self.logger.info(
                f"Mesh dimensions: {dimensions[0]:.1f} × {dimensions[1]:.1f} × {dimensions[2]:.1f} mm"
            )
        
        if hasattr(mesh, 'volume') and mesh.volume > 0:
            self.logger.info(f"Mesh volume: {mesh.volume:.2f} mm³")
        
        if hasattr(mesh, 'area') and mesh.area > 0:
            self.logger.info(f"Mesh surface area: {mesh.area:.2f} mm²")
    
    def estimate_print_time(self, mesh: trimesh.Trimesh) -> dict:
        """
        Estimate 3D printing time and material usage.
        
        Args:
            mesh: Mesh to analyze
            
        Returns:
            Dictionary with printing estimates
        """
        estimates = {
            'volume_mm3': 0,
            'material_weight_g': 0,
            'estimated_print_time_hours': 0,
            'layer_count': 0
        }
        
        try:
            if hasattr(mesh, 'volume') and mesh.volume > 0:
                # Volume calculations
                estimates['volume_mm3'] = mesh.volume

                # PLA density from constants
                estimates['material_weight_g'] = (mesh.volume / 1000) * const.PLA_DENSITY_G_CM3
                
                # Estimate layer count
                if hasattr(mesh, 'bounds'):
                    height_mm = mesh.bounds[1][2] - mesh.bounds[0][2]
                    estimates['layer_count'] = int(height_mm / self.settings.layer_height)
                
                # Rough print time estimate (very approximate)
                # Based on typical speeds for detailed prints
                estimated_hours = (mesh.volume / 1000) * const.PRINT_TIME_FACTOR_HOURS_PER_CM3
                estimates['estimated_print_time_hours'] = max(const.PRINT_TIME_MINIMUM_HOURS, estimated_hours)
                
        except Exception as e:
            self.logger.warning(f"Could not estimate print parameters: {e}")
        
        return estimates