# Development Guide

## Getting Started

### Development Environment Setup

**Requirements:**
- Python 3.8 or higher
- Git (for version control)
- Code editor (VS Code, PyCharm, etc.)
- 3D slicer for testing (PrusaSlicer, Cura, etc.)

**Installation:**
```bash
# Clone repository
git clone <repository-url>
cd lamp-generator

# Install dependencies
pip install -r requirements.txt

# Run application
python main.py
```

### Project Structure

```
lamp-generator/
├── main.py                    # Application entry point
├── run.bat                    # Windows launcher
├── requirements.txt           # Dependencies
├── config/
│   └── settings.yaml          # Configuration
├── src/
│   ├── gui/                   # PyQt6 user interface
│   ├── processing/            # Image and 3D processing
│   ├── core/                  # Settings and constants
│   └── utils/                 # Utilities
├── docs/                      # Documentation
└── tests/                     # Testing resources
```

### Code Style

**Conventions:**
- PEP 8 style guide
- Type hints for all function signatures
- Google-style docstrings
- Descriptive variable names
- Comments for complex logic only

**Example:**
```python
def process_image(image: np.ndarray, target_size: Tuple[int, int]) -> np.ndarray:
    """
    Process image for lithophane creation.

    Args:
        image: Input grayscale image (uint8)
        target_size: (width, height) for final output

    Returns:
        Processed grayscale image ready for thickness mapping

    Raises:
        ValueError: If image is None or invalid
    """
    if image is None or image.size == 0:
        raise ValueError("Image is None or empty")

    # Implementation...
    return processed_image
```

## Common Development Tasks

### Task 1: Modify Physical Dimensions

**Goal:** Change cylinder size (e.g., make it taller)

**Files to modify:**
1. `config/settings.yaml`
2. `src/core/constants.py` (if changing defaults)

**Example:** Make cylinder 150mm tall instead of 130mm

**In `config/settings.yaml`:**
```yaml
cylinder:
  diameter: 60.0        # Keep same
  height: 150.0         # Changed from 130.0
  wall_thickness: 2.0   # Keep same
```

**In `src/core/constants.py`:**
```python
DEFAULT_CYLINDER_HEIGHT = 150.0  # Changed from 130.0
```

**Test:** Run application, generate lithophane, verify STL dimensions

### Task 2: Change Lithophane Coverage Angle

**Goal:** Wrap image around more or less of the cylinder

**Files to modify:**
1. `config/settings.yaml`
2. `src/core/constants.py`

**Example:** Change from 190° to 220°

**In `config/settings.yaml`:**
```yaml
lithophane:
  coverage_angle: 220.0  # Changed from 190.0
```

**In `src/core/constants.py`:**
```python
DEFAULT_LITHOPHANE_COVERAGE_ANGLE = 220.0  # Changed from 190.0
```

**Note:** Maximum recommended is 220° (leave gap for seam visibility)

### Task 3: Adjust Processing Strength

**Goal:** Make faces smoother or add more detail

**File to modify:** `src/processing/simple_processor.py`

**Make smoother:**
```python
self.clahe = cv2.createCLAHE(
    clipLimit=1.0,         # Gentler (was 1.3)
    tileGridSize=(32, 32)  # Larger tiles (was 24,24)
)

smoothed = cv2.bilateralFilter(
    enhanced,
    d=9,               # Stronger smoothing (was 7)
    sigmaColor=80,     # More aggressive (was 60)
    sigmaSpace=80
)
```

**Add more detail:**
```python
self.clahe = cv2.createCLAHE(
    clipLimit=2.0,         # Stronger (was 1.3)
    tileGridSize=(16, 16)  # Smaller tiles (was 24,24)
)

smoothed = cv2.bilateralFilter(
    enhanced,
    d=5,               # Less smoothing (was 7)
    sigmaColor=40,     # Less aggressive (was 60)
    sigmaSpace=40
)
```

**Test:** Generate lithophane, compare results

### Task 4: Change Thickness Range

**Goal:** Adjust brightness/contrast of lithophane

**Files to modify:**
1. `config/settings.yaml`
2. `src/core/constants.py`

