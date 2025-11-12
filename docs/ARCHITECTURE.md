# Architecture Documentation

## System Overview

The Lithophane Lamp Generator is built on a clean, modular architecture that separates concerns into distinct layers:

```
┌─────────────────────────────────────────────────────┐
│              PyQt6 GUI Layer                        │
│  (main_window.py, language_manager.py, etc.)       │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│           Background Worker (QThread)                │
│              (worker.py)                             │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│         Image Processing Pipeline                    │
│  (image_processor.py → simple_processor.py →        │
│   thickness_mapper.py)                              │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│         3D Mesh Generation                           │
│         (cylinder_builder.py)                        │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│         STL Export (trimesh)                         │
└─────────────────────────────────────────────────────┘
```

## Core Components

### 1. Application Entry Point

**File:** `main.py`

**Responsibilities:**
- Initialize Qt application
- Load settings and configuration
- Set up logging infrastructure
- Create main window
- Handle application lifecycle

**Key Functions:**
```python
def main():
    # Initialize Qt application
    # Load settings from config/settings.yaml
    # Set up logging to lamp_generator.log
    # Create and show main window
    # Start Qt event loop
```

### 2. GUI Layer (`src/gui/`)

#### Main Window (`main_window.py`)

**Class:** `LampGeneratorApp(QMainWindow)`

**Responsibilities:**
- Create the main user interface
- Handle image selection
- Manage output file selection
- Create and manage worker thread
- Display progress updates
- Show success/error dialogs

**Key Methods:**
- `select_image()` - Open file dialog for image selection
- `select_output()` - Open file dialog for STL output location
- `create_lithophane()` - Start the generation process
- `on_progress_updated()` - Update progress bar and status
- `on_creation_completed()` - Handle completion or errors

**Signals:**
- Uses Qt signal/slot mechanism for thread-safe communication
- Worker thread emits signals, main thread updates UI

#### Language Manager (`language_manager.py`)

**Class:** `LanguageManager`

**Responsibilities:**
- Manage Hebrew/English translations
- Provide RTL/LTR layout support
- Store all UI text strings
- Handle language switching

**Text Keys:**
- `app_title`, `select_image_button`, `output_location_label`, etc.
- All hardcoded strings go through this manager

#### Success Dialog (`success_dialog.py`)

**Class:** `SuccessDialog(QDialog)`

**Responsibilities:**
- Display completion statistics
- Show generation details (mesh info, file size, etc.)
- Provide "Open Folder" functionality

### 3. Worker Thread (`src/utils/worker.py`)

**Class:** `LithophaneLampWorker(QThread)`

**Responsibilities:**
- Run processing pipeline in background thread
- Prevent UI blocking during long operations
- Emit progress signals to main thread
- Handle errors gracefully
- Support cancellation

**Processing Stages:**
1. **Validation (0-15%)** - Check image file, output directory
2. **Image Processing (15-35%)** - Convert and enhance image
3. **3D Generation (35-85%)** - Build cylindrical mesh
4. **STL Export (85-100%)** - Write file to disk

**Signals:**
```python
progress_updated = pyqtSignal(int, str)  # (percentage, status_message)
creation_completed = pyqtSignal(bool, str, dict)  # (success, message, statistics)
```

**Pipeline Execution:**
```python
def run(self):
    # Stage 1: Validate inputs
    self._validate_inputs()

    # Stage 2: Process image
    thickness_map = self._process_image()

    # Stage 3: Build 3D cylinder
    mesh = self._build_cylinder(thickness_map)

    # Stage 4: Export STL
    self._export_stl(mesh)

    # Stage 5: Generate statistics and emit completion
    statistics = self._generate_completion_statistics(mesh)
    self.creation_completed.emit(True, success_message, statistics)
```

### 4. Image Processing Pipeline (`src/processing/`)

#### Image Processor (`image_processor.py`)

**Class:** `IntelligentImageProcessor`

**Responsibilities:**
- Orchestrate the processing pipeline
- Load and validate images
- Convert to grayscale
- Call simple processor
- Create thickness map

