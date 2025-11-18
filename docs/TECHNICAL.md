# Technical Documentation

Developer and contributor guide for the Premium Lithophane Lamp Generator.

## Architecture Overview

The application follows a clean modular architecture with strict separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                    main.py (Entry Point)                 │
│          Environment Setup + Qt Application Init         │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                    GUI Layer (PyQt6)                     │
│  - main_window.py: Application window                   │
│  - language_manager.py: Bilingual i18n                  │
│  - animations.py: UI animations                         │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                  Processing Layer                        │
│  - image_processor.py: Smart pipeline orchestrator      │
│  - face_handler.py: Face detection & enhancement        │
│  - shadow_lifter.py: Shadow analysis & correction       │
│  - simple_processor.py: Image resize & filtering        │
│  - thickness_mapper.py: Grayscale → thickness           │
│  - cylinder_builder.py: 3D mesh generation              │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                    Core Layer                            │
│  - settings.py: Configuration management                │
│  - constants.py: Centralized constants                  │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                   Utilities Layer                        │
│  - worker.py: Background QThread processing             │
│  - validation.py: Image & settings validation           │
│  - heic_loader.py: HEIC format support                  │
│  - image_utils.py: Shared utilities                     │
└─────────────────────────────────────────────────────────┘
```

## Code Structure

### Core Modules

#### `main.py` - Application Entry Point
- Loads environment variables from `.env`
- Configures logging (console + file)
- Validates processing environment
- Loads settings from YAML
- Initializes Qt application with high DPI support
- Starts event loop

#### `src/core/settings.py` - Configuration Management
**Dataclass-based settings with validation:**
- Three-tier priority: Environment variables → YAML → Defaults
- Runtime validation of all settings
- Dynamic mesh resolution calculation
- Type-safe configuration access

**Key Settings:**
```python
@dataclass
class Settings:
    cylinder_diameter: float
    cylinder_height: float
    min_thickness: float
    max_thickness: float
    resolution: float
    lithophane_coverage_angle: float
    gamma_override: Optional[float]  # None = smart auto
```

#### `src/core/constants.py` - Centralized Constants
- Default physical dimensions
- Mesh resolution limits
- Material properties (PLA density)
- Processing thresholds

### GUI Layer

#### `src/gui/main_window.py` - Main Application Window
**Features:**
- Bilingual UI (Hebrew RTL ↔ English LTR)
- File selection with validation
- Progress tracking with QProgressBar
- Activity log with auto-scroll
- Thread-safe signal handling

**Threading Model:**
- Main thread: Qt event loop and UI updates
- Worker thread: All image processing and 3D generation
- Signals: Progress updates, completion, errors

#### `src/gui/language_manager.py` - Internationalization
- Complete Hebrew/English translations
- Dynamic layout direction (RTL/LTR)
- 280+ translated strings
- Font optimization for Hebrew

### Processing Layer

#### `src/processing/image_processor.py` - Smart Pipeline Orchestrator

**Complete Processing Pipeline:**
```python
def process_image_for_lithophane(image_path: str) -> np.ndarray:
    1. Validate and load image (with HEIC support)
    2. Convert to grayscale
    3. Detect faces using Haar Cascade
    4. Analyze shadows (threshold, distribution)
    5. Lift shadows if needed (face-aware mode)
    6. Enhance detected faces (gentle CLAHE + smoothing)
    7. Calculate smart gamma based on image analysis
    8. Resize and apply contrast enhancement
    9. Create thickness map with optimal gamma
    10. Return thickness map for 3D builder
```

**Smart Gamma Selection:**
```python
def _calculate_smart_gamma(image, face_result, shadow_analysis) -> float:
    # Portraits (has faces):
    #   Dark portrait (brightness < 35%): γ = 0.80
    #   Portrait with shadows (< 50%): γ = 0.85
    #   Well-lit portrait: γ = 0.90

    # General images:
    #   Very dark (< 30%): γ = 0.85
    #   Moderately dark (< 45%): γ = 0.92
    #   Normal: γ = 0.95
    #   Bright (> 75%): γ = 1.0 (linear)
