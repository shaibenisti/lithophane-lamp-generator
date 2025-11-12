# Lithophane Lamp Generator

**Professional desktop application for creating 3D-printable lithophane lamp cylinders from images.**

## Overview

The Lithophane Lamp Generator is a PyQt6-based desktop application that converts photographs into cylindrical lithophane lamps ready for 3D printing. The system uses optimized image processing and high-precision 3D mesh generation to create STL files that, when printed in white PLA and backlit with LEDs, beautifully display your images.

## Key Features

- **Zero-Configuration Interface** - No settings to adjust, optimized parameters built-in
- **Bilingual Support** - Hebrew and English UI with RTL/LTR layout support
- **Intelligent Processing** - Automatically optimized for smooth, clean results
- **High-Precision 3D Meshes** - Print-ready STL files with no manifold errors
- **Background Processing** - Non-blocking operation with real-time progress updates
- **LED-Optimized Design** - Hollow cylinder with perfect inner diameter for LED strips

## Physical Specifications

All dimensions are pre-configured for optimal results:

- **Cylinder Size**: Ø60mm × 130mm tall
- **Wall Thickness**: 2.0mm (hollow design)
- **Lithophane Coverage**: 190° around the circumference
- **Thickness Range**: 0.5mm (bright areas) to 2.2mm (dark areas)
- **Inner Diameter**: 56mm (for LED strip integration)
- **Print Resolution**: 0.08mm processing resolution

## Quick Start

### Installation

**Requirements:**
- Python 3.8 or higher
- Windows (tested), macOS, or Linux

**Install dependencies:**
```bash
pip install -r requirements.txt
```

### Running the Application

**Windows:**
```bash
run.bat
```

**macOS/Linux:**
```bash
python main.py
```

### Creating Your First Lithophane

1. **Launch the application**
2. **Click "Select Image"** - Choose a JPG, PNG, or other image file
3. **Wait for processing** - Progress bar shows real-time status
4. **Save the STL** - Choose output location for your 3D model
5. **3D print** - Load STL in your slicer, print in white PLA
6. **Add LEDs** - Insert LED strip inside the hollow cylinder
7. **Enjoy!** - Your image illuminates beautifully when backlit

## Supported Image Formats

- **JPEG/JPG** - Standard photos
- **PNG** - Transparent backgrounds supported
- **BMP** - Bitmap images
- **TIFF** - High-quality formats
- **HEIC** - iPhone photos (requires pillow-heif)

## 3D Printing Recommendations

### Optimal Slicer Settings

- **Material**: White PLA (1.75mm)
- **Layer Height**: 0.12mm (high quality) or 0.16mm (balanced)
- **Nozzle**: 0.4mm
- **Wall Lines**: 2-3 perimeters
- **Infill**: 15-20% (structural support only)
- **Speed**: 40-50 mm/s (slow for quality)
- **Cooling**: 100% fan after first layer

### Print Orientation

- **Stand vertically** - Cylinder axis along Z-axis
- **Use supports** - For overhangs if needed
- **Brim recommended** - For better bed adhesion

### LED Integration

- **LED Strip**: 12V or 5V LED strip, warm white (2700-3000K)
- **Inner Diameter**: 56mm accommodates most LED strips
- **Power**: USB-powered or 12V adapter depending on strip

## Project Structure

```
lamp-generator/
├── main.py                 # Application entry point
├── run.bat                 # Windows launcher
├── requirements.txt        # Python dependencies
├── config/
│   └── settings.yaml       # Configuration file
├── src/
│   ├── gui/                # User interface (PyQt6)
│   │   ├── main_window.py
│   │   ├── language_manager.py
│   │   ├── success_dialog.py
│   │   └── animations.py
│   ├── processing/         # Image and 3D processing
│   │   ├── image_processor.py
│   │   ├── simple_processor.py
│   │   ├── thickness_mapper.py
│   │   └── cylinder_builder.py
│   ├── core/               # Core configuration
│   │   ├── settings.py
│   │   └── constants.py
│   └── utils/              # Utilities
│       ├── worker.py
│       ├── validation.py
│       ├── image_utils.py
│       └── heic_loader.py
├── docs/                   # Documentation
└── tests/                  # Testing resources
```

## Configuration

The application uses pre-optimized settings stored in `config/settings.yaml`. While these are already tuned for best results, advanced users can modify:

- **Resolution**: Processing precision (default: 0.08mm)
- **Mesh Quality**: Vertex density multiplier (default: 1.2)
- **Gamma Correction**: Tonal curve adjustment (default: 1.0)

## Technical Details

### Processing Pipeline

1. **Image Loading** - Multi-format support with HEIC compatibility
2. **Validation** - File format and dimension checks
3. **Grayscale Conversion** - Preserve tonal information
4. **Resizing** - Lanczos4 interpolation for quality
5. **Enhancement** - Light CLAHE with large tiles (smooth results)
6. **Smoothing** - Bilateral filter eliminates texture noise
7. **Thickness Mapping** - Grayscale → thickness values (0.5-2.2mm)
8. **3D Mesh Generation** - High-precision cylindrical mesh
9. **STL Export** - Print-ready 3D model file

### Why These Settings?

The application uses **Style #4 (Smooth)** processing parameters:

- **CLAHE**: Light enhancement (clip_limit=1.3) with large tiles (24×24) for smooth facial areas
- **Bilateral Filter**: Strong smoothing (d=7, sigma=60) to eliminate skin texture while preserving edges
- **Result**: Clean, professional lithophanes without noisy texture amplification

## Troubleshooting

### Common Issues

**"Image file not found" error:**
- Verify the file path is correct
- Check file permissions
- Ensure the file isn't open in another program

**STL file is empty or won't open:**
- Check available disk space
- Verify write permissions in output directory
- Try a different output location

**Processing takes too long:**
- Large images (>4000px) take longer - this is normal
- Background processing continues even if UI seems frozen
- Check `lamp_generator.log` for progress details

**3D print shows artifacts:**
- Lower print speed to 40 mm/s
- Increase layer cooling to 100%
- Reduce layer height to 0.12mm

## Support and Feedback

For issues, suggestions, or questions:

- Check the `lamp_generator.log` file for detailed error information
- Review the documentation in the `docs/` folder
- Ensure all dependencies are installed correctly

## License

Copyright © 2025 Shai Benisti

---

**Created with passion for transforming memories into illuminated art.**