**Example:** Wider range for more contrast

**In `config/settings.yaml`:**
```yaml
printing:
  min_thickness: 0.4   # Thinner (was 0.5)
  max_thickness: 2.5   # Thicker (was 2.2)
```

**Warning:**
- Below 0.4mm: Structural integrity issues
- Above 2.5mm: Diminishing returns (blocks all light)

### Task 5: Add New UI Language

**Goal:** Support a new language (e.g., Spanish)

**File to modify:** `src/gui/language_manager.py`

**Steps:**

1. **Add language constant:**
```python
SPANISH = 'es'
```

2. **Create text dictionary:**
```python
SPANISH_TEXTS = {
    'app_title': 'Generador de Lámparas Litofánicas',
    'select_image_button': 'Seleccionar Imagen',
    'output_location_label': 'Ubicación de Salida:',
    # ... all other keys
}
```

3. **Add to language lists:**
```python
SUPPORTED_LANGUAGES = [HEBREW, ENGLISH, SPANISH]

def __init__(self):
    self.texts = {
        self.HEBREW: HEBREW_TEXTS,
        self.ENGLISH: ENGLISH_TEXTS,
        self.SPANISH: SPANISH_TEXTS
    }
```

4. **Update language switching logic** in `main_window.py`

### Task 6: Add New Image Format Support

**Goal:** Support a new image format (e.g., WebP)

**Files to modify:**
1. `src/utils/validation.py`
2. `src/utils/heic_loader.py` (or create new loader)

**In `validation.py`:**
```python
SUPPORTED_IMAGE_FORMATS = {
    '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif',
    '.heic', '.heif',
    '.webp'  # Added
}
```

**In `heic_loader.py` (or new loader):**
```python
def load_image_with_format_support(file_path: str) -> np.ndarray:
    import cv2
    from pathlib import Path

    ext = Path(file_path).suffix.lower()

    if ext in {'.heic', '.heif'}:
        return load_heic(file_path)
    elif ext == '.webp':
        return load_webp(file_path)  # New function
    else:
        return cv2.imread(file_path)

def load_webp(file_path: str) -> np.ndarray:
    """Load WebP image file."""
    import cv2
    return cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
```

### Task 7: Modify Mesh Resolution

**Goal:** Generate higher/lower resolution meshes

**File to modify:** `config/settings.yaml`

**Current:**
```yaml
quality:
  resolution: 0.08          # Processing precision (mm)
  mesh_quality_multiplier: 1.2  # Vertex density
```

**Higher resolution (more vertices, larger files):**
```yaml
quality:
  resolution: 0.06          # Finer (was 0.08)
  mesh_quality_multiplier: 1.5  # Denser (was 1.2)
```

**Lower resolution (fewer vertices, smaller files):**
```yaml
quality:
  resolution: 0.10          # Coarser (was 0.08)
  mesh_quality_multiplier: 1.0  # Less dense (was 1.2)
```

**Impact:**
- Resolution 0.06: ~6M vertices, 40MB STL, highest quality
- Resolution 0.08: ~3M vertices, 20MB STL, balanced (current)
- Resolution 0.10: ~2M vertices, 12MB STL, faster processing

## Advanced Modifications

### Add Pre-Processing Step

**Goal:** Add a new processing step before CLAHE

**File:** `src/processing/simple_processor.py`

**Example:** Add denoising for noisy images

```python
def process(self, image: np.ndarray, target_size: Tuple[int, int]) -> np.ndarray:
    # Existing: Resize
    resized = cv2.resize(image, target_size, interpolation=cv2.INTER_LANCZOS4)

    # NEW: Denoise before enhancement
    denoised = cv2.fastNlMeansDenoising(
        resized,
        h=10,          # Filtering strength
        templateWindowSize=7,
        searchWindowSize=21
    )
    self.logger.info("Applied denoising")

    # Existing: CLAHE
    enhanced = self.clahe.apply(denoised)  # Use denoised instead of resized

    # ... rest of pipeline
```

### Implement Adaptive Processing

**Goal:** Automatically adjust processing based on image characteristics

**File:** `src/processing/simple_processor.py`