```

#### `src/processing/face_handler.py` - Face Detection & Enhancement

**Face Detection:**
- Uses OpenCV Haar Cascade (`haarcascade_frontalface_default.xml`)
- Parameters: `scaleFactor=1.1, minNeighbors=5, minSize=(30,30)`
- Returns face regions as (x, y, w, h) rectangles

**Face Enhancement:**
1. Extract face region with 20% padding
2. Apply gentle CLAHE: `clipLimit=1.5, tileGridSize=(16,16)`
3. Apply Gaussian blur `(5,5)` to smooth skin texture
4. Brighten if dark (target brightness: 100/255)
5. Blend back with gradient mask for smooth edges

**Key Design Choice:**
- Large CLAHE tiles (16×16) avoid amplifying skin pores
- Gaussian blur removes fine texture (wrinkles, pores)
- Preserves important features (eyes, nose, mouth)

#### `src/processing/shadow_lifter.py` - Shadow Analysis & Correction

**Shadow Analysis:**
```python
def analyze_shadows(image: np.ndarray) -> ShadowAnalysis:
    # Threshold: pixels < 60/255 considered shadows
    # Heavy shadows: > 25% of pixels are dark
    return ShadowAnalysis(shadow_ratio, has_heavy_shadows)
```

**Shadow Lifting:**
- Proportional to darkness (darker areas lifted more)
- Gaussian blur for smooth transitions
- Face-aware mode: extra lift for dark faces
- Strength: 40/255 (configurable)

#### `src/processing/simple_processor.py` - Image Processing

**Processing Steps:**
1. **Resize** - Lanczos4 interpolation for quality
2. **CLAHE** - Gentle contrast: `clipLimit=1.3, tileGridSize=(24,24)`
3. **Bilateral Filter** - Aggressive skin smoothing: `d=9, sigmaColor=85, sigmaSpace=85`

**Bilateral Filter:**
- Smooths textures while preserving edges
- Critical for removing skin pores and fine details
- Higher sigma values = more aggressive smoothing

#### `src/processing/thickness_mapper.py` - Grayscale to Thickness

**Thickness Mapping:**
```python
def create_thickness_map(image: np.ndarray) -> np.ndarray:
    normalized = image / 255.0
    gamma_corrected = normalized ** gamma  # Apply gamma curve
    inverted = 1.0 - gamma_corrected       # Dark = thick
    thickness = min_thickness + inverted * (max_thickness - min_thickness)
    return thickness  # In millimeters
```

**Key Principle:**
- Dark pixels (0) → max_thickness (2.5mm) → blocks light → appears dark
- Bright pixels (255) → min_thickness (0.5mm) → allows light → appears bright

#### `src/processing/cylinder_builder.py` - 3D Mesh Generation

**High-Precision Mesh Creation:**

1. **Setup:**
```python
outer_radius = cylinder_diameter / 2
inner_radius = outer_radius - wall_thickness
angular_segments = 800-1400  # Based on resolution
height_segments = 600-1200   # Based on resolution
```

2. **Interpolation:**
```python
# SciPy RegularGridInterpolator with cubic method
interpolator = RegularGridInterpolator(
    (y_coords, x_coords),
    thickness_map,
    method='cubic'
)
```

3. **Vertex Generation:**
```python
for each angular position (θ):
    for each height position (z):
        # Sample thickness from interpolator
        thickness = interpolator([z, θ])

        # Curvature compensation (3% factor)
        effective_thickness = thickness * (1 + 0.03 * cos(θ * 0.8))

        # Generate vertices
        inner_vertex = (inner_radius * cos(θ), inner_radius * sin(θ), z)
        outer_vertex = ((inner_radius + thickness) * cos(θ), ..., z)
```

4. **Mesh Assembly:**
```python
# Create faces (quad-based triangulation)
for each quad:
    triangle1 = [v0, v1, v2]
    triangle2 = [v0, v2, v3]

