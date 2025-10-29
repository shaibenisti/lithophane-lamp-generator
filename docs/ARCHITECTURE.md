# Architecture Documentation

## Project Structure

```
E:\STL softwhere\
│
├── main.py                          # Application entry point and initialization
├── requirements.txt                 # Python package dependencies
├── run.bat                         # Windows quick launcher
│
├── config/
│   └── settings.yaml               # YAML configuration file
│
├── src/
│   ├── core/                       # Core configuration and constants
│   │   ├── settings.py             # Settings management class
│   │   └── constants.py            # Application-wide constants
│   │
│   ├── gui/                        # User interface components
│   │   ├── main_window.py          # Main application window
│   │   ├── language_manager.py     # Bilingual translation system
│   │   ├── segmented_control.py    # Modern iOS-style language selector
│   │   ├── success_dialog.py       # Success notification dialogs
│   │   └── animations.py           # UI animation effects
│   │
│   ├── processing/                 # Image and 3D processing engines
│   │   ├── image_processor.py      # Intelligent image enhancement
│   │   ├── image_rescue.py         # Automatic image problem fixing
│   │   └── cylinder_builder.py     # 3D mesh generation
│   │
│   └── utils/                      # Utility modules
│       ├── worker.py               # Background QThread worker
│       ├── validation.py           # Input validation utilities
│       └── image_utils.py          # Image processing helpers
│
├── docs/                           # Documentation
│   ├── README.md                   # User guide
│   ├── ARCHITECTURE.md             # This file
│   ├── GUI.md                      # UI components documentation
│   └── CONFIGURATION.md            # Settings guide
│
├── Tests/                          # Test files and test images
└── .claude/                        # Claude Code AI instructions
    └── CLAUDE.md                   # Project-specific AI guidelines
```

## Module Overview

### Entry Point: `main.py`

**Responsibilities:**
- Environment initialization (logging, .env loading)
- System validation (Python version, dependencies)
- Qt application creation and lifecycle management
- Settings loading from YAML and environment
- Main window instantiation
- Graceful error handling and shutdown

**Key Functions:**
- `setup_logging()` - Configures file and console logging
- `verify_dependencies()` - Checks critical packages
- `load_environment()` - Loads .env configuration
- `main()` - Application entry point

---

## Core Module (`src/core/`)

### `settings.py` - Configuration Management

**Class: `PremiumSettings`**

Central configuration manager that loads settings from multiple sources with priority:
1. Environment variables (.env)
2. YAML configuration file
3. Hardcoded defaults

**Key Attributes:**
```python
# Cylinder physical dimensions
diameter: float           # Outer diameter (mm)
height: float            # Cylinder height (mm)
wall_thickness: float    # Base wall thickness (mm)

# Lithophane specifications
min_thickness: float     # Thinnest areas (bright) - 0.5mm
max_thickness: float     # Thickest areas (dark) - 2.2mm
coverage_angle: float    # Wrap angle (degrees) - 200°

# Processing quality
resolution: float        # Processing resolution - 0.1mm
detail_level: str       # 'high', 'medium', 'low'
```

**Key Methods:**
- `load_from_yaml()` - Parses settings.yaml
- `get_mesh_resolution()` - Calculates optimal mesh density
- `get_gamma_for_image()` - Returns appropriate gamma correction
- `validate()` - Ensures settings are within acceptable ranges

### `constants.py` - Application Constants

Contains all hardcoded values used throughout the application:
```python
# File size limits
MAX_IMAGE_SIZE_MB = 50
MAX_OUTPUT_SIZE_MB = 500

# Image processing
MIN_IMAGE_WIDTH = 200
MIN_IMAGE_HEIGHT = 200
MAX_IMAGE_DIMENSION = 4000

# Thread configuration
WORKER_SHUTDOWN_TIMEOUT_MS = 5000

# UI display
MAX_FILENAME_DISPLAY_LENGTH = 50
MIN_PRINTABLE_CHAR_CODE = 32
```

---

## GUI Module (`src/gui/`)

### `main_window.py` - Main Application Window

**Class: `PremiumLampGeneratorApp(QMainWindow)`**

The main application window with bilingual support and dark theme.

