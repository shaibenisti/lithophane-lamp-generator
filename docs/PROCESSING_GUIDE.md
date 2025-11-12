# Image Processing Guide

## Overview

The Lithophane Lamp Generator uses a clean, simple processing pipeline designed to create smooth, professional lithophanes without texture noise or over-processing artifacts. This guide explains how the image processing works and why these specific techniques were chosen.

## Processing Philosophy

**Core Principle:** Minimal, predictable processing that respects the original image while creating smooth facial areas suitable for lithophane printing.

### Design Goals

1. **Smooth Faces** - Eliminate skin texture noise that looks bad when backlit
2. **Preserved Features** - Keep sharp edges like eyes, lips, hair boundaries
3. **Natural Tones** - Respect the original brightness and contrast
4. **Predictable Results** - Same input always produces same output
5. **Fast Processing** - Under 5 seconds for typical images

### What We DON'T Do

- ❌ No AI upscaling or enhancement
- ❌ No face detection or region-specific processing
- ❌ No multi-stage adaptive enhancement
- ❌ No aggressive histogram manipulation
- ❌ No automatic brightness/contrast adjustment

These techniques often create artifacts, inconsistency, or over-processed results.

## The Processing Pipeline

### Stage 1: Image Loading and Validation

**File:** `src/processing/image_processor.py` → `_load_and_convert_image()`

**Steps:**
1. Load image using OpenCV or HEIC loader
2. Validate image loaded successfully
3. Convert to grayscale (preserves tonal information)

**Code:**
```python
def _load_and_convert_image(self, image_path: str) -> np.ndarray:
    # Load image with HEIC support
    image = load_image_with_heic_support(image_path)

    # Convert to grayscale if needed
    if len(image.shape) == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    return image
```

**Grayscale Conversion:**
- Uses standard luminosity formula: `0.299*R + 0.587*G + 0.114*B`
- Preserves perceived brightness correctly
- Eliminates color information (not needed for lithophanes)

### Stage 2: Resize to Target Dimensions

**File:** `src/processing/simple_processor.py` → `process()`

**Target Size Calculation:**
```python
# Based on cylinder dimensions and coverage angle
lithophane_width = (π * diameter * coverage_angle) / 360
lithophane_height = cylinder_height - top_margin - bottom_margin

# At resolution 0.08mm:
# Width: (π * 60 * 190) / 360 / 0.08 ≈ 1500 pixels
# Height: (130 - 2 - 2) / 0.08 ≈ 1800 pixels
target_size = (1500, 1800)
```

**Resize Method:**
```python
resized = cv2.resize(image, target_size, interpolation=cv2.INTER_LANCZOS4)
```

**Why Lanczos4?**
- Highest quality resampling filter in OpenCV
- Excellent for both upscaling and downscaling
- Preserves details without introducing aliasing
- Slight edge sharpening (good for lithophanes)

**Alternatives (NOT used):**
- `INTER_LINEAR`: Too blurry for large downscales
- `INTER_CUBIC`: Good but slightly less sharp than Lanczos
- `INTER_NEAREST`: Creates blocky artifacts
- `INTER_AREA`: Good for downscaling but not as sharp

### Stage 3: CLAHE Enhancement

**File:** `src/processing/simple_processor.py`

**What is CLAHE?**

CLAHE (Contrast Limited Adaptive Histogram Equalization) is a localized contrast enhancement technique that:
- Divides image into small tiles
- Enhances contrast within each tile
- Limits enhancement to prevent noise amplification
- Blends tiles smoothly to avoid tile boundaries

**Our Parameters:**
```python
clahe = cv2.createCLAHE(
    clipLimit=1.3,        # Very gentle enhancement
    tileGridSize=(24, 24) # Large tiles for smooth results
)
enhanced = clahe.apply(resized)
```

**Parameter Explanation:**

**clipLimit = 1.3**
- Range: 1.0 (no enhancement) to 4.0+ (aggressive)
- Lower values = gentler, smoother enhancement
- Higher values = stronger contrast but more noise
- 1.3 provides subtle detail enhancement without amplifying texture

**tileGridSize = (24, 24)**
- Defines the size of local enhancement regions
- Larger tiles = smoother, more global enhancement
- Smaller tiles = more local, can amplify skin texture
- (24, 24) creates smooth facial areas without localized noise