**Pipeline:**
```python
def process_image_for_lithophane(self, image_path: str) -> np.ndarray:
    # 1. Validate image file
    validation_result = ImageValidator.validate_image_file(image_path)

    # 2. Load and convert to grayscale
    image = self._load_and_convert_image(image_path)

    # 3. Get target dimensions
    target_size = self.settings.get_lithophane_dimensions()

    # 4. Process image (resize + enhancement)
    processed = self.processor.process(image, target_size)

    # 5. Create thickness map
    thickness_map = self.thickness_mapper.create_thickness_map(processed)

    return thickness_map
```

#### Simple Processor (`simple_processor.py`)

**Class:** `SimpleImageProcessor`

**Responsibilities:**
- Resize images with high quality
- Apply light contrast enhancement (CLAHE)
- Apply bilateral smoothing for clean faces
- Minimal, predictable processing

**Processing Steps:**
```python
def process(self, image: np.ndarray, target_size: Tuple[int, int]) -> np.ndarray:
    # Step 1: Resize with Lanczos4 interpolation
    resized = cv2.resize(image, target_size, interpolation=cv2.INTER_LANCZOS4)

    # Step 2: Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    # Parameters: clip_limit=1.3, tile_size=(24, 24)
    enhanced = self.clahe.apply(resized)

    # Step 3: Bilateral filter for smooth faces
    # Parameters: diameter=7, sigma_color=60, sigma_space=60
    smoothed = cv2.bilateralFilter(enhanced, d=7, sigmaColor=60, sigmaSpace=60)

    return smoothed
```

**Why These Parameters?**
- **CLAHE clip_limit=1.3**: Very gentle contrast enhancement
- **Tile size (24, 24)**: Large tiles prevent localized over-enhancement
- **Bilateral d=7, sigma=60**: Strong smoothing while preserving edges
- **Result**: Clean, smooth faces without texture noise

#### Thickness Mapper (`thickness_mapper.py`)

**Class:** `ThicknessMapper`

**Responsibilities:**
- Convert grayscale values to thickness (mm)
- Apply gamma correction
- Apply edge blending for smooth wrap-around
- Ensure thickness stays within printable range (0.5-2.2mm)

**Mapping Logic:**
```python
def create_thickness_map(self, image: np.ndarray) -> np.ndarray:
    # Step 1: Normalize to 0-1 range
    normalized = image.astype(np.float32) / 255.0

    # Step 2: Apply gamma correction (default: 1.0)
    gamma_corrected = np.power(normalized, self.gamma)

    # Step 3: Invert (bright → thin, dark → thick)
    inverted = 1.0 - gamma_corrected

    # Step 4: Map to thickness range
    thickness_map = min_thickness + (inverted * (max_thickness - min_thickness))

    # Step 5: Apply edge blending (4mm smooth transitions)
    thickness_map = self._apply_edge_blending(thickness_map)

    return thickness_map
```

**Thickness Philosophy:**
- **Dark pixels** → **Thick walls (2.2mm)** → Blocks light → Appears dark
- **Bright pixels** → **Thin walls (0.5mm)** → Allows light → Appears bright
- This creates the lithophane effect when backlit

### 5. 3D Mesh Generation (`src/processing/cylinder_builder.py`)

**Class:** `CylinderBuilder`

**Responsibilities:**
- Generate high-precision 3D cylinder mesh
- Apply thickness variations from thickness map
- Create hollow cylinder (inner + outer surfaces)
- Optimize topology for 3D printing
- Validate and repair mesh

**Mesh Generation Process:**

```python
def create_lithophane_cylinder(self, thickness_map: np.ndarray) -> trimesh.Trimesh:
    # Step 1: Calculate cylinder parameters
    outer_radius = cylinder_diameter / 2  # 30mm
    inner_radius = outer_radius - wall_thickness  # 28mm

    # Step 2: Create high-precision interpolator
    interpolator = self._create_precision_interpolator(thickness_map)

    # Step 3: Generate vertices
    vertices = self._generate_premium_vertices(
        interpolator, outer_radius, inner_radius,
        angular_segments=1400, height_segments=1200
    )

    # Step 4: Generate face topology
    faces = self._generate_optimized_faces(angular_segments, height_segments)

    # Step 5: Create and validate mesh
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
    mesh.remove_duplicate_faces()
    mesh.remove_degenerate_faces()
    mesh.fix_normals()

    return mesh
```

**Key Techniques:**

