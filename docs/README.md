# Premium Lithophane Lamp Generator

**Version:** 1.0
**Platform:** Windows (tested), Cross-platform compatible
**Language:** Python 3.8+

## Overview

The Premium Lithophane Lamp Generator is a professional desktop application for creating 3D-printable lithophane lamp cylinders from photographs. Using advanced image processing with face detection, intelligent enhancement pipelines, and high-precision 3D mesh generation, it produces STL files optimized for FDM printing with LED integration.

## What is a Lithophane?

A lithophane is a 3D object where varying wall thickness creates an image when backlit. Thin areas allow more light through (bright), while thick areas block light (dark). The result is a stunning illuminated photograph perfect for gifts and home decor.

## Key Features

### Intelligent Image Processing
- **Automatic Image Rescue** - Fixes low-resolution, dark, compressed, or problematic images
- **Face Detection** - Optimizes portraits with special processing for faces
- **Image Classification** - Automatically detects underexposed, overexposed, low-contrast images
- **Smart Enhancement** - Applies appropriate adjustments based on image characteristics
- **Faithful Representation** - Preserves original image character without over-brightening

### Modern User Interface
- **Bilingual Support** - Hebrew (RTL) and English (LTR) with seamless switching
- **Modern Segmented Control** - iOS-style language selector
- **Dark Theme** - Professional Claude.ai-inspired styling
- **Real-time Progress** - Live status updates during processing
- **Activity Log** - Comprehensive logging of all operations

### Professional Quality Output
- **High-Precision Mesh** - Up to 1,400 × 1,200 segments for smooth surfaces
- **Optimized Topology** - Clean quad-based triangulation
- **Watertight Geometry** - Print-ready STL files with no manifold errors
- **Accurate Dimensions** - Precise millimeter-scale output

### Physical Specifications (Default)
- **Cylinder Dimensions:** Ø60mm × 130mm
- **Wall Thickness:** 2.0mm hollow design
- **Lithophane Coverage:** 200° around circumference
- **Thickness Range:** 0.5mm (brightest) to 2.2mm (darkest)
- **Inner Diameter:** 56mm (for LED strip integration)
- **Resolution:** 0.08mm-0.12mm processing resolution

## Installation

### Requirements
- Python 3.8 or higher
- Windows 10/11 (or Linux/macOS with Qt6 support)
- 4GB RAM minimum, 8GB recommended
- 500MB free disk space

### Quick Start

1. **Clone or download the repository**
   ```bash
   git clone <repository-url>
   cd "STL softwhere"
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python main.py
   # or
   run.bat  (Windows)
   ```

## Usage

### Basic Workflow

1. **Launch Application** - Run `python main.py` or `run.bat`
2. **Select Language** - Click Hebrew (עברית) or English in the top-right segmented control
3. **Choose Image** - Click "Select Image" and pick your photo (JPG, PNG, BMP, TIFF, GIF)
4. **Select Output** - Click "Select Save Location" and choose where to save the STL file
5. **Create Lamp** - Click "Create Lamp" and wait for processing (1-3 minutes)
6. **Print** - Load the STL file into your slicer and print!

### Supported Image Formats
- JPEG/JPG (including heavily compressed)
- PNG (with transparency support)
- BMP
- TIFF
- GIF

### Best Practices for Images

**Ideal Images:**
- Portraits with clear faces (300×300px minimum)
- High-contrast photos
- Images with good lighting
- Resolution: 800×800px or higher recommended

**Challenging Images (But We Handle Them!):**
- Low resolution (200-800px) - automatically upscaled
- Dark/underexposed photos - exposure correction applied
- Heavily compressed JPEGs - denoising applied
- Backlit photos - intelligent shadow lifting
- Old vintage photos - restoration processing

### What NOT to Use
- Extremely busy images with too much detail
- Images with critical text (may not be readable)
- Very high resolution images (>4000px) - will be downscaled

## Output

The application generates a **print-ready STL file** containing:
- Cylindrical base and top
- Hollow interior (56mm diameter) for LED insertion
- Lithophane panel wrapped around 200° of the cylinder
- Smooth transitions at lithophane edges
- Optimized mesh for clean printing

### Printing Recommendations
- **Material:** White PLA (translucent filaments work best)
- **Nozzle:** 0.4mm
- **Layer Height:** 0.12mm or finer for best detail
- **Wall Lines:** 2-3 perimeters
- **Infill:** Not critical for lithophane area (20% for base/top)
- **Speed:** Slow (30-40mm/s) for lithophane section
- **Supports:** Generally not needed for cylinder design

### LED Integration
The hollow interior (56mm diameter) is sized for:
- LED strip coils
- Battery-powered LED strings
- USB-powered LED modules
- Tea light candles (flameless recommended)

## Configuration

Configuration files are located in:
- `config/settings.yaml` - Main settings
- `.env` - Environment variables (create from template)

See [CONFIGURATION.md](CONFIGURATION.md) for detailed settings documentation.

## Project Structure

```
E:\STL softwhere\
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── run.bat                # Windows launcher
├── config/
│   └── settings.yaml      # Configuration file
├── src/
│   ├── core/              # Core settings and constants
│   ├── gui/               # PyQt6 UI components
│   ├── processing/        # Image and 3D processing
│   └── utils/             # Helper utilities
└── docs/                  # Documentation
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed code structure.

## Troubleshooting

### Application Won't Start
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Check Python version
python --version  # Should be 3.8+
```

### "Missing Dependencies" Error
```bash
pip install PyQt6 opencv-python numpy trimesh scipy PyYAML python-dotenv
```

### Face Detection Not Working
Face detection uses OpenCV's built-in Haar Cascade. Verify installation:
```python
import cv2
print(cv2.data.haarcascades)
```

### STL Export Fails
- Check disk space
- Verify write permissions in output directory
- Ensure output path doesn't contain special characters

### Memory Issues
Edit `.env` and reduce:
```
MAX_MEMORY_GB=4
OPENCV_THREADS=2
```

## Support & Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - Code structure and design patterns
- [GUI.md](GUI.md) - UI components and customization
- [CONFIGURATION.md](CONFIGURATION.md) - Settings and environment variables

## License

© 2025 Premium Lithophane Lamp Generator. All rights reserved.

## Credits

**Technologies Used:**
- PyQt6 - Modern GUI framework
- OpenCV - Image processing and computer vision
- NumPy - Numerical operations
- Trimesh - 3D mesh manipulation
- SciPy - Scientific computing and interpolation

---

**Made with precision and care for creating beautiful illuminated memories.**
