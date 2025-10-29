# Configuration Guide

## Overview

The Premium Lithophane Lamp Generator uses a flexible configuration system that supports multiple sources with priority-based loading:

**Configuration Priority (highest to lowest):**
1. Environment variables (`.env` file)
2. YAML configuration (`config/settings.yaml`)
3. Hardcoded defaults (`src/core/constants.py`)

This allows you to customize the application without modifying code.

---

## Configuration Files

### 1. `config/settings.yaml` - Main Configuration

Primary configuration file for cylinder dimensions, quality settings, and image processing parameters.

**Location:** `E:\STL softwhere\config\settings.yaml`

**Format:** YAML (human-readable structured data)

### 2. `.env` - Environment Variables

Optional environment variable overrides for runtime configuration.

**Location:** `E:\STL softwhere\.env` (create if doesn't exist)

**Format:** KEY=VALUE pairs

**Note:** `.env` is git-ignored for security (credentials, API keys, etc.)

---

## YAML Configuration Reference

### Cylinder Dimensions

```yaml
cylinder:
  diameter: 60.0          # Outer diameter in mm
  height: 130.0           # Cylinder height in mm
  wall_thickness: 2.0     # Base wall thickness in mm
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `diameter` | float | 60.0 | Outer diameter of cylinder (mm). Typical range: 50-100mm |
| `height` | float | 130.0 | Total height of cylinder (mm). Typical range: 100-200mm |
| `wall_thickness` | float | 2.0 | Base wall thickness excluding lithophane (mm). Typical: 1.5-3.0mm |

**Examples:**

```yaml
# Smaller lamp (fits tea light)
cylinder:
  diameter: 50.0
  height: 100.0
  wall_thickness: 1.8

# Larger decorative lamp
cylinder:
  diameter: 80.0
  height: 150.0
  wall_thickness: 2.5
```

**Important:**
- Inner diameter = `diameter - (2 × wall_thickness)` - ensure this fits your LED source
- Larger cylinders need more processing time
- Very thin walls (<1.5mm) may be structurally weak

---

### Printing Parameters

```yaml
printing:
  nozzle_diameter: 0.4    # 3D printer nozzle diameter in mm
  layer_height: 0.12      # Layer height for printing in mm
  min_thickness: 0.5      # Minimum lithophane thickness in mm
  max_thickness: 2.2      # Maximum lithophane thickness in mm
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `nozzle_diameter` | float | 0.4 | Your 3D printer nozzle diameter (mm). Standard: 0.4mm |
| `layer_height` | float | 0.12 | Target layer height for printing (mm). For detail: 0.08-0.15mm |
| `min_thickness` | float | 0.5 | Thinnest lithophane areas = brightest light transmission |
| `max_thickness` | float | 2.2 | Thickest lithophane areas = darkest (blocks most light) |

**Thickness Range Guidelines:**

The `min_thickness` to `max_thickness` range controls how your lithophane looks when backlit:

```
Brightness:     ████████░░░░░░░░░░░░░░  (Thin = Bright)
Thickness:      0.5mm → 2.2mm
Darkness:       ░░░░░░░░░░░░░░░░████████  (Thick = Dark)
```

**Recommended Ranges:**

| Material | Min | Max | Notes |
|----------|-----|-----|-------|
| White PLA | 0.5mm | 2.2mm | Default, best light transmission |
| Natural PLA | 0.6mm | 2.4mm | Slightly less translucent |
| PETG | 0.6mm | 2.5mm | More translucent, needs thicker range |
| Resin (translucent) | 0.3mm | 1.5mm | Very translucent, thinner range |

**Warning:**
Changing the thickness range significantly alters the visual appearance of your lithophane. The default 0.5-2.2mm range is calibrated for white PLA and standard LED backlighting. Test before committing to large prints.

---

### Quality Settings

```yaml
quality:
  resolution: 0.15        # Processing resolution in mm
  mesh_quality_multiplier: 1.0  # Mesh quality multiplier
  lithophane_coverage_angle: 200.0  # Coverage angle in degrees
  detail_enhancement: false  # Enable detail enhancement
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `resolution` | float | 0.15 | Processing resolution (mm). Lower = higher quality & slower |
| `mesh_quality_multiplier` | float | 1.0 | Mesh density multiplier (0.5-2.0) |
| `lithophane_coverage_angle` | float | 200.0 | How many degrees around cylinder (0-360°) |
| `detail_enhancement` | bool | false | Extra detail processing (slower) |

**Resolution Impact:**

| Resolution | Quality | Processing Time | STL Size | Recommended For |
|------------|---------|-----------------|----------|-----------------|
| 0.20mm | Draft | ~30 seconds | ~1 MB | Quick tests |
| 0.15mm | Standard | ~1-2 minutes | ~2 MB | Most prints |
| 0.10mm | High | ~3-5 minutes | ~5 MB | Critical detail |
| 0.08mm | Ultra | ~5-10 minutes | ~10 MB | Professional work |

**Lithophane Coverage Angle:**

```
360° = Full wrap (image wraps completely around)
270° = Three-quarter wrap
200° = Default (leaves 160° solid back for stability)
180° = Half cylinder (flat back)
90° = Quarter cylinder
```

Visual:
```
Top view:

200° Coverage:           360° Coverage:
    ___                      ___
   /   \                    /   \
  |  █  |                  |█████|
  |█████|                  |█████|
  |█████|                  |█████|
   \___/                    \___/
    ^^^                    ^^^^^^^
  Lithophane              Lithophane
```

**Recommendations:**
- 200° (default) - Good balance of visual + structural strength
- 180° - Best for portraits, easier printing
- 270-360° - Panoramic images, requires good printer

---

### Margins

```yaml
margins:
  top_margin: 2.0         # Top margin in mm
  bottom_margin: 2.0      # Bottom margin in mm
  edge_blend_width: 4.0   # Edge blending width in mm
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `top_margin` | float | 2.0 | Solid margin at top of cylinder (mm) |
| `bottom_margin` | float | 2.0 | Solid margin at bottom of cylinder (mm) |
| `edge_blend_width` | float | 4.0 | Smooth transition at lithophane edges (mm) |

**Visual:**
```
Side view:

┌─────────┐  ← Top solid cap
├─────────┤  ← Top margin (2mm)
│░░░░░░░░░│  ← Edge blend zone (4mm) - gradual transition
│█████████│
│█████████│  ← Lithophane area
│█████████│
│░░░░░░░░░│  ← Edge blend zone (4mm)
├─────────┤  ← Bottom margin (2mm)
└─────────┘  ← Bottom solid cap
```

**Edge Blend Width:**
- Creates smooth visual transition where lithophane meets solid areas
- Prevents harsh boundaries
- Typical range: 2-6mm
- Larger values = softer edges, smaller lithophane area

---

### Performance

```yaml
performance:
  opencv_threads: 4       # Number of OpenCV processing threads
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `opencv_threads` | int | 4 | Number of CPU threads for OpenCV operations |

**Recommendations:**

| CPU Cores | Recommended Setting |
|-----------|---------------------|
| 2 cores | `opencv_threads: 2` |
| 4 cores | `opencv_threads: 4` |
| 6+ cores | `opencv_threads: 6` |
| 8+ cores | `opencv_threads: 8` |

**Note:** Using more threads than CPU cores provides no benefit and may degrade performance.

---

### Gamma Values (Image Processing)

```yaml
gamma_values:
  portrait: 0.9
  portrait_low_contrast: 0.8
  underexposed: 0.7
  overexposed: 1.2
  low_contrast: 0.85
  shadow_heavy: 0.75
  highlight_heavy: 1.1
  balanced: 1.0
```

**What is Gamma?**

Gamma correction adjusts the brightness curve of an image:
- **Gamma < 1.0** - Brightens mid-tones, lifts shadows
- **Gamma = 1.0** - No correction (linear)
- **Gamma > 1.0** - Darkens mid-tones, recovers highlights

**Image Classifications:**

| Classification | Gamma | Description |
|----------------|-------|-------------|
| `portrait` | 0.9 | Images with detected faces |
| `portrait_low_contrast` | 0.8 | Portraits with flat lighting |
| `underexposed` | 0.7 | Dark images (brightness < 40%) |
| `overexposed` | 1.2 | Bright images (brightness > 80%) |
| `low_contrast` | 0.85 | Flat images (contrast < 40%) |
| `shadow_heavy` | 0.75 | Images with >60% shadow pixels |
| `highlight_heavy` | 1.1 | Images with >60% highlight pixels |
| `balanced` | 1.0 | Well-exposed images |

**Tuning Gamma:**

If your lithophanes are coming out too dark:
```yaml
gamma_values:
  portrait: 0.85         # Lower = brighter
  underexposed: 0.65     # More aggressive brightening
```

If your lithophanes are coming out too bright (washed out):
```yaml
gamma_values:
  portrait: 0.95         # Higher = preserve darkness
  balanced: 1.05         # Slightly darken
```

**Design Philosophy:**

The default values prioritize **faithful image representation** over artificial brightening. Dark areas stay dark (thick walls), bright areas stay bright (thin walls). The result is a natural-looking lithophane that respects the original photograph's character.

---

### Validation Settings

```yaml
validation:
  max_file_size_mb: 50
  min_resolution: [100, 100]
  max_resolution: [8000, 8000]
  supported_formats: ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif']
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_file_size_mb` | int | 50 | Maximum input image file size (MB) |
| `min_resolution` | [int, int] | [100, 100] | Minimum width and height (pixels) |
| `max_resolution` | [int, int] | [8000, 8000] | Maximum width and height (pixels) |
| `supported_formats` | list | ['.jpg', ...] | Allowed file extensions |

**Recommendations:**

For high-resolution work:
```yaml
validation:
  max_file_size_mb: 100
  max_resolution: [10000, 10000]
```

For constrained systems:
```yaml
validation:
  max_file_size_mb: 20
  max_resolution: [4000, 4000]
```

---

## Environment Variables (`.env`)

Optional runtime configuration that overrides YAML settings.

**Create file:** `E:\STL softwhere\.env`

### Available Variables

```bash
# Logging Configuration
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_TO_FILE=true            # Enable file logging (lamp_generator.log)
DEBUG_MODE=false            # Enable debug mode with verbose output

# UI Configuration
DEFAULT_LANGUAGE=he         # Default language: 'he' (Hebrew) or 'en' (English)
AUTO_SAVE_SETTINGS=true     # Auto-save settings changes

# Performance Configuration
MAX_MEMORY_GB=8             # Maximum memory usage limit (GB)
OPENCV_THREADS=4            # Number of OpenCV processing threads

# Processing Configuration
ENABLE_FACE_DETECTION=true  # Enable face detection for portraits
APPLY_IMAGE_RESCUE=true     # Enable automatic image rescue system
USE_GAMMA_CORRECTION=true   # Enable gamma correction

# Output Configuration
DEFAULT_OUTPUT_DIR=./output # Default directory for STL files
INCLUDE_STATISTICS=true     # Include processing stats in output
```

### Example `.env` File

**For development/debugging:**
```bash
LOG_LEVEL=DEBUG
DEBUG_MODE=true
LOG_TO_FILE=true
ENABLE_FACE_DETECTION=true
APPLY_IMAGE_RESCUE=true
DEFAULT_LANGUAGE=en
```

**For production/performance:**
```bash
LOG_LEVEL=INFO
DEBUG_MODE=false
LOG_TO_FILE=true
MAX_MEMORY_GB=16
OPENCV_THREADS=8
DEFAULT_LANGUAGE=he
```

**For low-resource systems:**
```bash
LOG_LEVEL=WARNING
DEBUG_MODE=false
MAX_MEMORY_GB=4
OPENCV_THREADS=2
```

---

## Common Configuration Scenarios

### Scenario 1: Faster Processing (Lower Quality)

**Goal:** Speed up processing for testing, reduce file sizes

```yaml
quality:
  resolution: 0.20                    # Lower resolution
  mesh_quality_multiplier: 0.7        # Reduce mesh density
  detail_enhancement: false

performance:
  opencv_threads: 8                   # Use all CPU cores
```

**Result:** ~50% faster, ~50% smaller files, slightly less detail

---

### Scenario 2: Maximum Quality (Slow)

**Goal:** Best possible quality for professional/portfolio work

```yaml
quality:
  resolution: 0.08                    # High resolution
  mesh_quality_multiplier: 1.5        # Denser mesh
  detail_enhancement: true            # Extra processing

printing:
  layer_height: 0.08                  # Fine layers
```

**Result:** 3-5× slower, 5-10× larger files, maximum detail

---

### Scenario 3: Large Cylinder (Gift Lamp)

**Goal:** Create a larger decorative lamp

```yaml
cylinder:
  diameter: 80.0                      # Larger diameter
  height: 160.0                       # Taller
  wall_thickness: 2.5                 # Stronger walls

quality:
  lithophane_coverage_angle: 220.0    # More wrap-around
```

**Result:** More impressive size, longer print time (~10-15 hours)

---

### Scenario 4: Small Portrait Lamp

**Goal:** Compact portrait lamp for desk/nightstand

```yaml
cylinder:
  diameter: 50.0                      # Compact
  height: 100.0                       # Desktop size
  wall_thickness: 1.8

quality:
  lithophane_coverage_angle: 180.0    # Half cylinder, portrait-optimized
  resolution: 0.12                    # Good detail
```

**Result:** Quick print (~3-4 hours), good for portraits

---

### Scenario 5: Panoramic Landscape

**Goal:** Wrap a landscape photo around full cylinder

```yaml
quality:
  lithophane_coverage_angle: 350.0    # Nearly full wrap

margins:
  edge_blend_width: 6.0               # Wider blend for seamless wrap
```

**Result:** Panoramic effect, requires careful positioning

---

## Troubleshooting

### "Out of Memory" Errors

**Symptoms:** Crashes during mesh generation

**Solutions:**
```bash
# In .env
MAX_MEMORY_GB=4

# In settings.yaml
quality:
  resolution: 0.20
  mesh_quality_multiplier: 0.8
```

---

### Processing Too Slow

**Symptoms:** Takes >5 minutes per lamp

**Solutions:**
```yaml
quality:
  resolution: 0.15              # Increase from 0.10
  detail_enhancement: false     # Disable if enabled

performance:
  opencv_threads: 8             # Match CPU cores
```

---

### STL Files Too Large

**Symptoms:** Files >10 MB, slicer crashes

**Solutions:**
```yaml
quality:
  resolution: 0.18
  mesh_quality_multiplier: 0.7
```

---

### Lithophanes Too Dark

**Symptoms:** Backlit image barely visible

**Solutions:**
```yaml
gamma_values:
  portrait: 0.85                # Lower gamma = brighter
  balanced: 0.9
  underexposed: 0.65

printing:
  min_thickness: 0.4            # Thinner minimum = more light
```

---

### Lithophanes Too Bright (Washed Out)

**Symptoms:** No dark areas, lack of contrast

**Solutions:**
```yaml
gamma_values:
  portrait: 0.95                # Higher gamma = preserve darkness
  balanced: 1.05

printing:
  max_thickness: 2.5            # Thicker maximum = darker darks
```

---

### Face Detection Not Working

**Symptoms:** Portraits not classified correctly

**Solutions:**
```bash
# In .env
ENABLE_FACE_DETECTION=true

# Verify OpenCV installation
python -c "import cv2; print(cv2.data.haarcascades)"
```

---

## Advanced: Configuration Hierarchy

The application loads settings in this order:

1. **Hardcoded defaults** (`src/core/constants.py`)
2. **YAML file** (`config/settings.yaml`) - *overrides defaults*
3. **Environment variables** (`.env`) - *overrides YAML*
4. **Runtime changes** (future feature) - *overrides all*

**Example:**

```python
# Default (in code)
diameter = 60.0

# YAML override
diameter: 65.0              # Now 65.0

# .env override
CYLINDER_DIAMETER=70.0      # Now 70.0 (if supported)
```

**Recommendation:** Use YAML for permanent settings, .env for temporary testing.

---

## Configuration Best Practices

1. **Backup before editing** - Copy `settings.yaml` before major changes
2. **Test with sample images** - Verify changes with small test prints first
3. **Document custom values** - Add comments explaining your changes
4. **Use version control** - Track changes to `settings.yaml` with git
5. **Start conservative** - Make small adjustments, test, iterate

---

## Need Help?

- See [README.md](README.md) for general usage
- See [ARCHITECTURE.md](ARCHITECTURE.md) for code structure
- See [GUI.md](GUI.md) for UI customization

---

**Experiment, test, and find the perfect settings for your use case!**
