#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Worker Thread for Lithophane Lamp Generator
Background processing with progress reporting and error handling.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

import numpy as np
import trimesh
from PyQt6.QtCore import QThread, pyqtSignal

from ..core.settings import Settings
from ..processing.image_processor import IntelligentImageProcessor, ImageProcessingError
from ..processing.cylinder_builder import CylinderBuilder, CylinderBuildError
from ..utils.validation import ValidationError


logger = logging.getLogger(__name__)


class WorkerError(Exception):
    """Custom exception for worker thread errors."""
    pass


class LithophaneLampWorker(QThread):
    """
    Background worker for lithophane lamp creation.
    
    Handles the complete pipeline from image processing to STL export
    while providing progress updates and comprehensive error handling.
    """
    
    # Qt signals for communication with main thread
    progress_updated = pyqtSignal(int, str)  # percentage, status_message
    creation_completed = pyqtSignal(bool, str, dict)  # success, message, statistics
    
    def __init__(self, image_path: str, output_path: str, 
                 settings: Optional[Settings] = None):
        """
        Initialize worker thread.
        
        Args:
            image_path: Path to input image
            output_path: Path for output STL file
            settings: Settings (uses defaults if None)
        """
        super().__init__()
        
        self.image_path = image_path
        self.output_path = output_path
        self.settings = settings or Settings()
        self.start_time: Optional[datetime] = None
        self._is_cancelled = False

        self.logger = logging.getLogger(__name__)

        # Processing components
        self.image_processor: Optional[IntelligentImageProcessor] = None
        self.cylinder_builder: Optional[CylinderBuilder] = None
    
    def run(self) -> None:
        """
        Execute the complete lithophane creation pipeline.
        
        This method runs in a separate thread and communicates progress
        and results via Qt signals.
        """
        self.start_time = datetime.now()
        
        try:
            self.logger.info(f"Starting lithophane creation: {Path(self.image_path).name}")
            
            # Initialize processing components
            self._initialize_processors()
            
            # Stage 1: Image Analysis and Validation (0-15%)
            self.progress_updated.emit(5, "Validating image file...")
            self._validate_inputs()

            if self._check_cancelled():
                return

            self.progress_updated.emit(15, "Analyzing image characteristics...")

            # Stage 2: Image Processing (15-35%)
            self.progress_updated.emit(20, "Processing image for high quality...")
            thickness_map = self._process_image()

            if self._check_cancelled():
                return

            self.progress_updated.emit(35, "Image processing completed")

            # Stage 3: 3D Mesh Generation (35-85%)
            self.progress_updated.emit(40, "Building 3D cylinder with high quality...")
            mesh = self._build_cylinder(thickness_map)

            if self._check_cancelled():
                return

            self.progress_updated.emit(85, "3D mesh generation completed")

            # Stage 4: STL Export (85-100%)
            self.progress_updated.emit(90, "Exporting STL file ready for printing...")
            self._export_stl(mesh)
            
            self.progress_updated.emit(100, "Lithophane lamp completed successfully!")
            
            # Generate completion statistics
            statistics = self._generate_completion_statistics(mesh)
            success_message = self._format_success_message(statistics)
            
            # Signal successful completion
            self.creation_completed.emit(True, success_message, statistics)
            
        except (ValidationError, ImageProcessingError, CylinderBuildError, WorkerError) as e:
            self._handle_known_error(e)
            
        except Exception as e:
            self._handle_unexpected_error(e)
    
    def _initialize_processors(self) -> None:
        """Initialize image processor and cylinder builder."""
        try:
            self.image_processor = IntelligentImageProcessor(self.settings)
            self.cylinder_builder = CylinderBuilder(self.settings)

        except (ImportError, AttributeError, TypeError) as e:
            raise WorkerError(f"Failed to initialize processors: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error initializing processors: {e}", exc_info=True)
            raise WorkerError(f"Unexpected initialization error: {e}")
    
    def _validate_inputs(self) -> None:
        """
        Validate input parameters and files.
        
        Raises:
            ValidationError: If validation fails
        """
        # Validate image path
        image_path = Path(self.image_path)
        if not image_path.exists():
            raise ValidationError(f"Image file not found: {self.image_path}")
        
        if not image_path.is_file():
            raise ValidationError(f"Image path is not a file: {self.image_path}")
        
        # Validate output path
        output_path = Path(self.output_path)
        if not output_path.parent.exists():
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise ValidationError(f"Cannot create output directory: {e}")
        
        # Check write permissions
        try:
            # Test write access
            test_file = output_path.parent / ".write_test"
            test_file.touch()
            test_file.unlink()
        except (PermissionError, OSError) as e:
            raise ValidationError(f"No write permission for output directory: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error testing write permissions: {e}", exc_info=True)
            raise ValidationError(f"Cannot verify write permissions: {e}")
    
    def _process_image(self) -> np.ndarray:
        """
        Process image for lithophane creation.
        
        Returns:
            Thickness map array
            
        Raises:
            ImageProcessingError: If image processing fails
        """
        if not self.image_processor:
            raise WorkerError("Image processor not initialized")
        
        try:
            return self.image_processor.process_image_for_lithophane(self.image_path)
            
        except Exception as e:
            raise ImageProcessingError(f"Image processing failed: {e}")
    
    def _build_cylinder(self, thickness_map: np.ndarray) -> trimesh.Trimesh:
        """
        Build 3D cylinder mesh.
        
        Args:
            thickness_map: Processed thickness map
            
        Returns:
            3D mesh object
            
        Raises:
            CylinderBuildError: If cylinder building fails
        """
        if not self.cylinder_builder:
            raise WorkerError("Cylinder builder not initialized")
        
        try:
            return self.cylinder_builder.create_lithophane_cylinder(thickness_map)
            
        except Exception as e:
            raise CylinderBuildError(f"Cylinder building failed: {e}")
    
    def _export_stl(self, mesh: trimesh.Trimesh) -> None:
        """
        Export mesh to STL file.

        Args:
            mesh: 3D mesh to export

        Raises:
            WorkerError: If STL export fails
        """
        try:
            # Ensure output directory exists
            Path(self.output_path).parent.mkdir(parents=True, exist_ok=True)

            # Export mesh
            mesh.export(self.output_path)

            # Verify file was created
            if not Path(self.output_path).exists():
                raise WorkerError("STL file was not created")

            file_size = Path(self.output_path).stat().st_size
            if file_size == 0:
                raise WorkerError("STL file is empty")

            self.logger.info(f"STL exported successfully: {self.output_path}")

        except (IOError, OSError, PermissionError) as e:
            raise WorkerError(f"STL export failed (file I/O error): {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error during STL export: {e}", exc_info=True)
            raise WorkerError(f"STL export failed: {e}")
    
    def _generate_completion_statistics(self, mesh: trimesh.Trimesh) -> Dict[str, Any]:
        """
        Generate comprehensive completion statistics.
        
        Args:
            mesh: Generated mesh
            
        Returns:
            Dictionary with statistics
        """
        if not self.start_time:
            creation_time_seconds = 0
        else:
            creation_time = datetime.now() - self.start_time
            creation_time_seconds = creation_time.total_seconds()
        
        try:
            file_size_mb = Path(self.output_path).stat().st_size / (1024 * 1024)
        except:
            file_size_mb = 0
        
        angular_segments, height_segments = self.settings.get_mesh_resolution()
        
        statistics = {
            'vertices_count': len(mesh.vertices) if hasattr(mesh, 'vertices') else 0,
            'faces_count': len(mesh.faces) if hasattr(mesh, 'faces') else 0,
            'file_size_mb': file_size_mb,
            'creation_time_seconds': creation_time_seconds,
            'angular_segments': angular_segments,
            'height_segments': height_segments,
            'resolution_mm': self.settings.resolution,
            'thickness_range': f"{self.settings.min_thickness}-{self.settings.max_thickness}mm",
            'output_filename': Path(self.output_path).name,
            'cylinder_dimensions': f"⌀{self.settings.cylinder_diameter}mm × {self.settings.cylinder_height}mm",
            'wall_thickness': f"{self.settings.wall_thickness}mm"
        }
        
        # Add mesh-specific statistics if available
        if hasattr(mesh, 'volume') and mesh.volume > 0:
            statistics['volume_mm3'] = mesh.volume
            statistics['material_weight_g'] = (mesh.volume / 1000) * 1.24  # PLA density
        
        if hasattr(mesh, 'area') and mesh.area > 0:
            statistics['surface_area_mm2'] = mesh.area
        
        # Add printing estimates
        if self.cylinder_builder:
            try:
                print_estimates = self.cylinder_builder.estimate_print_time(mesh)
                statistics.update(print_estimates)
            except:
                pass
        
        return statistics
    
    def _format_success_message(self, stats: Dict[str, Any]) -> str:
        """
        Format comprehensive success message.
        
        Args:
            stats: Statistics dictionary
            
        Returns:
            Formatted success message
        """
        message = f"""*** Lithophane Lamp Completed Successfully! ***

PHYSICAL SPECIFICATIONS:
* Cylinder: {stats['cylinder_dimensions']}, hollow design
* Wall thickness: {stats['wall_thickness']}
* Lithophane coverage: {self.settings.lithophane_coverage_angle} degrees

TECHNICAL QUALITY:
* Resolution: {stats['resolution_mm']:.2f}mm (high quality)
* Mesh density: {stats['angular_segments']:,} x {stats['height_segments']:,} segments
* Geometry: {stats['vertices_count']:,} vertices, {stats['faces_count']:,} faces
* File size: {stats['file_size_mb']:.1f} MB

PRINT OPTIMIZATION:
* Thickness range: {stats['thickness_range']} (calibrated for white PLA)
* Layer height: {self.settings.layer_height}mm
* Optimized for 0.4mm nozzle
* Ready for LED integration (inner diameter: {self.settings.get_inner_radius()*2:.0f}mm)

Processing completed in {stats['creation_time_seconds']:.1f} seconds
Saved as: {stats['output_filename']}

Your premium lithophane lamp is ready for 3D printing!
The image will illuminate beautifully with LED backlighting."""
        
        # Add printing estimates if available
        if 'estimated_print_time_hours' in stats and stats['estimated_print_time_hours'] > 0:
            message += f"\n\nPRINTING ESTIMATES:\n"
            message += f"* Estimated print time: {stats['estimated_print_time_hours']:.1f} hours\n"
            if 'material_weight_g' in stats:
                message += f"* Material usage: ~{stats['material_weight_g']:.1f}g PLA\n"
            if 'layer_count' in stats:
                message += f"* Layer count: {stats['layer_count']:,} layers"
        
        return message
    
    def _handle_known_error(self, error: Exception) -> None:
        """
        Handle known error types with appropriate user messages.
        
        Args:
            error: Known error type
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        self.logger.error(f"{error_type}: {error_message}")
        
        # Create user-friendly error message
        if isinstance(error, ValidationError):
            user_message = f"Input Validation Error:\n{error_message}"
        elif isinstance(error, ImageProcessingError):
            user_message = f"Image Processing Error:\n{error_message}\n\nPlease try a different image or check image quality."
        elif isinstance(error, CylinderBuildError):
            user_message = f"3D Model Creation Error:\n{error_message}\n\nThis may be due to complex image features or system limitations."
        else:
            user_message = f"Processing Error:\n{error_message}"
        
        self.creation_completed.emit(False, user_message, {})
    
    def _handle_unexpected_error(self, error: Exception) -> None:
        """
        Handle unexpected errors with comprehensive logging.
        
        Args:
            error: Unexpected error
        """
        self.logger.error(f"Unexpected error in worker thread: {error}", exc_info=True)
        
        error_message = f"""Unexpected Error Occurred:
{str(error)}