**Example:** Detect low-contrast images and enhance more

```python
def process(self, image: np.ndarray, target_size: Tuple[int, int]) -> np.ndarray:
    resized = cv2.resize(image, target_size, interpolation=cv2.INTER_LANCZOS4)

    # Analyze contrast
    contrast = np.std(resized)

    # Adaptive CLAHE
    if contrast < 40:
        # Low contrast - use stronger enhancement
        clip_limit = 2.0
        self.logger.info(f"Low contrast ({contrast:.1f}), using stronger CLAHE")
    else:
        # Normal contrast - use gentle enhancement
        clip_limit = 1.3
        self.logger.info(f"Normal contrast ({contrast:.1f}), using standard CLAHE")

    adaptive_clahe = cv2.createCLAHE(
        clipLimit=clip_limit,
        tileGridSize=(24, 24)
    )
    enhanced = adaptive_clahe.apply(resized)

    # ... rest of pipeline
```

### Add Real-Time Preview

**Goal:** Show preview before generating STL

**Complexity:** High (requires 3D rendering)

**Approach:**
1. Add preview button to main window
2. Generate low-resolution mesh (fast)
3. Render mesh with simulated backlight
4. Display in Qt widget or external viewer

**Not implemented** but possible with:
- `trimesh.viewer` (3D mesh viewer)
- `matplotlib` (2D preview with simulated lighting)
- `pyqtgraph` (3D rendering in Qt)

## Testing

### Manual Testing Checklist

Before committing changes:

- [ ] Application launches without errors
- [ ] Image selection dialog works
- [ ] Processing completes for test image
- [ ] Progress bar updates correctly
- [ ] STL file is created and valid
- [ ] STL opens in slicer without errors
- [ ] Mesh dimensions are correct
- [ ] No console errors or warnings
- [ ] Language switching works
- [ ] Success dialog displays correctly

### Test Images

Use diverse test images:

- **High quality photo** (4000×3000, well-lit)
- **Low resolution** (800×600, compressed)
- **Portrait** (single face, centered)
- **Group photo** (multiple faces)
- **High contrast** (bright highlights, deep shadows)
- **Low contrast** (flat, gray)
- **Dark photo** (underexposed)
- **Bright photo** (overexposed)

### Testing Workflow

```bash
# 1. Make code changes
# 2. Test with application
python main.py

# 3. Generate test lithophane
# 4. Load STL in slicer
# 5. Check quality, dimensions, etc.
# 6. Iterate if needed
# 7. Commit changes
git add .
git commit -m "Description of changes"
```

### Automated Testing

**Currently:** No automated tests (manual testing only)

**Future:** Could add:
- Unit tests for image processing functions
- Integration tests for pipeline
- STL validation tests
- Performance benchmarks

## Debugging

### Enable Debug Logging

