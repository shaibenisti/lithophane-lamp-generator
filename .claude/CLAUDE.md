# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Premium Lithophane Lamp Generator** - A professional PyQt6 desktop application for creating 3D-printable lithophane lamp cylinders from images. The system uses advanced image processing with face detection, intelligent enhancement pipelines, and high-precision 3D mesh generation to produce STL files optimized for FDM printing with LED integration.

**Primary Language:** Python 3.8+
**Platform:** Windows (tested), cross-platform compatible
**Application Type:** Desktop GUI with PyQt6

## Running the Application

### Development Mode
```bash
# Install dependencies
pip install -r requirements.txt

# Run directly
python main.py

# Or use the batch file (Windows)
run.bat
```

### Environment Configuration
- Configuration files: `config/settings.yaml`
- Environment variables: `.env` file (git-ignored)
- Logs: `lamp_generator.log` (git-ignored)

### Key Environment Variables (.env)
```bash
OPENCV_THREADS=4          # Number of OpenCV processing threads
LOG_LEVEL=INFO            # Logging level (DEBUG, INFO, WARNING, ERROR)
DEFAULT_LANGUAGE=he       # UI language (he=Hebrew, en=English)
MAX_MEMORY_GB=8           # Maximum memory usage
DEBUG_MODE=false          # Enable debug mode
LOG_TO_FILE=true          # Enable file logging
AUTO_SAVE_SETTINGS=true   # Auto-save configuration
```

## Architecture Overview

### Modular Structure
The codebase follows a clean separation of concerns with distinct modules:

- **`main.py`** - Application entry point, initialization, environment setup, and Qt application lifecycle
- **`src/gui/`** - User interface components (PyQt6)
  - `main_window.py` - Main application window with bilingual RTL/LTR support
  - `language_manager.py` - i18n system for Hebrew/English switching
  - `success_dialog.py` - Success notifications
  - `animations.py` - UI animations
- **`src/processing/`** - Core image and 3D processing algorithms
  - `image_processor.py` - Intelligent image analysis and enhancement
  - `image_rescue.py` - Automatic fixing for problematic images (low-res, dark, compressed)
  - `cylinder_builder.py` - High-precision 3D mesh generation
- **`src/core/`** - Core configuration and constants
  - `settings.py` - Configuration management with YAML support
  - `constants.py` - Centralized constants
- **`src/utils/`** - Utility modules
  - `worker.py` - Background processing with QThread
  - `validation.py` - Image and file validation
  - `image_utils.py` - Image processing utilities

### Data Flow Pipeline

1. **User selects image** → `ImageValidator` validates format, size, resolution
2. **Image loading** → `IntelligentImageProcessor.process_image_for_lithophane()`
3. **Rescue system** → `ImageRescueSystem.analyze_and_rescue()` - fixes low-res, dark, compressed images
4. **Image analysis** → Face detection, exposure classification, contrast analysis
5. **Enhancement** → Adaptive processing based on image characteristics (portraits, underexposed, etc.)
6. **Resizing** → Multi-stage resize with detail preservation
7. **Thickness mapping** → Convert grayscale to thickness values (0.5-2.2mm)
8. **3D generation** → `PremiumCylinderBuilder.create_premium_lithophane_cylinder()`
9. **Mesh creation** → High-precision interpolation, vertex generation, face optimization
10. **Export** → STL file export via trimesh

### Threading Model
- Main thread: Qt event loop and UI
- Worker thread: `LithophaneLampWorker` (QThread) handles all processing
- Progress signals: Real-time updates from worker to UI
- Thread-safe logging throughout

## Key Technical Details

### Physical Specifications (Configurable)
- **Cylinder**: Ø60mm × 130mm (default)
- **Wall thickness**: 2.0mm hollow design
- **Lithophane coverage**: 200° around circumference (configurable up to 220°)
- **Thickness range**: 0.5mm (brightest) to 2.2mm (darkest)
- **Inner diameter**: 56mm (for LED strip integration)
- **Resolution**: 0.08mm-0.12mm processing resolution

