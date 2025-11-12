# User Guide - Lithophane Lamp Generator

## What is a Lithophane?

A lithophane is a thin, translucent image that reveals a picture when backlit. When 3D printed in white PLA and illuminated with LEDs, your photos transform into glowing works of art.

**How it works:**
- **Thin areas** (0.5mm) = More light passes through = Bright areas of image
- **Thick areas** (2.2mm) = Less light passes through = Dark areas of image
- The varying thickness creates a beautiful grayscale image when lit from behind

## Getting Started

### Installation

1. **Download** the application
2. **Install Python 3.8+** if not already installed
3. **Open terminal/command prompt** in the application folder
4. **Run:** `pip install -r requirements.txt`
5. **Launch:** Double-click `run.bat` (Windows) or run `python main.py`

### System Requirements

- **Operating System:** Windows 10/11, macOS, or Linux
- **RAM:** 4GB minimum, 8GB recommended
- **Disk Space:** 100MB for application + space for STL files
- **Python:** 3.8 or higher

## Step-by-Step Tutorial

### Step 1: Choose Your Photo

**Best images for lithophanes:**
- ✅ **Portraits** with clear faces
- ✅ **Well-lit photos** with good contrast
- ✅ **Close-up shots** rather than distant subjects
- ✅ **Simple backgrounds** work better than busy ones
- ✅ **High resolution** (2000+ pixels) for best quality

**Avoid:**
- ❌ Very dark or very bright photos
- ❌ Heavily compressed/low quality images
- ❌ Photos with too many small details
- ❌ Images with important details at edges (will wrap around)

**Supported formats:**
- JPEG/JPG (most common)
- PNG
- BMP
- TIFF
- HEIC (iPhone photos)

### Step 2: Launch the Application

**Windows:**
- Double-click `run.bat`
- Or open Command Prompt and run: `python main.py`

**macOS/Linux:**
- Open Terminal
- Navigate to application folder
- Run: `python main.py`

### Step 3: Select Your Image

1. Click the **"Select Image"** button
2. Browse to your photo
3. Select the file and click **"Open"**
4. The file path will appear in the application