**Structure:**
```python
__init__()
    ├── Initialize settings and language manager
    ├── Set state variables (selected paths, worker)
    └── Call initialize_interface()

initialize_interface()
    ├── Window configuration (title, size, geometry)
    ├── create_header() - Language selector
    ├── create_control_panel()
    │   ├── create_file_selection_section()
    │   ├── create_action_section()
    │   ├── create_progress_section()
    │   └── create_activity_log_section()
    └── apply_styling() - Dark theme CSS
```

**Key Methods:**
- `select_image_file()` - File dialog and image validation
- `select_output_location()` - Output path selection
- `create_lithophane_lamp()` - Initiates background processing
- `change_language()` - Handles language switching
- `update_ui_language()` - Updates all UI text elements
- `update_layout_direction()` - Switches RTL/LTR layout

**Signal/Slot Connections:**
```python
# Button connections
select_image_button.clicked → select_image_file()
select_output_button.clicked → select_output_location()
create_lamp_button.clicked → create_lithophane_lamp()

# Language selector
language_selector.selectionChanged(int, str) → change_language(int, str)

# Worker thread signals
worker.progress_updated(int, str) → update_progress_and_status(int, str)
worker.creation_completed(bool, str, dict) → on_creation_completed(bool, str, dict)
```

### `language_manager.py` - Internationalization

**Class: `LanguageManager`**

Manages Hebrew/English translations with complete UI text coverage.

**Structure:**
```python
translations = {
    'he': { 'key': 'Hebrew text', ... },
    'en': { 'key': 'English text', ... }
}
```

**Key Methods:**
- `get_text(key)` - Retrieves translated string
- `set_language(lang_code)` - Changes active language
- `get_available_languages()` - Returns {'he': 'עברית', 'en': 'English'}
- `is_rtl()` - Returns True for Hebrew

### `segmented_control.py` - Modern Language Selector

**Class: `SegmentedControl(QWidget)`**

Custom iOS-style segmented control widget.

**Features:**
- Side-by-side button display
- Active/inactive visual states
- Hover effects
- Rounded container background

**Signal:**
```python
selectionChanged = pyqtSignal(int, str)  # (index, data)
```

**Key Methods:**
- `add_segment(text, data)` - Adds a new segment
- `set_current_index(index)` - Sets active segment programmatically
- `current_index()` - Returns selected index
- `current_data()` - Returns associated data
- `paintEvent(event)` - Custom background painting

---

## Processing Module (`src/processing/`)

### `image_processor.py` - Intelligent Image Enhancement

**Class: `IntelligentImageProcessor`**

Core image processing engine with face detection and adaptive enhancement.

**Processing Pipeline:**
```
process_image_for_lithophane()
    ├── 1. Load and validate image
    ├── 2. Analyze image characteristics
    │   ├── _detect_faces_premium() - Face detection
    │   ├── _classify_exposure() - Underexposed/overexposed/balanced
    │   └── _analyze_histogram() - Contrast, shadows, highlights
    ├── 3. Rescue problematic images
    │   └── ImageRescueSystem.analyze_and_rescue()
    ├── 4. Apply adaptive enhancements
    │   ├── Portrait mode (if faces detected)
    │   ├── Underexposed correction
    │   ├── Overexposed recovery
    │   └── Contrast enhancement
    ├── 5. Multi-stage resize
    │   └── _resize_with_detail_preservation()
    ├── 6. Final grayscale conversion
    │   └── Luminance-based with gamma correction
    └── 7. Return processed image + metadata
```

**Key Methods:**
- `_detect_faces_premium()` - OpenCV Haar Cascade face detection
- `_enhance_for_portraits()` - Face-region enhancement
- `_lift_shadows()` - Shadow recovery with selective brightening
- `_enhance_contrast()` - CLAHE (Contrast Limited Adaptive Histogram Equalization)
- `_apply_gamma_correction()` - Gamma curve adjustment

### `image_rescue.py` - Automatic Problem Fixing

**Class: `ImageRescueSystem`**

Automatically detects and fixes common image problems.

**Detection & Fixes:**
```python
analyze_and_rescue(image)
    ├── Check resolution (upscale if < 800px)
    ├── Check exposure (correct if too dark/bright)
    ├── Check contrast (enhance if < 40%)
    ├── Check compression (denoise if JPEG artifacts)
    └── Return rescued image + applied fixes
```

**Rescue Operations:**
- **Low Resolution** → Multi-stage upscaling with LANCZOS interpolation
- **Underexposed** → Exposure compensation + shadow lifting
- **Overexposed** → Highlight recovery + tone mapping
- **Low Contrast** → Histogram equalization
- **Compression Artifacts** → Bilateral filtering (denoise)