### Critical Design Philosophy: Faithful Image Representation
**See `docs/THICKNESS_PHILOSOPHY.md` for full details.**

The system prioritizes **faithful representation** over artificial brightening:
- Dark areas → thick walls (up to 2.2mm) → less light → naturally dark
- Bright areas → thin walls (0.5mm) → more light → naturally bright
- Minimal gamma correction (0.95 for most images) to preserve original character
- Thickness variation creates the visual effect, not aggressive image enhancement

### Image Processing Intelligence

#### Automatic Image Rescue System (`image_rescue.py`)
Detects and fixes common problems:
- Low resolution (upscales with detail preservation)
- Underexposed images (exposure correction)
- Overexposed images (highlight recovery)
- Low contrast (histogram equalization)
- Heavy compression artifacts (denoising)

#### Face Detection & Portrait Optimization
- Uses OpenCV Haar Cascade for face detection
- Portrait images get specialized processing:
  - Face-region enhancement
  - Skin tone preservation
  - Localized contrast adjustment
  - Intelligent shadow lifting
- Face data influences mesh resolution (higher for portraits)

#### Image Classification
Automatically detects image types and applies appropriate processing:
- **Portrait** (with faces)
- **Underexposed** (brightness < 40%)
- **Overexposed** (brightness > 80%)
- **Low contrast** (contrast < 40%)
- **Shadow heavy** (shadows > 60% of pixels)
- **Highlight heavy** (highlights > 60%)
- **Balanced**

### 3D Mesh Generation (`cylinder_builder.py`)

#### High-Precision Approach
- **Interpolation**: SciPy `RegularGridInterpolator` with cubic interpolation
- **Mesh density**: Up to 1,400 angular segments × 1,200 height segments (adaptive)
- **Curvature compensation**: Accounts for cylindrical projection distortion
- **Edge blending**: 4mm smooth transitions at wrap-around edges
- **Topology**: Optimized quad-based triangulation for clean geometry

#### Mesh Quality
- Automatic mesh repair and validation via trimesh
- Watertight mesh guaranteed
- Print-ready output (no manifold errors)

### Configuration System (`core/settings.py`)

Settings loaded in priority order:
1. Environment variables (`.env`)
2. YAML configuration (`config/settings.yaml`)
3. Hardcoded defaults (`core/constants.py`)

Settings are validated on load with descriptive errors for invalid values.

## Common Development Tasks

### Modifying Physical Dimensions
Edit `config/settings.yaml`:
```yaml
cylinder:
  diameter: 60.0          # Outer diameter
  height: 130.0           # Cylinder height
  wall_thickness: 2.0     # Base wall thickness

printing:
  min_thickness: 0.5      # Thinnest lithophane areas
  max_thickness: 2.2      # Thickest lithophane areas

quality:
  lithophane_coverage_angle: 200.0  # Degrees around cylinder
```

### Adjusting Image Processing Behavior
Key locations:
- **Gamma values**: `src/core/settings.py` - `GAMMA_VALUES` dict
- **Enhancement strength**: `src/processing/image_processor.py` - methods like `_enhance_contrast()`, `_lift_shadows()`
- **Face detection**: `src/processing/image_processor.py` - `_detect_faces_premium()`
- **Rescue thresholds**: `src/processing/image_rescue.py` - `RESCUE_THRESHOLDS`

### Adding New Language Support
1. Edit `src/gui/language_manager.py`
2. Add translations to both `HEBREW_TEXTS` and `ENGLISH_TEXTS` dicts
3. Ensure all UI strings use `self.language_manager.get_text(key)`

### Modifying Mesh Resolution
Resolution is adaptive based on image content:
```python
# In src/core/settings.py - PremiumSettings.get_mesh_resolution()
angular_segments = int(2 * math.pi * outer_radius / self.resolution)
height_segments = int(lithophane_height / self.resolution)
```
Lower `resolution` value = higher mesh density = slower but better quality.

## Testing Images

### Test with Real-World Problematic Images
The system is designed for production use. Test with:
- Low resolution photos (200-800px)
- Heavily compressed JPEGs (Facebook/WhatsApp downloads)
- Backlit photos
- Very dark or very bright images
- Group photos with multiple faces
- Old vintage photos with fading
- Pet photos (dark fur)

