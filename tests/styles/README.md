# Processing Styles for Lithophane Generator

## Quick Reference

| Style | CLAHE | Smoothing | Best For |
|-------|-------|-----------|----------|
| **1_minimal** | None | None | High-quality originals, natural tones |
| **2_natural** | Very Light | Gentle | Well-lit portraits |
| **3_balanced** | Moderate | Moderate | All-around (current default) |
| **4_smooth** | Light | Heavy | Clean faces, minimal texture |
| **5_detailed** | Strong | Minimal | Sharp images, maximum detail |

## Testing Instructions

1. Run the generator with SABA.jpg
2. Each style will create: `output_style1.stl`, `output_style2.stl`, etc.
3. Compare the 5 STL files in your slicer
4. Tell Claude which number you prefer!

## What Each Parameter Does

**CLAHE (Contrast Limited Adaptive Histogram Equalization):**
- `clip_limit`: Higher = more contrast (0.5-3.0)
- `tile_size`: Larger = smoother enhancement

**Bilateral Filter (Smoothing):**
- `diameter`: Larger = more smoothing
- `sigma_color`: How similar colors get smoothed together
- `sigma_space`: Spatial distance for smoothing

## Quick Decision Guide

- **Too noisy/textured?** → Try Style 4 (Smooth)
- **Too flat/lifeless?** → Try Style 5 (Detailed)
- **Want natural look?** → Try Style 2 (Natural)
- **Not sure?** → Start with Style 3 (Balanced)