### `cylinder_builder.py` - 3D Mesh Generation

**Class: `PremiumCylinderBuilder`**

High-precision 3D mesh generator for lithophane cylinders.

**Generation Pipeline:**
```
create_premium_lithophane_cylinder()
    ├── 1. Calculate dimensions and mesh resolution
    ├── 2. Generate thickness map from image
    │   └── Map pixel brightness → wall thickness (0.5-2.2mm)
    ├── 3. Create cylindrical coordinate grid
    │   ├── Angular segments (around circumference)
    │   └── Height segments (vertical)
    ├── 4. Apply edge blending (4mm transition zones)
    ├── 5. Interpolate thickness values
    │   └── SciPy RegularGridInterpolator (cubic)
    ├── 6. Generate vertices (inner + outer surface)
    ├── 7. Create faces (quad-based triangulation)
    ├── 8. Add cylinder base and top caps
    ├── 9. Mesh validation and repair
    └── 10. Export to STL via trimesh
```

**Key Methods:**
- `_generate_thickness_map()` - Converts grayscale to thickness
- `_create_cylinder_vertices()` - Generates 3D vertex positions
- `_create_cylinder_faces()` - Topology generation
- `_apply_edge_blending()` - Smooth wrap-around transitions
- `_add_cylinder_caps()` - Top and bottom solid discs

**Mesh Quality Features:**
- Cubic interpolation for smooth surfaces
- Curvature compensation for cylindrical projection
- Watertight mesh guarantee
- Manifold edge validation

---

## Utilities Module (`src/utils/`)

### `worker.py` - Background Processing

**Class: `LithophaneLampWorker(QThread)`**

Background thread worker for non-blocking lamp creation.

**Signals:**
```python
progress_updated = pyqtSignal(int, str)      # (percentage, message)
creation_completed = pyqtSignal(bool, str, dict)  # (success, message, stats)
```

**Processing Flow:**
```python
run()
    ├── 1. Emit progress: "Loading image..."
    ├── 2. Call IntelligentImageProcessor.process_image_for_lithophane()
    ├── 3. Emit progress: "Building 3D cylinder..."
    ├── 4. Call PremiumCylinderBuilder.create_premium_lithophane_cylinder()
    ├── 5. Emit progress: "Exporting STL..."
    ├── 6. Save mesh.export(output_path)
    └── 7. Emit creation_completed with statistics
```

**Thread Safety:**
- All file I/O in worker thread
- Progress updates via signals
- Graceful cancellation support
- Exception handling with error reporting

### `validation.py` - Input Validation

**Classes:**
- `ValidationError(Exception)` - Custom validation exception
- `ImageValidator` - Image file validation
- `FileValidator` - Output path validation

**ImageValidator Methods:**
```python
validate_image_file(path)
    ├── Check file exists
    ├── Check file extension
    ├── Check file size (< 50MB)
    ├── Try to load with OpenCV
    ├── Check dimensions (>= 200x200)
    ├── Analyze quality metrics
    └── Return validation result + warnings
```

**FileValidator Methods:**
```python
validate_output_path(path)
    ├── Check parent directory exists
    ├── Check write permissions
    ├── Ensure .stl extension
    ├── Check available disk space
    └── Return validated absolute path
```

### `image_utils.py` - Image Processing Helpers

Utility functions for common image operations:
- `safe_resize()` - Resize with aspect ratio preservation
- `convert_to_grayscale()` - Luminance-based conversion
- `apply_clahe()` - Contrast enhancement wrapper
- `calculate_brightness()` - Average brightness calculation
- `estimate_noise()` - JPEG artifact detection

---

## Data Flow Architecture

### Complete Processing Flow