1. **Cubic Interpolation:**
   ```python
   interpolator = RegularGridInterpolator(
       (y_coords, x_coords), thickness_map,
       method='cubic'  # Smooth interpolation
   )
   ```

2. **Edge Blending:**
   - 4mm smooth transitions at lithophane wrap-around edges
   - Prevents visible seams when cylinder closes

3. **Curvature Compensation:**
   ```python
   curvature_compensation = 1.0 + 0.05 * cos(angle * 2.0)
   adjusted_thickness = thickness * curvature_compensation
   ```
   - Compensates for cylindrical projection distortion

4. **Adaptive Resolution:**
   ```python
   angular_segments = int(2 * π * outer_radius / resolution)  # ~1400
   height_segments = int(lithophane_height / resolution)      # ~1200
   ```

**Mesh Quality:**
- Watertight mesh (no holes)
- No manifold errors
- Proper normals (outward-facing)
- Clean topology (quads triangulated optimally)

### 6. Configuration System (`src/core/`)

#### Settings (`settings.py`)

**Class:** `Settings`

**Responsibilities:**
- Load configuration from YAML
- Provide default values
- Validate settings
- Calculate derived values (mesh resolution, dimensions, etc.)

**Key Settings:**
```python
# Physical dimensions (hardcoded for optimal results)
cylinder_diameter: 60.0  # mm
cylinder_height: 130.0   # mm
wall_thickness: 2.0      # mm

# Lithophane specifications
lithophane_coverage_angle: 190.0  # degrees
min_thickness: 0.5       # mm (brightest)
max_thickness: 2.2       # mm (darkest)

# Processing quality
resolution: 0.08         # mm (processing precision)
mesh_quality_multiplier: 1.2  # Higher = more vertices
gamma: 1.0               # Tonal curve (1.0 = linear)
```

**Calculated Values:**
```python
def get_mesh_resolution(self) -> Tuple[int, int]:
    """Calculate angular and height segments based on resolution."""
    angular_segments = int(2 * π * outer_radius / resolution)
    height_segments = int(lithophane_height / resolution)
    return angular_segments, height_segments

def get_inner_radius(self) -> float:
    """Calculate inner radius for hollow cylinder."""
    return (cylinder_diameter / 2) - wall_thickness
```

#### Constants (`constants.py`)

**Purpose:** Centralized constants used throughout the application

**Categories:**
- Physical defaults (dimensions, thickness range)
- Processing parameters (CLAHE, bilateral filter)
- Mesh generation (edge blending, curvature compensation)
- Validation limits (min/max image size)
- File format support

### 7. Utilities (`src/utils/`)

#### Validation (`validation.py`)

**Class:** `ImageValidator`

**Responsibilities:**
- Validate image files before processing
- Check file existence and format
- Verify image dimensions
- Ensure file is readable

#### HEIC Loader (`heic_loader.py`)

**Purpose:** Support iPhone HEIC format images

**Key Function:**
```python
def load_image_with_heic_support(file_path: str) -> np.ndarray:
    # Detect HEIC format
    if is_heic_file(file_path):
        # Load with pillow_heif
        return heic_loader.load_heic(file_path)
    else:
        # Standard OpenCV loading
        return cv2.imread(file_path)
```

## Data Flow

### Complete Processing Flow

```
1. User selects image
   ↓
2. Main window validates path
   ↓
3. User clicks "Create Lithophane"
   ↓
4. Worker thread starts
   ↓
5. Image validation (ImageValidator)
   ↓
6. Image loading (load_image_with_heic_support)
   ↓
7. Grayscale conversion (cv2.cvtColor)
   ↓
8. Image processing (SimpleImageProcessor)
   ├─ Resize with Lanczos4
   ├─ CLAHE enhancement
   └─ Bilateral smoothing
   ↓
9. Thickness mapping (ThicknessMapper)
   ├─ Normalize to 0-1
   ├─ Gamma correction
   ├─ Invert (bright → thin)
   ├─ Map to 0.5-2.2mm range
   └─ Apply edge blending
   ↓
10. 3D mesh generation (CylinderBuilder)
    ├─ Create interpolator
    ├─ Generate vertices
    ├─ Generate faces
    ├─ Create trimesh
    └─ Validate and repair
    ↓
11. STL export (trimesh.export)
    ↓
12. Statistics generation
    ↓
13. Signal completion to main thread
    ↓
14. Show success dialog
```