This appears to be an internal error. Please try again or contact support if the problem persists.

Technical details have been logged for debugging."""
        
        self.creation_completed.emit(False, error_message, {})
    
    def _check_cancelled(self) -> bool:
        """
        Check if cancellation was requested.

        Returns:
            True if cancelled, False otherwise
        """
        if self._is_cancelled or self.isInterruptionRequested():
            self.logger.info("Worker thread cancelled by user")
            self.creation_completed.emit(False, "Operation cancelled by user", {})
            return True
        return False

    def cancel(self) -> None:
        """
        Request graceful cancellation of worker thread.

        The thread will stop at the next cancellation check point.
        This is safer than terminate() as it allows cleanup.
        """
        self._is_cancelled = True
        self.requestInterruption()
        self.logger.info("Worker thread cancellation requested")

    def stop(self) -> None:
        """
        Request worker thread to stop (alias for cancel).

        Note: This is a cooperative stop - the thread will finish the current
        operation before stopping.
        """
        self.cancel()


class ProgressTracker:
    """
    Helper class for tracking progress across multiple stages.
    """
    
    def __init__(self, worker: LithophaneLampWorker):
        """
        Initialize progress tracker.
        
        Args:
            worker: Worker thread to send progress updates to
        """
        self.worker = worker
        self.stage_ranges = {
            'validation': (0, 15),
            'image_processing': (15, 35),
            'mesh_generation': (35, 85),
            'export': (85, 100)
        }
        self.current_stage = 'validation'
        self.stage_progress = 0
    
    def set_stage(self, stage: str) -> None:
        """Set current processing stage."""
        if stage in self.stage_ranges:
            self.current_stage = stage
            self.stage_progress = 0
    
    def update_progress(self, stage_percent: float, message: str) -> None:
        """
        Update progress within current stage.
        
        Args:
            stage_percent: Progress within current stage (0-100)
            message: Status message
        """
        start, end = self.stage_ranges.get(self.current_stage, (0, 100))
        overall_percent = start + (stage_percent / 100) * (end - start)
        
        self.worker.progress_updated.emit(int(overall_percent), message)