# Trimesh validation
mesh = trimesh.Trimesh(vertices, faces)
mesh.fix_normals()  # Ensure correct orientation
mesh.fill_holes()   # Watertight guarantee
```

**Critical Details:**
- Consistent radius calculation prevents non-manifold edges
- Curvature compensation improves light distribution
- Minimal padding (2px) for interpolation edge cases
- Quad-based topology for clean geometry

### Utilities Layer

#### `src/utils/worker.py` - Background Processing

**QThread-based Worker:**
```python
class LithophaneLampWorker(QThread):
    progress = pyqtSignal(int, str)  # (percentage, status_message)
    finished = pyqtSignal(dict)       # Success with info
    error = pyqtSignal(str)           # Error message

    def run(self):
        # Process image in background thread
        # Emit progress signals
        # Handle cancellation
```

**Thread Safety:**
- All processing in worker thread
- UI updates via signals only
- Graceful cancellation with 3-second timeout

#### `src/utils/validation.py` - Comprehensive Validation

**Image Validation:**
- File existence and format
- Minimum/maximum dimensions
- File size checks
- Quality scoring (resolution, aspect ratio)
- Warnings for problematic images

**Settings Validation:**
- Physical dimension constraints
- Thickness range validation
- Resolution bounds
- Angle limits (180-220°)

## Data Flow

**Complete Processing Flow:**
```
User selects image
    ↓
ImageValidator validates format/size/quality
    ↓
Load with HEIC support
    ↓
Convert to grayscale
    ↓
FaceHandler.detect_faces() → Haar Cascade
    ↓
ShadowLifter.analyze_shadows() → Shadow ratio
    ↓
If heavy shadows → ShadowLifter.lift_shadows() (face-aware)
    ↓
If faces detected → FaceHandler.enhance_face_regions()
    ↓
Calculate smart gamma based on faces + brightness
    ↓
SimpleProcessor.process() → Resize + CLAHE + Bilateral
    ↓
ThicknessMapper.create_thickness_map() → Apply gamma
    ↓
CylinderBuilder.create_lithophane_cylinder() → 3D mesh
    ↓
Export STL via Trimesh
    ↓
Success dialog with statistics
```

## Key Algorithms

### Face Detection
- **Algorithm:** OpenCV Haar Cascade (frontal face detection)
- **Cascade:** `haarcascade_frontalface_default.xml`
- **Trade-offs:** Fast but less accurate than DNN; sufficient for lithophanes
- **Future:** Could upgrade to MediaPipe for better accuracy

### Shadow Analysis
- **Threshold:** Pixels < 60/255 considered shadows
- **Heavy threshold:** >25% of image
- **Lifting:** Proportional to darkness, Gaussian smoothed

### Bilateral Filtering
- **Purpose:** Smooth textures while preserving edges
- **Parameters:** `d=9, sigmaColor=85, sigmaSpace=85`
- **Trade-off:** Computationally expensive but essential for quality

### Cubic Interpolation
- **Purpose:** Smooth thickness transitions in 3D mesh
- **Library:** SciPy `RegularGridInterpolator`
- **Method:** Cubic (higher quality than linear)
- **Performance:** Fast enough for 1M+ vertex meshes

## Development Setup

### Environment Setup

1. **Clone and install:**
```bash
git clone <repo>
cd lithophane-lamp-generator
pip install -r requirements.txt
```

2. **Create `.env` for development:**
```bash
LOG_LEVEL=DEBUG
DEBUG_MODE=true
```

3. **Run:**
```bash
python main.py
```

### Code Style

- **Type hints:** Used throughout for clarity
- **Docstrings:** Google-style on all public methods
- **Logging:** Structured logging at appropriate levels
- **Error handling:** Specific exception types, descriptive messages
- **Validation:** Comprehensive with user-friendly errors

### Adding New Features

#### Adding New Image Processing Step

1. Create module in `src/processing/`
2. Implement as class with clear interface
3. Integrate into `image_processor.py` pipeline
4. Add settings to `settings.py` if configurable
5. Update logging and progress signals
6. Test with various image types

Example:
```python
# src/processing/my_enhancer.py
class MyEnhancer:
    def enhance(self, image: np.ndarray) -> np.ndarray:
        # Your processing
        return enhanced_image

# src/processing/image_processor.py
self.my_enhancer = MyEnhancer()

def process_image_for_lithophane(self, image_path: str):
    # ... existing steps ...
    preprocessed = self.my_enhancer.enhance(preprocessed)
    # ... continue pipeline ...