## Threading Model

### Main Thread
- Handles all Qt GUI operations
- Responds to user interactions
- Updates progress bar and status labels
- Never blocks during processing

### Worker Thread
- Runs processing pipeline
- Emits progress signals (thread-safe)
- Can be cancelled gracefully
- Cleans up resources on completion/cancellation

### Thread Communication
```python
# Worker → Main Thread (via Qt signals)
worker.progress_updated.emit(50, "Building 3D mesh...")
worker.creation_completed.emit(True, message, statistics)

# Main Thread → Worker (via method calls)
worker.cancel()  # Request cancellation
worker.stop()    # Alias for cancel
```

## Error Handling Strategy

### Validation Errors
- Caught early before processing starts
- User-friendly error messages
- Clear guidance on how to fix

### Processing Errors
- Caught at each pipeline stage
- Detailed logging to `lamp_generator.log`
- Graceful degradation when possible
- Informative error dialogs

### Example Error Flow:
```python
try:
    thickness_map = image_processor.process_image_for_lithophane(image_path)
except ValidationError as e:
    # Show user-friendly message
    show_error("Invalid Image", str(e))
except ImageProcessingError as e:
    # Log detailed error + show simplified message
    logger.error(f"Processing failed: {e}", exc_info=True)
    show_error("Processing Error", "Unable to process image. Try a different image.")
except Exception as e:
    # Unexpected error - log everything
    logger.error(f"Unexpected error: {e}", exc_info=True)
    show_error("Unexpected Error", "An internal error occurred. Check the log file.")
```

## Logging Infrastructure

### Log Levels
- **DEBUG**: Detailed processing information
- **INFO**: Normal operation (image loaded, mesh created, etc.)
- **WARNING**: Non-critical issues (mesh not watertight, etc.)
- **ERROR**: Failures that prevent completion

### Log Locations
- **Console**: Real-time output during development
- **File**: `lamp_generator.log` (persistent logging)

### Example Log Output:
```
2025-11-12 21:30:15 INFO Starting lithophane creation: family_photo.jpg
2025-11-12 21:30:15 INFO Processing image: 4000×3000 → 1500×1800
2025-11-12 21:30:16 INFO Resized to 1500×1800
2025-11-12 21:30:16 INFO Applied light contrast enhancement (CLAHE)
2025-11-12 21:30:17 INFO Applied bilateral smoothing for texture reduction
2025-11-12 21:30:17 INFO Creating premium lithophane cylinder...
2025-11-12 21:30:18 INFO Mesh resolution: 1400 × 1200 segments
2025-11-12 21:30:25 INFO Cylinder completed: 3362800 vertices, 6720000 faces
2025-11-12 21:30:30 INFO STL exported successfully: output/family_photo.stl
```

## Performance Considerations

### Memory Usage
- Large images (>4000px) create large meshes
- High vertex counts (>3 million) require significant RAM
- Mesh processing is memory-intensive

### Processing Time
- **Image processing**: 1-3 seconds (typical)
- **Mesh generation**: 5-15 seconds (typical)
- **STL export**: 5-10 seconds (file I/O)
- **Total**: 15-30 seconds for typical images

### Optimization Techniques
1. **Adaptive resolution**: Mesh density based on cylinder size
2. **Efficient interpolation**: SciPy cubic interpolation (fast)
3. **Background threading**: Non-blocking UI
4. **Memory-efficient processing**: Pipeline approach (no full duplication)

## Extensibility Points

### Adding New Image Formats
1. Add format to `validation.py` supported formats list
2. Implement loader in `heic_loader.py` or similar
3. Update `load_image_with_heic_support()` to detect and load

### Modifying Processing
1. Adjust parameters in `simple_processor.py`
2. Change CLAHE or bilateral filter settings
3. Add additional processing steps in pipeline

### Changing Physical Dimensions
1. Edit `config/settings.yaml`
2. Update constants in `constants.py` if needed
3. Rebuild application

### Adding API Support
See separate API integration documentation for:
- REST API approach (Flask/FastAPI)
- CLI interface approach
- Python module import approach

---

**Architecture Philosophy:** Clean separation of concerns, minimal coupling, maximum clarity.