See `docs/BUSINESS_CRITICAL_FEATURES.md` for comprehensive real-world scenarios.

## Important Implementation Notes

### DO NOT Modify Thickness Range Without Understanding
The 0.5-2.2mm range is carefully calibrated for:
- White PLA light transmission characteristics
- 0.4mm nozzle with 0.12mm layers
- LED backlight visibility
- Structural integrity

Changing this affects the fundamental appearance of lithophanes. See `docs/THICKNESS_PHILOSOPHY.md` before modifying.

### Face Detection Cascade Path
The system loads OpenCV's Haar Cascade from the installed cv2 package:
```python
cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
```
This is package-dependent; verify path if face detection fails.

### STL Export Coordinate System
- Units: millimeters
- Coordinate system: Right-handed (X, Y, Z)
- Origin: Center of cylinder base
- Z-axis: Vertical (cylinder height)

### Logging Strategy
- Application uses Python's `logging` module throughout
- All modules get loggers via `logging.getLogger(__name__)`
- Logs go to both console and `lamp_generator.log`
- Progress updates are separate (via Qt signals) from debug logs

## Known Limitations & Future Enhancements

See `docs/BUSINESS_CRITICAL_FEATURES.md` for detailed business priorities:

### High Priority Missing Features
1. **HEIC format support** - iPhone default format (70% of mobile users)
2. **Preview simulation** - Show backlit preview before STL generation
3. **AI upscaling** - Better handling of very low-res images (Real-ESRGAN)
4. **Batch processing** - Process multiple images efficiently
5. **Better JPEG artifact handling** - Stronger denoising for compressed images

### Medium Priority
- Auto-rotation based on EXIF data
- Multi-face priority weighting
- Vintage photo restoration (scratch/tear inpainting)
- Customer adjustment interface (brightness/contrast tweaking)

## Dependencies

### Critical Dependencies
- **PyQt6** ≥6.4.0 - GUI framework
- **opencv-python** ≥4.7.0 - Image processing and computer vision
- **numpy** ≥1.21.0 - Numerical operations
- **trimesh** ≥3.20.0 - 3D mesh manipulation and STL export
- **scipy** ≥1.9.0 - Scientific computing (interpolation)
- **PyYAML** ≥6.0.0 - Configuration parsing
- **python-dotenv** ≥1.0.0 - Environment variables

### Optional Dependencies
- **psutil** - Performance monitoring
- **tqdm** - Progress bars

## Debugging

### Common Issues

**"Missing Dependencies" error:**
```bash
pip install --upgrade -r requirements.txt
```

**Face detection not working:**
Check OpenCV installation and Haar Cascade availability:
```python
import cv2
print(cv2.data.haarcascades)
```

**STL export fails:**
- Verify write permissions in output directory
- Check disk space
- Ensure trimesh is properly installed

**Image processing errors:**
Check `lamp_generator.log` for detailed traceback. Most errors include context about the failing image.

### Enable Debug Mode
Set in `.env`:
```bash
LOG_LEVEL=DEBUG
DEBUG_MODE=true
```

## Code Style Notes

- **Type hints**: Used throughout for clarity
- **Docstrings**: Google-style docstrings on all public methods
- **Validation**: Comprehensive validation with descriptive errors
- **Error handling**: Try-except blocks with specific exception types
- **Logging**: All significant operations logged at appropriate levels

## Documentation

Additional documentation in `docs/`:
- `README.md` - User-facing documentation
- `THICKNESS_PHILOSOPHY.md` - Design philosophy for thickness mapping
- `BUSINESS_CRITICAL_FEATURES.md` - Real-world usage priorities
- `HISTOGRAM_NORMALIZATION.md` - Technical details on image processing
- `IMAGE_RESCUE_SYSTEM.md` - Automatic image fixing system
- `UPGRADE_SUMMARY.md` - Project evolution history
- `CODE_IMPROVEMENTS.md` - Technical improvement tracking
