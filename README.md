# Lithophane Lamp Generator

A professional desktop application for creating premium lithophane lamps from images. This application converts images into 3D-printable STL files optimized for cylindrical lithophane lamps with LED backlighting.

## Features

### Core Functionality
- **Intelligent Image Processing**: Advanced image analysis and enhancement optimized for lithophane creation
- **Premium Quality Output**: High-resolution 3D mesh generation with professional print quality
- **Hollow Cylinder Design**: Optimized for LED integration with precise inner diameter (56mm)
- **Multi-language Support**: Hebrew and English interface
- **Real-time Progress Tracking**: Visual feedback during processing

### Image Processing Capabilities
- **Automatic Image Analysis**: Detects portrait photos, exposure levels, and image characteristics
- **Adaptive Enhancement**: 
  - Portrait optimization with face detection
  - Exposure correction for underexposed/overexposed images
  - Contrast enhancement for low-contrast images
  - Shadow/highlight recovery
- **Professional Quality Resize**: Multi-stage resizing with detail preservation
- **Format Support**: JPEG, PNG, BMP, TIFF, GIF

### 3D Generation Specifications
- **Cylinder Dimensions**: ⌀60mm × 130mm (customizable)
- **Wall Thickness**: 2.0mm (hollow design for LED integration)
- **Lithophane Coverage**: 220° around cylinder circumference
- **Resolution**: 0.12mm (premium quality)
- **Thickness Range**: 0.5mm - 2.2mm (calibrated for white PLA)
- **Mesh Quality**: High-density mesh with up to 1,400 angular segments

### Print Optimization
- **3D Printer Ready**: Optimized for Creality K2 Plus and similar FDM printers
- **Nozzle Size**: 0.4mm nozzle diameter
- **Layer Height**: 0.12mm recommended
- **Material**: White PLA recommended for optimal light transmission
- **LED Compatible**: 56mm inner diameter for LED strip integration

## Installation

### Prerequisites
- Python 3.8 or higher
- Windows 10/11 (primary platform)

### Required Dependencies
Install the required packages using pip:

```bash
pip install -r requirements.txt
```

## Usage

### Running the Application
```bash
python main.py
```

### Basic Workflow
1. **Launch Application**: Run the main.py file
2. **Select Image**: Click "Select Image" and choose your photo
3. **Choose Output Location**: Click "Select Save Location" for the STL file
4. **Create Lamp**: Click "Create Lamp" to start processing
5. **Wait for Completion**: Monitor progress and wait for completion message

### Language Selection
- Switch between Hebrew (עברית) and English using the dropdown in the top-right
- Default language is Hebrew

### Image Requirements
- **Supported Formats**: JPEG, PNG, BMP, TIFF, GIF
- **Resolution**: Any size (will be optimized automatically)
- **Type**: Color or grayscale images
- **Recommended**: Portrait photos with good contrast work best

## Technical Details

### Image Processing Pipeline
1. **Analysis Phase**: Automatic detection of image characteristics
2. **Enhancement Phase**: Adaptive processing based on image type
3. **Resize Phase**: Professional multi-stage resizing with detail preservation
4. **Thickness Mapping**: Conversion to calibrated thickness values

### 3D Generation Process
1. **Interpolation**: High-precision cubic interpolation for smooth surfaces
2. **Vertex Generation**: Premium quality mesh with optimized density
3. **Face Optimization**: Efficient triangulation for clean geometry
4. **Mesh Validation**: Automatic repair and optimization
5. **STL Export**: Industry-standard format ready for slicing

### Performance Specifications
- **Processing Time**: Typically 30-60 seconds for standard images
- **Memory Usage**: Optimized for efficiency with large images
- **Output File Size**: 1-5 MB typical STL file size
- **Mesh Density**: Up to 1,400×1,200 segments for maximum quality

## 3D Printing Guidelines

### Recommended Settings
- **Layer Height**: 0.12mm
- **Nozzle Temperature**: 210°C (white PLA)
- **Bed Temperature**: 60°C
- **Print Speed**: 30-50mm/s for quality
- **Infill**: 0% (hollow design)
- **Support**: Generally not required

### Post-Processing
1. Remove any support material if used
2. Light sanding of base if needed
3. Insert LED strip (warm white recommended)
4. Test lighting before final assembly

## LED Integration

### Recommended LED Specifications
- **Type**: Warm white LED strip (3000K-3500K)
- **Width**: Up to 10mm wide strips
- **Length**: 150-180mm to cover full height
- **Power**: Low power (2-5W) for optimal results
- **Control**: Dimmable controller recommended

### Assembly Tips
- Insert LED strip vertically inside cylinder
- Use diffusion material at base if needed
- Ensure even light distribution
- Test before permanent installation

## Troubleshooting

### Common Issues
- **Image Not Loading**: Ensure file format is supported
- **Processing Fails**: Check available system memory
- **Poor Quality**: Try enhancing image contrast before processing
- **File Too Large**: Reduce mesh quality settings if needed

### Performance Tips
- Close other applications during processing
- Use SSD storage for faster file operations
- Ensure adequate RAM (8GB+ recommended)

## Technical Architecture

### Core Classes
- **`IntelligentImageProcessor`**: Advanced image analysis and enhancement
- **`PremiumCylinderBuilder`**: 3D mesh generation and optimization
- **`LithophaneLampWorker`**: Background processing thread
- **`PremiumLampGeneratorApp`**: Main GUI application

### Key Technologies
- **OpenCV**: Image processing and computer vision
- **NumPy**: Numerical computations and array operations
- **Trimesh**: 3D mesh manipulation and STL export
- **SciPy**: Scientific computing and interpolation
- **PyQt6**: Modern desktop GUI framework

## License

This software is provided for educational and personal use.

## Support

For issues and feature requests, please check the application logs located in `lamp_generator.log`.

## Version History

- **Current Version**: Professional lithophane lamp generator
- **Features**: Premium quality processing, multi-language support, LED integration
- **Optimization**: Creality K2 Plus and FDM printer compatibility