**Visual Effect:**
```
Before CLAHE:               After CLAHE (1.3, 24×24):
┌──────────────┐            ┌──────────────┐
│  Flat gray   │            │ Gentle detail│
│  face with   │    →       │ enhancement  │
│  low detail  │            │ smooth areas │
└──────────────┘            └──────────────┘
```

**Why Not Stronger?**

Testing showed that higher clip_limit or smaller tiles creates:
- Noisy skin texture (pores, blemishes amplified)
- Unnatural appearance when backlit
- Distracting texture variation

**Comparison:**
```
clip_limit=2.0, tiles=(8,8):   ← OLD (too noisy)
  - Strong local enhancement
  - Skin pores visible
  - Texture amplification

clip_limit=1.3, tiles=(24,24): ← CURRENT (smooth)
  - Gentle global enhancement
  - Smooth facial areas
  - Natural appearance
```

### Stage 4: Bilateral Filtering

**File:** `src/processing/simple_processor.py`

**What is Bilateral Filtering?**

A edge-preserving smoothing filter that:
- Smooths flat regions (like skin)
- Preserves sharp edges (like eyes, lips, hair)
- Considers both spatial distance AND color similarity
- Perfect for removing texture while keeping features

**Our Parameters:**
```python
smoothed = cv2.bilateralFilter(
    enhanced,
    d=7,              # Diameter: size of filter neighborhood
    sigmaColor=60,    # Color similarity threshold
    sigmaSpace=60     # Spatial distance threshold
)
```

**Parameter Explanation:**

**d = 7**
- Filter diameter in pixels
- Larger = more smoothing, slower processing
- 7 is a sweet spot for face smoothing

**sigmaColor = 60**
- Range: 0-255
- Higher = more aggressive color-based smoothing
- 60 smooths skin tones while preserving edges

**sigmaSpace = 60**
- Controls spatial falloff
- Higher = smoother gradients
- 60 creates nice smooth transitions

**How It Works:**

```python
# For each pixel, consider neighbors within diameter d
# Weight neighbors by:
# 1. Spatial distance (closer = more weight)
# 2. Color similarity (similar color = more weight)

# Example: Smoothing skin near an eye
┌─────────────────────────────┐
│ Skin pixels (similar color) │ ← Smoothed together
│   All weighted equally       │
├─────────────────────────────┤
│ Eye edge (different color)  │ ← NOT smoothed with skin
│   Low weight, preserved      │
└─────────────────────────────┘
```

**Visual Effect:**
```
Before Bilateral:           After Bilateral (d=7, σ=60):
┌──────────────┐            ┌──────────────┐
│ Skin texture │            │ Smooth skin  │
│ pores, noise │    →       │ sharp eyes   │
│ sharp edges  │            │ sharp hair   │
└──────────────┘            └──────────────┘
```

**Why This Works for Lithophanes:**

Lithophanes are backlit, so:
- **Smooth areas** = even light transmission = natural appearance
- **Texture noise** = random light variation = distracting artifacts
- **Sharp features** = preserved character = recognizable faces

**Comparison:**
```
No smoothing:                  ← Noisy, textured
  - Skin pores visible
  - Distracting when backlit

Gaussian blur (d=7):          ← Blurry, loses detail
  - Smooths everything
  - Eyes and edges blurred

Bilateral (d=7, σ=60):        ← OPTIMAL
  - Smooth skin
  - Sharp features
  - Perfect for lithophanes
```

## Thickness Mapping

### Stage 5: Convert Grayscale to Thickness

**File:** `src/processing/thickness_mapper.py`

**Goal:** Convert grayscale pixel values (0-255) to wall thickness (0.5-2.2mm)

**Pipeline:**
```python
def create_thickness_map(self, image: np.ndarray) -> np.ndarray:
    # Step 1: Normalize to 0-1
    normalized = image / 255.0

    # Step 2: Apply gamma correction (default: 1.0 = linear)
    gamma_corrected = np.power(normalized, 1.0)

    # Step 3: Invert (bright → thin, dark → thick)
    inverted = 1.0 - gamma_corrected

    # Step 4: Map to thickness range
    thickness_map = 0.5 + (inverted * (2.2 - 0.5))

    # Step 5: Apply edge blending
    thickness_map = self._apply_edge_blending(thickness_map)

    return thickness_map
```

**Thickness Philosophy:**