**In `.env` file (create if doesn't exist):**
```bash
LOG_LEVEL=DEBUG
DEBUG_MODE=true
```

**Or in code:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Output:** Detailed logs in console and `lamp_generator.log`

### Common Issues

**Issue: Application won't start**
```
Check:
- Python version (3.8+)
- Dependencies installed (pip install -r requirements.txt)
- PyQt6 installed correctly
- Check console for error messages
```

**Issue: STL file is empty**
```
Check:
- Image loaded correctly (check logs)
- Thickness map created (check logs)
- Mesh generated (vertex count > 0)
- Write permissions in output directory
```

**Issue: Mesh has errors in slicer**
```
Check:
- Mesh is watertight (check logs for warnings)
- No degenerate faces
- Normals point outward
- Use trimesh.repair if needed
```

**Issue: Processing is very slow**
```
Check:
- Image size (very large images take longer)
- Mesh resolution (lower resolution = faster)
- Bilateral filter (slowest operation)
- Check CPU usage
```

### Profiling Performance

**Add timing to code:**
```python
import time

start = time.time()
# ... operation to profile ...
elapsed = time.time() - start
print(f"Operation took {elapsed:.2f} seconds")
```

**Profile entire pipeline:**
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Run processing pipeline
worker.run()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 slowest functions
```

## Git Workflow

### Branching Strategy

**Simple workflow** (single developer):
```bash
# Work directly on main
git add .
git commit -m "Descriptive message"
git push
```

**Feature branch workflow** (multiple developers):
```bash
# Create feature branch
git checkout -b feature/add-webp-support

# Make changes, test
git add .
git commit -m "Add WebP image format support"

# Merge to main
git checkout main
git merge feature/add-webp-support
```

### Commit Messages

**Format:**
```
<type>: <short description>

<optional longer description>

<optional footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code restructuring
- `perf`: Performance improvement
- `test`: Testing changes

**Examples:**
```
feat: Add WebP image format support

Implemented WebP loading in heic_loader.py and added to
supported formats in validation.py.

fix: Repair edge blending TypeError

Edge blend width was float, needed int for range() function.
Converted to int before use.

docs: Update processing guide with bilateral filter explanation

Added detailed explanation of how bilateral filtering works
and why it's optimal for lithophanes.
```

## Deployment

### Creating Executable (PyInstaller)

**Not currently configured**, but possible:

```bash
# Install PyInstaller
pip install pyinstaller

# Create executable
pyinstaller --onefile --windowed \
    --add-data "config:config" \
    --icon=icon.ico \
    main.py

# Output: dist/main.exe
```

**Challenges:**
- Large file size (~200MB with dependencies)
- OpenCV and trimesh dependencies complex
- May need additional data files bundled

### Windows Installer (Inno Setup)

**After creating executable**, create installer:

1. Install Inno Setup
2. Create `.iss` script
3. Build installer
4. Distribute `.exe` installer

**Not currently implemented.**

## Contributing Guidelines

### Before Submitting Changes

1. **Test thoroughly** with multiple images
2. **Update documentation** if behavior changes
3. **Follow code style** (PEP 8, type hints, docstrings)
4. **Add comments** for complex logic
5. **Check logs** for errors/warnings
6. **Commit with descriptive message**

### Code Review Checklist

- [ ] Code follows PEP 8 style
- [ ] All functions have type hints
- [ ] All functions have docstrings
- [ ] No hardcoded magic numbers (use constants)
- [ ] Error handling is comprehensive
- [ ] Logging is appropriate (DEBUG/INFO/WARNING/ERROR)
- [ ] No unnecessary complexity
- [ ] Comments explain WHY, not WHAT
- [ ] Changes tested manually
- [ ] No breaking changes (or documented)

## Future Enhancement Ideas

### Short Term

1. **HEIC support** - Requires pillow-heif dependency
2. **Batch processing** - Process multiple images at once
3. **Preview mode** - Show 2D preview before generating STL
4. **Undo/redo** - Image selection history
5. **Recent files** - Quick access to previous images

### Medium Term

1. **AI upscaling** - Real-ESRGAN for low-res images
2. **Auto-rotation** - Detect and fix image orientation
3. **Crop tool** - Select region of interest
4. **Brightness/contrast adjustment** - User controls
5. **Style presets** - Quick selection of processing styles

### Long Term

1. **3D preview** - Real-time mesh visualization
2. **API server** - REST API for remote access
3. **Cloud processing** - Offload heavy processing
4. **Mobile app** - iOS/Android companion
5. **Print profiles** - Slicer-specific optimizations

## Resources

### Documentation
- See `docs/` folder for all documentation
- `README.md` - User overview
- `ARCHITECTURE.md` - Technical architecture
- `PROCESSING_GUIDE.md` - Image processing details

### External Resources
- **OpenCV Documentation**: https://docs.opencv.org/
- **PyQt6 Documentation**: https://www.riverbankcomputing.com/static/Docs/PyQt6/
- **Trimesh Documentation**: https://trimsh.org/
- **NumPy Documentation**: https://numpy.org/doc/
- **SciPy Documentation**: https://docs.scipy.org/

### Learning Materials
- **Lithophane Theory**: How light transmission creates images
- **CLAHE**: Adaptive histogram equalization techniques
- **Bilateral Filtering**: Edge-preserving smoothing
- **3D Mesh Generation**: Triangulation and topology
- **STL Format**: 3D printing file format specification

---

**Happy coding! Build amazing lithophanes!**
