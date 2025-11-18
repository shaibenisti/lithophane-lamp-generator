#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Constants Module for Lithophane Lamp Generator
Centralized definitions for magic numbers and configuration values.
"""

# ===== 3D Mesh Generation Constants =====

# Curvature compensation
CURVATURE_COMPENSATION_FACTOR = 0.03
CURVATURE_ANGLE_SCALE = 0.8

# Mesh validation thresholds
MESH_MIN_VERTEX_COUNT = 100
MESH_MAX_VERTEX_COUNT = 500000

# ===== Material Constants =====

# PLA material properties
PLA_DENSITY_G_CM3 = 1.24  # grams per cubic centimeter

# Printing estimates
PRINT_TIME_FACTOR_HOURS_PER_CM3 = 0.5  # Approximate print time
PRINT_TIME_MINIMUM_HOURS = 2.0  # Minimum estimated print time

# ===== Histogram Analysis Constants =====

HISTOGRAM_BINS = 256
HISTOGRAM_RANGE = [0, 256]
HISTOGRAM_SHADOW_CUTOFF = 64
HISTOGRAM_HIGHLIGHT_CUTOFF = 192


# ===== Default Settings =====

# Default cylinder dimensions (mm)
DEFAULT_CYLINDER_DIAMETER = 60.0
DEFAULT_CYLINDER_HEIGHT = 130.0
DEFAULT_WALL_THICKNESS = 2.0

# Default lithophane parameters
DEFAULT_MIN_THICKNESS = 0.5
DEFAULT_MAX_THICKNESS = 2.2
DEFAULT_RESOLUTION = 0.08
DEFAULT_LITHOPHANE_COVERAGE_ANGLE = 190.0

# Default margins
DEFAULT_BOTTOM_MARGIN = 0.0
DEFAULT_TOP_MARGIN = 0.0

# Default printing parameters
DEFAULT_LAYER_HEIGHT = 0.12
DEFAULT_NOZZLE_DIAMETER = 0.4

# ===== Logging Constants =====

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# ===== UI Constants =====

# Progress stages
PROGRESS_VALIDATION = (0, 15)
PROGRESS_IMAGE_PROCESSING = (15, 35)
PROGRESS_MESH_GENERATION = (35, 85)
PROGRESS_EXPORT = (85, 100)

# Status update intervals
STATUS_UPDATE_INTERVAL_MS = 100

# ===== Mesh Resolution Constants =====

# Angular segments (circumference resolution)
MESH_ANGULAR_SEGMENTS_MIN = 800
MESH_ANGULAR_SEGMENTS_MAX = 1400

# Height segments (vertical resolution)
MESH_HEIGHT_SEGMENTS_MIN = 600
MESH_HEIGHT_SEGMENTS_MAX = 1200

# Resolution calculation multiplier
MESH_RESOLUTION_MULTIPLIER = 0.7

# ===== Filename Display Constants =====

# Maximum filename length for GUI display
MAX_FILENAME_DISPLAY_LENGTH = 50
MIN_PRINTABLE_CHAR_CODE = 32

# ===== Worker Thread Constants =====

# Graceful shutdown timeout (milliseconds)
WORKER_SHUTDOWN_TIMEOUT_MS = 3000