```
┌──────────────────────────────────────────────────┐
│  Pixel Value  →  Thickness  →  Light  →  Result │
├──────────────────────────────────────────────────┤
│  255 (white)  →   0.5mm     →  Bright →  Bright │
│  128 (gray)   →   1.35mm    →  Medium →  Medium │
│    0 (black)  →   2.2mm     →  Dark   →  Dark   │
└──────────────────────────────────────────────────┘
```

**Why Invert?**
- Bright areas should be THIN (allow light through)
- Dark areas should be THICK (block light)
- This creates the lithophane effect

**Thickness Range (0.5mm - 2.2mm):**

**Minimum (0.5mm):**
- Thinnest printable wall with 0.4mm nozzle
- Bright highlights, maximum light transmission
- Structurally sound (2-3 perimeters = 0.8-1.2mm total)

**Maximum (2.2mm):**
- Deep shadows, minimal light transmission
- Still provides good contrast when backlit
- Not too thick (saves material, print time)

**Why Not Wider Range?**
- Thinner than 0.5mm: Structural integrity issues
- Thicker than 2.2mm: Diminishing returns (blocks almost all light)

**Gamma Correction:**

Currently disabled (gamma = 1.0), but available for adjustment:

```python
gamma = 1.0   # Linear (current)
gamma = 0.9   # Slightly brighter mid-tones
gamma = 1.1   # Slightly darker mid-tones
```

Gamma adjusts the tonal curve without changing black/white points.

### Stage 6: Edge Blending

**File:** `src/processing/thickness_mapper.py` → `_apply_edge_blending()`

**Purpose:** Create smooth transitions at the wrap-around edges of the lithophane

**The Problem:**

```
Lithophane wraps 190° around cylinder:
┌────────────────────────┐
│  Image                 │
└────────────────────────┘
        ↓ Wrapped ↓
   ┌──────────┐
   │          │ ← Left and right edges meet here
   │  Image   │    Need smooth transition!
   │          │
   └──────────┘
```

**The Solution:**

Apply gradual blending at edges (4mm blend width):

```python
def _apply_edge_blending(self, thickness_map: np.ndarray) -> np.ndarray:
    blend_width = int(4.0 / 0.08)  # 50 pixels at 0.08mm resolution

    # Create fade mask at edges
    for x in range(blend_width):
        factor = x / blend_width  # 0.0 → 1.0

        # Blend left edge toward average thickness
        thickness_map[:, x] = thickness_map[:, x] * factor + avg * (1 - factor)

        # Blend right edge toward average thickness
        thickness_map[:, -x-1] = thickness_map[:, -x-1] * factor + avg * (1 - factor)

    return thickness_map
```

**Visual Effect:**
```
Without edge blending:        With 4mm edge blending:
┌──────────────────┐          ┌──────────────────┐
│Sharp│      │Sharp│          │Fade│       │Fade │
│Edge │ Main │Edge │   →      │ In │  Main │ Out│
│     │Image │     │          │    │ Image │    │
└──────────────────┘          └──────────────────┘
         ↓                             ↓
    Visible seam              Seamless wrap
```

## Processing Parameters Summary

### Current Settings (Style #4 - Smooth)

```yaml
Resize:
  method: INTER_LANCZOS4
  target: (1500, 1800) pixels

CLAHE:
  enabled: true
  clip_limit: 1.3
  tile_size: [24, 24]

Bilateral Filter:
  enabled: true
  diameter: 7
  sigma_color: 60
  sigma_space: 60

Thickness Mapping:
  min_thickness: 0.5 mm
  max_thickness: 2.2 mm
  gamma: 1.0
  edge_blend_width: 4.0 mm
```

### Alternative Styles (Available in tests/styles/)

**Style #1 - Minimal:**
```yaml
# No processing, just resize
CLAHE: disabled
Bilateral: disabled
Result: Natural, minimal intervention
```

**Style #2 - Natural:**
```yaml
CLAHE: clip=1.0, tiles=(32,32)
Bilateral: d=3, sigma=30
Result: Very subtle enhancement
```

**Style #3 - Balanced:**
```yaml
CLAHE: clip=1.5, tiles=(16,16)
Bilateral: d=5, sigma=40
Result: Moderate enhancement
```

**Style #4 - Smooth (CURRENT):**
```yaml
CLAHE: clip=1.3, tiles=(24,24)
Bilateral: d=7, sigma=60
Result: Smooth faces, clean results
```