**Tips:**
- Make a copy of your photo first (application doesn't modify originals)
- Use a descriptive filename for easy identification
- Keep photos organized in a dedicated folder

### Step 4: Choose Output Location

1. Click the **"Select Output"** button
2. Navigate to where you want to save the STL file
3. Enter a filename (e.g., `family_portrait.stl`)
4. Click **"Save"**

**File naming tips:**
- Use descriptive names: `mom_birthday_2024.stl`
- Avoid special characters
- Add date or version if making multiple versions
- Default location works fine if unsure

### Step 5: Create the Lithophane

1. Click the **"Create Lithophane"** button
2. Watch the progress bar
3. Processing stages:
   - **Validating** (0-15%) - Checking your image
   - **Processing** (15-35%) - Enhancing for smooth results
   - **Building** (35-85%) - Creating 3D cylinder mesh
   - **Exporting** (85-100%) - Saving STL file

**Processing time:**
- Small images (2000×1500): 15-20 seconds
- Large images (4000×3000): 25-35 seconds
- Very large (6000×4000): 40-60 seconds

**What's happening:**
- Image is resized to optimal dimensions
- Contrast is gently enhanced for detail
- Smoothing is applied for clean faces
- 3D cylinder mesh is generated
- STL file is created and saved

### Step 6: Success!

When complete, you'll see a success dialog with:
- **Cylinder dimensions** (Ø60mm × 130mm)
- **Mesh quality** (vertices, faces)
- **File size** (typically 15-25 MB)
- **Processing time**
- **Technical specifications**

Click **"Open Folder"** to view your STL file.

## 3D Printing Your Lithophane

### Required Equipment

- **3D Printer** (FDM type - Ender 3, Prusa, etc.)
- **Filament:** White PLA, 1.75mm
- **Slicer Software:** PrusaSlicer, Cura, or similar
- **LED Strip:** For backlighting (12V or 5V)

### Optimal Slicer Settings

**Critical settings for best quality:**

```
Material: White PLA
Layer Height: 0.12mm (high quality) or 0.16mm (balanced)
Nozzle: 0.4mm
Nozzle Temperature: 200-210°C
Bed Temperature: 60°C
Print Speed: 40-50 mm/s (slow for quality!)
Wall Lines: 2-3 perimeters
Infill: 15-20% (structural support)
Cooling: 100% fan after first layer
Supports: Auto (if needed for overhangs)
Brim/Raft: Recommended for better adhesion
```

**Why these settings matter:**

- **White PLA:** Required for light transmission
- **0.12mm layers:** Smooth surface, fine detail
- **Slow speed:** Better layer adhesion, fewer artifacts
- **100% cooling:** Prevents drooping, sharper details

### Print Orientation

**Correct way:** Stand cylinder upright (vertically)
```
     Top
      ↑
   ┌─────┐
   │     │  ← Cylinder stands on Z-axis
   │     │
   │     │
   └─────┘
    Bottom
   (on bed)
```

**Why vertical:**
- Layers run horizontally (best for lithophane effect)
- Light shines through layers correctly
- Minimal supports needed
- Better structural integrity

### First Layer Tips

- **Clean bed** thoroughly (isopropyl alcohol)
- **Level bed** carefully
- **Z-offset** properly calibrated
- **Watch first layer** to ensure adhesion
- **Use brim** for large cylinders (reduces warping)

### During Printing

**Monitor for:**
- First layer adhesion
- Layer consistency
- No stringing or blobs
- Proper cooling (no drooping)

**Print time:** 8-15 hours depending on size and settings

**Material usage:** ~40-60 grams of PLA

### After Printing

1. **Let cool completely** before removing from bed
2. **Remove supports carefully** (if any)
3. **Clean up any strings** with craft knife
4. **Check for imperfections** on lithophane surface
5. **Sand lightly** if needed (400+ grit sandpaper)

## LED Integration

### Choosing LED Strip

**Recommended:**
- **Type:** LED strip, warm white (2700-3000K)
- **Voltage:** 12V or 5V (USB-powered)
- **Brightness:** Medium (too bright washes out image)
- **Width:** Must fit inside 56mm inner diameter

**Popular options:**
- USB LED strip (5V, easy to power)
- 12V LED strip with adapter
- Battery-powered LED strip (portable)

### Installation

1. **Measure inside height** of cylinder (~126mm)
2. **Cut LED strip** to appropriate length
3. **Test LEDs** before final installation
4. **Insert strip** inside cylinder
5. **Arrange evenly** for uniform lighting
6. **Secure with tape** if needed
7. **Run power cable** through bottom or top
8. **Connect to power source**
9. **Test brightness** and adjust if possible

### Lighting Tips

**Best results:**
- **Medium brightness** - Too bright washes out details
- **Warm white** - More natural skin tones
- **Even distribution** - Avoid hot spots
- **Diffuser** (optional) - Smooth light, reduces LED spots

**Dimmer highly recommended** for brightness control.

## Tips for Best Results

### Photo Selection

**Great subjects:**
- Family portraits
- Pet photos (faces work best)
- Wedding photos
- Baby pictures
- Memorial photos
- Landscape with strong foreground subject

**Photo tips:**
- Face camera straight on (not profile)
- Good lighting (not backlit)
- Sharp focus (not blurry)
- High resolution original
- Simple, uncluttered background

### Processing Quality

**The application automatically:**
- Resizes to optimal dimensions
- Enhances contrast gently
- Smooths facial areas
- Creates clean, printable mesh

**You don't need to:**
- Pre-edit photos
- Adjust brightness/contrast
- Remove backgrounds
- Crop precisely

**The application handles it!**

### Common Issues

**Issue: Face looks blurry in print**
- **Cause:** Print speed too fast or layer height too large
- **Fix:** Reduce speed to 40 mm/s, use 0.12mm layers

**Issue: Face has visible lines**
- **Cause:** Layer height too large
- **Fix:** Use 0.12mm layers instead of 0.2mm

**Issue: Image too dark when lit**
- **Cause:** LEDs too dim or printed too thick
- **Fix:** Use brighter LEDs or reduce max thickness in settings

**Issue: Image too bright/washed out**
- **Cause:** LEDs too bright
- **Fix:** Use dimmer LEDs or add dimmer control

**Issue: Visible texture on face**
- **Cause:** Print quality (not application)
- **Fix:** Slow down print, increase cooling, use 0.12mm layers

**Issue: Cylinder warped during print**
- **Cause:** Bed adhesion or cooling issues
- **Fix:** Use brim, ensure bed level, 60°C bed temp

## Maintenance and Care

### Caring for Your Lithophane

- **Handle carefully** - Thin areas are delicate
- **Keep clean** - Dust with soft cloth
- **Avoid direct sunlight** - PLA can warp in heat
- **Don't bend** - PLA is rigid, can crack
- **Store upright** - Prevents warping

### LED Maintenance

- **Check connections** periodically
- **Replace burned out LEDs** as needed
- **Keep wiring neat** inside cylinder
- **Avoid overheating** (LEDs should stay cool)

## Troubleshooting

### Application Issues

**Application won't start:**
- Check Python installed (3.8+)
- Run: `pip install -r requirements.txt`
- Check console for error messages
- Try running: `python main.py` from terminal

**"Image file not found" error:**
- Verify file path is correct
- Check file isn't open in another program
- Ensure file hasn't been moved/deleted
- Try copying file to simple location

**Processing takes forever:**
- Large images (>4000px) take longer
- This is normal - wait patiently
- Check task manager - Python should be active
- Cancel and try smaller image if needed

**STL file won't open in slicer:**
- Check file size (should be 15-50 MB)
- Ensure file fully created (processing completed)
- Try different slicer software
- Check disk space available

### Print Issues

**Print fails partway through:**
- Check filament not tangled
- Ensure bed still level
- Verify nozzle not clogged
- Check slicer settings correct

**Poor quality print:**
- Slow down print speed (40-50 mm/s)
- Increase cooling to 100%
- Use 0.12mm layers
- Check filament quality
- Ensure bed properly leveled

**Lithophane too dark:**
- Use brighter LEDs
- Ensure white PLA (not colored)
- Check slicer used correct STL
- Verify wall thickness in slicer

**Image not visible:**
- Check LEDs are working
- Ensure cylinder not too thick (check print)
- Verify used white PLA
- Try brighter/more LEDs

## Frequently Asked Questions

**Q: What's the best type of photo?**
A: Well-lit portraits with clear faces work best. Avoid very dark or very bright photos.

**Q: Can I print in color?**
A: No, lithophanes require white PLA for light transmission. Color filament blocks too much light.

**Q: How long does printing take?**
A: Typically 8-15 hours depending on printer and settings. Quality takes time!

**Q: Can I make it bigger/smaller?**
A: Currently dimensions are fixed (Ø60mm × 130mm) for optimal results. Contact developer for custom sizes.

**Q: Do I need to edit my photo first?**
A: No! The application automatically optimizes your image. Use the original photo.

**Q: Can I print multiple images?**
A: Currently one image per cylinder. Future versions may support batch processing.

**Q: What if I don't have a 3D printer?**
A: Many local makerspaces, libraries, or print services can print STL files for you.

**Q: How much does it cost to print?**
A: ~40-60g of PLA filament (about $1-2) plus electricity. Very affordable!

**Q: Can I sell prints made with this?**
A: Check license terms. Generally OK for personal use and gifts. Commercial use may have restrictions.

**Q: Why use this instead of online generators?**
A: This application creates cylindrical lithophanes specifically optimized for LED backlighting, not flat lithophanes.

## Getting Help

### Resources

- **Documentation:** See `docs/` folder for technical details
- **Log File:** Check `lamp_generator.log` for errors
- **Settings:** See `config/settings.yaml` for configuration

### Reporting Issues

If you encounter a problem:

1. Check this user guide first
2. Review the log file (`lamp_generator.log`)
3. Try with a different image
4. Restart the application
5. Contact developer with:
   - Error message
   - Image characteristics
   - Log file contents
   - Steps to reproduce

## Gallery Ideas

### Gift Ideas

- **Birthday gifts** - Personalized lamp with birthday photos
- **Wedding gifts** - Couple's portrait
- **Mother's/Father's Day** - Family photos
- **Graduation** - Graduate's portrait
- **New baby** - Baby photos for grandparents
- **Memorial** - Remembrance lamp
- **Pet memorial** - Beloved pet photos

### Display Ideas

- **Bedside lamp** - Gentle nightlight
- **Office desk** - Personal touch
- **Shelf display** - Conversation piece
- **Restaurant table** - Ambient lighting
- **Event centerpiece** - Special occasions

### Creative Uses

- **Night light** for children
- **Mood lighting** in living room
- **Romantic lighting** for dinner
- **Photo booth** backup at events
- **Business branding** with logo

## Next Steps

1. ✅ **Choose a photo** you love
2. ✅ **Generate your first lithophane**
3. ✅ **Print it** with recommended settings
4. ✅ **Add LEDs** and light it up
5. ✅ **Share** your creation!
6. ✅ **Make more** - gifts for everyone!

---

**Happy printing! Transform your memories into illuminated art!**
