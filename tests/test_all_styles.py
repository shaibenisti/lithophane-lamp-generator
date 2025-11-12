#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test All Processing Styles
Generates lithophanes with all 5 styles for comparison
"""

import sys
import yaml
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import cv2
import numpy as np
from processing.simple_processor import SimpleImageProcessor
from processing.thickness_mapper import ThicknessMapper
from processing.cylinder_builder import CylinderBuilder
from core.settings import Settings
from utils.heic_loader import load_image_with_heic_support

def load_style(style_path):
    """Load style configuration from YAML."""
    with open(style_path, 'r') as f:
        return yaml.safe_load(f)

def process_with_style(image_path, style_config, output_path, settings):
    """Process image with specific style settings."""
    print(f"\n{'='*60}")
    print(f"Processing: {style_config['name']}")
    print(f"Description: {style_config['description']}")
    print(f"{'='*60}")

    # Load image
    image = load_image_with_heic_support(image_path)
    if len(image.shape) == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    print(f"Loaded: {image.shape[1]}×{image.shape[0]}")

    # Get target size
    target_width, target_height, _, _ = settings.get_lithophane_dimensions()
    target_size = (target_width, target_height)

    # Resize
    resized = cv2.resize(image, target_size, interpolation=cv2.INTER_LANCZOS4)
    print(f"Resized: {resized.shape[1]}×{resized.shape[0]}")

    # Apply CLAHE if enabled
    result = resized
    if style_config['clahe']['enabled']:
        clahe = cv2.createCLAHE(
            clipLimit=style_config['clahe']['clip_limit'],
            tileGridSize=tuple(style_config['clahe']['tile_size'])
        )
        result = clahe.apply(result)
        print(f"CLAHE: clip={style_config['clahe']['clip_limit']}, tiles={style_config['clahe']['tile_size']}")
    else:
        print("CLAHE: disabled")

    # Apply bilateral filter if enabled
    if style_config['bilateral_filter']['enabled']:
        result = cv2.bilateralFilter(
            result,
            d=style_config['bilateral_filter']['diameter'],
            sigmaColor=style_config['bilateral_filter']['sigma_color'],
            sigmaSpace=style_config['bilateral_filter']['sigma_space']
        )
        print(f"Bilateral: d={style_config['bilateral_filter']['diameter']}, "
              f"sigma=({style_config['bilateral_filter']['sigma_color']}, "
              f"{style_config['bilateral_filter']['sigma_space']})")
    else:
        print("Bilateral: disabled")

    # Create thickness map
    thickness_mapper = ThicknessMapper(settings)
    thickness_map = thickness_mapper.create_thickness_map(result)
    print(f"Thickness map: {thickness_map.shape}")

    # Build cylinder
    cylinder_builder = CylinderBuilder(settings)
    mesh = cylinder_builder.create_lithophane_cylinder(thickness_map)
    print(f"Mesh: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")

    # Export
    mesh.export(output_path)
    print(f"✓ Exported: {output_path}")
    print(f"Note: {style_config['notes']}")

def main():
    """Generate all 5 style variations."""
    # Paths
    test_dir = Path(__file__).parent
    styles_dir = test_dir / 'styles'
    images_dir = test_dir / 'images'
    output_dir = test_dir / 'output'

    # Create output directory
    output_dir.mkdir(exist_ok=True)

    # Input image
    image_path = images_dir / 'SABA.jpg'

    if not image_path.exists():
        print(f"ERROR: Test image not found: {image_path}")
        return

    # Load settings
    settings = Settings()

    # Get all style files
    style_files = sorted(styles_dir.glob('*.yaml'))

    print(f"\n{'#'*60}")
    print(f"# LITHOPHANE STYLE COMPARISON TEST")
    print(f"# Input: {image_path.name}")
    print(f"# Styles: {len(style_files)}")
    print(f"{'#'*60}")

    # Process each style
    for style_file in style_files:
        style_config = load_style(style_file)
        style_name = style_file.stem  # e.g., "1_minimal"
        output_path = output_dir / f"saba_{style_name}.stl"

        try:
            process_with_style(str(image_path), style_config, str(output_path), settings)
        except Exception as e:
            print(f"✗ ERROR processing {style_name}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*60}")
    print(f"✓ ALL STYLES COMPLETED")
    print(f"✓ Output directory: {output_dir}")
    print(f"✓ Compare the STL files in your slicer!")
    print(f"={'='*60}\n")

if __name__ == '__main__':
    main()