```
User Action
    ↓
[Main Window] select_image_file()
    ├→ ImageValidator.validate_image_file()
    └→ Update UI state
    ↓
[Main Window] select_output_location()
    ├→ FileValidator.validate_output_path()
    └→ Enable create button
    ↓
[Main Window] create_lithophane_lamp()
    ├→ Create LithophaneLampWorker
    ├→ Connect signals
    └→ Start thread
         ↓
[Worker Thread] run()
    ├→ IntelligentImageProcessor.process_image_for_lithophane()
    │   ├→ ImageRescueSystem.analyze_and_rescue()
    │   ├→ Face detection
    │   ├→ Adaptive enhancement
    │   └→ Return processed image
    │
    ├→ PremiumCylinderBuilder.create_premium_lithophane_cylinder()
    │   ├→ Generate thickness map
    │   ├→ Build 3D mesh
    │   └→ Return trimesh object
    │
    ├→ mesh.export(output_path)
    └→ Emit creation_completed signal
         ↓
[Main Window] on_creation_completed()
    ├→ Show success/error dialog
    └→ Update UI state
```

### Threading Model

```
Main Thread (Qt Event Loop)
    ├── GUI rendering
    ├── User input handling
    └── Signal/slot connections

Worker Thread (QThread)
    ├── Image loading
    ├── Image processing (CPU-intensive)
    ├── 3D mesh generation (CPU-intensive)
    ├── File I/O
    └── Progress reporting (via signals)
```

**Thread Safety Mechanisms:**
- Qt signals/slots for cross-thread communication
- No shared mutable state
- All heavy computation in worker thread
- UI updates only from main thread

---

## Design Patterns

### 1. **Model-View-Controller (MVC)**
- **Model:** `PremiumSettings`, image data, mesh data
- **View:** `PremiumLampGeneratorApp`, UI widgets
- **Controller:** Signal/slot connections, event handlers

### 2. **Observer Pattern**
- Qt signals/slots for event-driven updates
- Worker progress updates to UI
- Language change propagation

### 3. **Strategy Pattern**
- Different enhancement strategies based on image classification
- Adaptive gamma correction based on image type

### 4. **Factory Pattern**
- Worker thread creation
- Widget creation methods in main_window

### 5. **Singleton-like Pattern**
- `LanguageManager` manages single translation state
- `PremiumSettings` centralizes configuration

---

## Error Handling Strategy

### Validation Errors
```python
try:
    ImageValidator.validate_image_file(path)
except ValidationError as e:
    QMessageBox.critical(self, "Validation Error", str(e))
```

### Processing Errors
```python
try:
    process_image_for_lithophane(image)
except Exception as e:
    logger.error(f"Processing failed: {e}")
    emit creation_completed(False, error_message, {})
```

### User-Facing Errors
- **Validation errors:** Shown immediately with clear guidance
- **Processing errors:** Logged + shown in completion dialog
- **System errors:** Logged with full traceback

---

## Performance Considerations

### Optimization Techniques

1. **Background Processing**
   - All heavy operations in QThread
   - Non-blocking UI

2. **Adaptive Resolution**
   - Mesh density based on image content
   - Higher resolution for portraits

3. **Memory Management**
   - Process images in place when possible
   - Clear intermediate results
   - Configurable memory limits

4. **Multi-stage Processing**
   - Progressive enhancement
   - Early validation to fail fast

### Typical Performance
- **Image processing:** 5-15 seconds
- **Mesh generation:** 10-30 seconds
- **STL export:** 5-10 seconds
- **Total:** 1-3 minutes per lamp

---

## Extension Points

### Adding New Image Enhancements
1. Add method to `IntelligentImageProcessor`
2. Call from `process_image_for_lithophane()` pipeline
3. Update progress messages

### Adding New Languages
1. Add translations to `LanguageManager.translations`
2. Add segment to `create_header()` in main_window
3. Update `get_available_languages()`

### Customizing Cylinder Shapes
1. Modify `cylinder_builder.py`
2. Update settings schema in `settings.py`
3. Add UI controls for new parameters

### Adding Export Formats
1. Extend `PremiumCylinderBuilder`
2. Add format selection to UI
3. Use trimesh export capabilities

---

## Testing Strategy

### Manual Testing
- Test with various image types and qualities
- Test language switching
- Test error conditions (invalid files, no permissions)

### Test Images Location
```
Tests/
├── high_quality.jpg
├── low_resolution.jpg
├── underexposed.jpg
├── portrait_with_faces.jpg
└── problematic_compressed.jpg
```

### Critical Test Scenarios
1. Low-resolution image rescue
2. Face detection on portraits
3. Very dark image enhancement
4. Large file handling
5. Permission errors
6. Language switching mid-process

---

**For UI-specific details, see [GUI.md](GUI.md)**
**For configuration options, see [CONFIGURATION.md](CONFIGURATION.md)**