**Style #5 - Detailed:**
```yaml
CLAHE: clip=2.0, tiles=(12,12)
Bilateral: d=3, sigma=30
Result: Maximum detail, some texture
```

## Modifying Processing Parameters

### To Adjust Processing Strength

**File:** `src/processing/simple_processor.py`

**Make faces smoother:**
```python
clahe = cv2.createCLAHE(
    clipLimit=1.0,        # Even gentler (was 1.3)
    tileGridSize=(32, 32) # Even larger tiles (was 24,24)
)

smoothed = cv2.bilateralFilter(
    enhanced,
    d=9,              # Stronger smoothing (was 7)
    sigmaColor=80,    # More aggressive (was 60)
    sigmaSpace=80
)
```

**Add more detail:**
```python
clahe = cv2.createCLAHE(
    clipLimit=2.0,        # Stronger enhancement (was 1.3)
    tileGridSize=(16, 16) # Smaller tiles (was 24,24)
)

smoothed = cv2.bilateralFilter(
    enhanced,
    d=5,              # Less smoothing (was 7)
    sigmaColor=40,    # Less aggressive (was 60)
    sigmaSpace=40
)
```

### To Adjust Brightness/Contrast

**File:** `src/processing/thickness_mapper.py`

**Make lithophane brighter overall:**
```python
# Increase gamma to darken mid-tones (more thin areas)
gamma = 0.9  # Was 1.0
```

**Make lithophane darker overall:**
```python
# Decrease gamma to brighten mid-tones (more thick areas)
gamma = 1.1  # Was 1.0
```

**Increase contrast:**
```python
# Widen thickness range
min_thickness = 0.4  # Was 0.5
max_thickness = 2.5  # Was 2.2
```

## Testing Your Changes

### Quick Test Process

1. **Modify parameters** in `simple_processor.py` or `thickness_mapper.py`
2. **Run the application** and generate a test lithophane
3. **Load STL in slicer** and preview with transparency
4. **Compare results** - smoother? more detail? better contrast?
5. **Iterate** until satisfied

### Batch Testing with Styles

Use the style testing system for rapid iteration:

1. **Create new style YAML** in `tests/styles/`
2. **Run test generator:** `python generate_test_styles.py`
3. **Compare all STLs** in your slicer
4. **Select best style** and update `simple_processor.py`

## Common Issues and Solutions

### Problem: Face looks too noisy/textured

**Cause:** CLAHE amplifying skin texture
**Solution:** Increase tile size and/or lower clip_limit
```python
clipLimit=1.0, tileGridSize=(32, 32)
```

### Problem: Face looks too blurry/soft

**Cause:** Bilateral filter too aggressive
**Solution:** Reduce diameter and sigma
```python
d=5, sigmaColor=40, sigmaSpace=40
```

### Problem: Image too dark when printed

**Cause:** Thickness range too thick
**Solution:** Reduce max thickness or adjust gamma
```python
gamma = 0.9  # Brightens mid-tones
```

### Problem: Not enough contrast

**Cause:** Thickness range too narrow
**Solution:** Widen thickness range
```python
min_thickness = 0.4
max_thickness = 2.5
```

### Problem: Visible seam at wrap-around

**Cause:** Edge blending too narrow
**Solution:** Increase edge blend width
```python
edge_blend_width = 6.0  # Was 4.0
```

## Performance Notes

### Processing Time Breakdown

For 4000×3000 input image → 1500×1800 output:

- **Resize**: ~200ms (Lanczos4)
- **CLAHE**: ~150ms (1500×1800 with 24×24 tiles)
- **Bilateral**: ~800ms (d=7, 1500×1800)
- **Thickness mapping**: ~50ms (simple math)
- **Total**: ~1.2 seconds

### Memory Usage

- Input image: ~40MB (4000×3000×3 channels)
- Grayscale: ~14MB (4000×3000×1 channel)
- Resized: ~3MB (1500×1800)
- Processing buffers: ~10MB
- **Peak**: ~70MB for image processing

### Optimization Opportunities

**Current approach is already well-optimized:**
- OpenCV functions are highly optimized (C++)
- Bilateral filter is the slowest operation (~70% of time)
- Further optimization would require:
  - GPU acceleration (CUDA)
  - Custom filter implementations
  - Reduced resolution (quality tradeoff)

**Not recommended unless processing time becomes an issue.**

---

**Processing Philosophy:** Simple, predictable, high-quality results with minimal intervention.