```

#### Adding New Configuration Setting

1. Add to `src/core/constants.py` (default value)
2. Add to `Settings` dataclass in `src/core/settings.py`
3. Add validation in `_validate_settings()`
4. Document in `config/settings.yaml` with comment
5. Use in processing code

#### Adding Translation

Edit `src/gui/language_manager.py`:
```python
ENGLISH_TEXTS = {
    'my_key': 'English text',
}

HEBREW_TEXTS = {
    'my_key': 'טקסט בעברית',
}
```

Use in GUI:
```python
text = self.language_manager.get_text('my_key')
```

## Performance Considerations

### Bottlenecks
1. **Bilateral filtering** - Most expensive operation (~40% of processing time)
2. **Cubic interpolation** - Scales with mesh density
3. **Face detection** - Fixed cost (~10% of time)

### Optimization Options
- Reduce `resolution` in settings (fewer mesh vertices)
- Disable face detection if not needed (faster by 10%)
- Use smaller input images (faster resize)
- Reduce bilateral filter parameters (lower quality but faster)

### Memory Usage
- Peak usage: ~500MB for large images (4000×3000)
- Mesh generation: ~200MB for high-density meshes
- STL export: Minimal (streaming write)

## Testing

### Manual Testing Checklist
- [ ] Portrait with face detection
- [ ] Dark/underexposed image
- [ ] Bright/overexposed image
- [ ] Landscape (no faces)
- [ ] HEIC format (iPhone)
- [ ] Very low resolution (<500px)
- [ ] Very high resolution (>4000px)
- [ ] Hebrew UI workflow
- [ ] English UI workflow

### Key Test Images
Place test images in `TESTS/` directory and process to verify:
1. Quality (no excessive noise)
2. Brightness (not too dark/bright)
3. STL validity (opens in slicer)
4. Print quality (if possible)

## Common Development Tasks

### Modifying Physical Dimensions
Edit `config/settings.yaml`:
```yaml
cylinder:
  diameter: 70.0  # Change outer diameter
  height: 150.0   # Change height
```

### Adjusting Image Processing Strength
- **More smoothing:** Increase bilateral filter sigmas in `simple_processor.py`
- **More contrast:** Increase CLAHE `clipLimit` in `simple_processor.py`
- **Brighter:** Lower gamma values (0.85-0.90)
- **More face enhancement:** Increase brightness boost in `face_handler.py`

### Changing Mesh Resolution
Lower `resolution` value = higher mesh density:
```yaml
quality:
  resolution: 0.04  # Very high (slow, large file)
  resolution: 0.06  # High (default)
  resolution: 0.10  # Low (fast, smaller file)
```

## Dependencies Explained

### Critical Dependencies
- **PyQt6** - Cross-platform GUI framework with native look
- **opencv-python** - Image processing, face detection, CLAHE, bilateral filter
- **numpy** - All array operations, fast numerical computing
- **trimesh** - 3D mesh creation, validation, STL export
- **scipy** - Cubic interpolation for smooth meshes

### Optional Dependencies
- **pillow-heif** - HEIC support (only if needed)
- **psutil** - Performance monitoring (optional)

### Why These Libraries?
- **PyQt6 over Tkinter:** More modern, better theming, RTL support
- **OpenCV over PIL:** Face detection, CLAHE, bilateral filter
- **Trimesh over numpy-stl:** Validation, repair, better mesh operations
- **SciPy over NumPy interpolation:** Cubic method for smoother results

## Future Enhancements

### High Priority
- AI upscaling (Real-ESRGAN) for very low-res images
- Preview simulation (backlit rendering before STL generation)
- Batch processing (multiple images → multiple STLs)
- Better JPEG artifact handling (stronger denoising)

### Medium Priority
- Auto-rotation based on EXIF data
- Multi-face priority weighting
- Custom STL file formats (OBJ, 3MF)
- Undo/redo for settings

### Low Priority
- GPU acceleration for image processing
- Advanced face detection (MediaPipe)
- Online repository of test images
- Plugin system for custom processors

---

**For user documentation, see:** [README.md](../README.md)
