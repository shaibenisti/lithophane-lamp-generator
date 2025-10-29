# GUI Documentation

## Overview

The Premium Lithophane Lamp Generator features a modern, bilingual desktop interface built with PyQt6. The UI emphasizes clarity, professional aesthetics, and seamless Hebrew/English switching with full RTL/LTR layout support.

## Design Philosophy

### Visual Design
- **Dark Theme** - Professional Claude.ai-inspired color scheme
- **Minimalist Layout** - Clean, focused interface without clutter
- **Consistent Spacing** - 8px grid system for visual harmony
- **Rounded Corners** - Modern 6-8px border radius throughout
- **Accent Color** - Warm copper (#cc785c) for primary actions

### User Experience
- **Progressive Disclosure** - Information revealed as needed
- **Real-time Feedback** - Immediate visual response to all actions
- **Clear State Management** - Obvious enabled/disabled states
- **Bilingual First** - Equal quality in Hebrew and English
- **Accessible** - High contrast, clear typography

---

## Main Window Layout

```
┌────────────────────────────────────────────────────┐
│                             [עברית | English]      │  Header
├────────────────────────────────────────────────────┤
│                                                    │
│  ┌──────────────────────────────────────────────┐ │
│  │  File Selection                              │ │
│  │  [Select Image]                              │ │
│  │  Status: No image selected                   │ │
│  │  [Select Save Location]                      │ │
│  │  Status: No save location selected           │ │
│  └──────────────────────────────────────────────┘ │
│                                                    │
│  ┌──────────────────────────────────────────────┐ │
│  │  Create Lamp                                 │ │  Control Panel
│  │  [🌟 Create Lamp]                            │ │
│  │  Specs: Cylinder ⌀60mm × 130mm, hollow      │ │
│  └──────────────────────────────────────────────┘ │
│                                                    │
│  ┌──────────────────────────────────────────────┐ │
│  │  Progress                                    │ │
│  │  [████████░░] 80%                            │ │
│  │  Building 3D cylinder...                     │ │
│  └──────────────────────────────────────────────┘ │
│                                                    │
│  ┌──────────────────────────────────────────────┐ │
│  │  Activity Log                                │ │
│  │  [13:45:12] Image selected: photo.jpg       │ │
│  │  [13:45:20] Starting creation...             │ │
│  │  [13:45:25] Processing image...              │ │
│  └──────────────────────────────────────────────┘ │
│                                                    │
└────────────────────────────────────────────────────┘
│ Ready to create lithophane lamps                 │  Status Bar
└────────────────────────────────────────────────────┘
```

---

## Components

### 1. Language Selector (Segmented Control)

**Location:** Top-right header
**Type:** Custom `SegmentedControl` widget

#### Visual Design

**Inactive State:**
```
┌──────────────────────────┐
│  עברית  │  English       │
│  ████   │                │  ← Active segment highlighted
└──────────────────────────┘
```

**Features:**
- Both languages visible simultaneously
- Active segment highlighted in accent color (#cc785c)
- Inactive segment in muted gray (#999999)
- Smooth hover effect (subtle background change)
- Rounded container background (#2d2d2d)
- Pointer cursor on hover

**Implementation:**
```python
# Location: src/gui/segmented_control.py
class SegmentedControl(QWidget):
    selectionChanged = pyqtSignal(int, str)  # Emitted on click
```

**Styling:**
- **Container:** 42px height, 8px border radius, #2d2d2d background
- **Segments:** 36px height, 6px border radius
- **Active:** #cc785c background, white text, bold
- **Inactive:** Transparent background, #999999 text
- **Hover:** Slight brightness increase

#### Behavior
- Click to switch language
- Instant UI update (all text changes)
- Layout direction switches (RTL ↔ LTR)
- Font optimization (Tahoma for Hebrew, Segoe UI for English)

---

### 2. File Selection Section

**Location:** Top section of control panel
**Type:** `QGroupBox`

#### Components

**Select Image Button**
```python
QPushButton: "📁 בחר תמונה" / "📁 Select Image"
- Opens QFileDialog
- Filters: *.png *.jpg *.jpeg *.bmp *.tiff *.gif
- Validates on selection
```

**Image Status Label**
```python
QLabel: Dynamic status text
- Default: "לא נבחרה תמונה" / "No image selected" (gray, italic)
- Selected: "נבחר: filename.jpg" / "Selected: filename.jpg" (green, bold)
- Truncates long filenames (max 50 chars)
```

**Select Output Button**
```python
QPushButton: "💾 בחר מיקום שמירה" / "💾 Select Save Location"
- Opens QFileDialog (save mode)
- Default filename: lithophane_lamp_YYYYMMDD_HHMMSS.stl
- Validates write permissions
```

**Output Status Label**
```python
QLabel: Dynamic status text
- Default: "לא נבחר מיקום שמירה" / "No save location selected"
- Selected: "שמירה בשם: filename.stl" / "Save as: filename.stl"
```

#### Visual States

**Default (Empty):**
```
┌─────────────────────────────────┐
│ File Selection                  │
│                                 │
│ [📁 Select Image           ]   │
│ No image selected               │  ← Gray, italic
│                                 │
│ [💾 Select Save Location   ]   │
│ No save location selected       │  ← Gray, italic
└─────────────────────────────────┘
```

**Populated:**
```
┌─────────────────────────────────┐
│ File Selection                  │
│                                 │
│ [📁 Select Image           ]   │
│ Selected: couple_photo.jpg      │  ← Green, bold
│                                 │
│ [💾 Select Save Location   ]   │
│ Save as: lithophane_lamp_...    │  ← Green, bold
└─────────────────────────────────┘
```

---

### 3. Create Lamp Section

**Location:** Middle section of control panel
**Type:** `QGroupBox`

#### Create Button

**Visual Design:**
```python
QPushButton: "🌟 צור מנורה" / "🌟 Create Lamp"
- Height: 35px minimum
- Background: #cc785c (copper accent)
- Text: White, bold, 13px
- Border radius: 8px
```

**States:**

**Enabled (Ready):**
- Background: #cc785c
- Hover: #d97757 (lighter)
- Active: #b56849 (darker)
- Cursor: Pointer

**Disabled (Not Ready):**
- Background: #252525 (dark gray)
- Text: #666666 (muted)
- Border: #333333
- Cursor: Default

**Enabling Conditions:**
```python
enabled = (image_selected AND output_location_selected)
```

#### Specifications Label

**Visual:**
```python
QLabel: "מפרטים: גליל ⌀60mm × 130mm, חלול"
        "Specs: Cylinder ⌀60mm × 130mm, hollow"
- Color: #999999 (muted)
- Size: 10px
- Alignment: Center
```

Purpose: Reminds user of output dimensions

---

### 4. Progress Section

**Location:** Below create lamp section
**Type:** `QGroupBox`

#### Progress Bar

**Visual:**
```python
QProgressBar
- Height: 20px
- Background: #252525
- Fill color: #cc785c (accent)
- Border: #404040, 6px radius
- Text: Center-aligned percentage
```

**Behavior:**
- Hidden by default (visible=false)
- Shows during processing (0-100%)
- Animated smooth fill
- Hides on completion

#### Progress Status Label

**Visual:**
```python
QLabel: Dynamic status message
- Color: #cc785c (accent)
- Size: 11px
- Word wrap enabled
```

**Example Messages:**
```
Hebrew:
- "מנתח מאפייני תמונה..."
- "מעבד תמונה לאיכות פרימיום..."
- "בונה גליל תלת מימדי..."
- "מייצא קובץ STL מוכן להדפסה..."

English:
- "Analyzing image characteristics..."
- "Processing image to premium quality..."
- "Building 3D cylinder with premium quality..."
- "Exporting STL file ready for printing..."
```

---

### 5. Activity Log Section

**Location:** Bottom section (largest area)
**Type:** `QGroupBox`

#### Log Text Area

**Visual:**
```python
QTextEdit
- Minimum height: 300px
- Background: #252525
- Font: Consolas/Courier New (monospace)
- Size: 11px
- Color: #c9c7c5
- Read-only
- Auto-scroll to bottom
```

**Log Format:**
```
[13:45:12] Image selected: photo.jpg
[13:45:15] Output location selected: lamp.stl
[13:45:20] Starting lithophane lamp creation...
[13:45:22] Analyzing image characteristics...
[13:45:25] Image classification: Portrait (2 faces detected)
[13:45:30] Processing image to premium quality...
[13:45:55] Building 3D cylinder with premium quality...
[13:46:40] Exporting STL file ready for printing...
[13:46:45] Lithophane lamp creation completed successfully!
```

**Behavior:**
- Timestamps in `[HH:MM:SS]` format
- Auto-scrolls to newest entry
- Persists for session duration
- Bilingual (follows current language)

---

### 6. Status Bar

**Location:** Bottom of window
**Type:** `QStatusBar`

**Visual:**
```python
- Background: #252525
- Text color: #e8e6e3
- Height: ~25px
- Padding: 6px
- Border-top: 1px solid #404040
```

**Messages:**
```
Default: "מוכן ליצירת מנורות ליטופן" / "Ready to create lithophane lamps"
Processing: "יוצר מנורה..." / "Creating lamp..."
```

---

## Color Palette

### Primary Colors
```
Background (Main):     #1a1a1a  - Dark charcoal
Background (Panels):   #2d2d2d  - Medium dark gray
Background (Input):    #252525  - Darker gray
Accent (Primary):      #cc785c  - Warm copper
Accent (Hover):        #d97757  - Light copper
Accent (Active):       #b56849  - Dark copper
```

### Text Colors
```
Primary Text:          #e8e6e3  - Off-white
Secondary Text:        #c9c7c5  - Light gray
Muted Text:            #999999  - Medium gray
Disabled Text:         #666666  - Dark gray
Success Text:          #7fb069  - Green
```

### Border Colors
```
Primary Border:        #404040  - Medium border
Secondary Border:      #4a4a4a  - Lighter border
Input Border:          #333333  - Dark border
```

---

## Typography

### Font Families

**Hebrew (RTL):**
```python
Primary: Tahoma
Fallback: Arial Unicode MS, Segoe UI, Arial
```

**English (LTR):**
```python
Primary: Segoe UI
Fallback: Arial, sans-serif
```

**Monospace (Logs):**
```python
Primary: Consolas
Fallback: Courier New, monospace
```

### Font Sizes
```
Headers (GroupBox):    13px, weight 600
Buttons:               12-13px, weight 500-700
Body Text:             12px, weight 400
Status Labels:         11px
Specs/Hints:           10px
```

---

## Layout & Spacing

### Window Dimensions
```python
Initial size:    900×750px
Minimum size:    800×700px
Position:        100, 100 (from top-left)
```

### Spacing System (8px Grid)
```
Main margins:        20px (2.5× grid)
Section spacing:     15-20px
Component spacing:   8-10px
Padding (panels):    12px
Padding (buttons):   10px vertical, 16px horizontal
Border radius:       6-8px
```

### Control Panel
```python
Width:           600px minimum, 750px maximum
Centered:        Horizontal stretch layout (1:0:1)
```

---

## Internationalization (i18n)

### Language Switching

**Process:**
1. User clicks segment in language selector
2. `selectionChanged(index, lang_code)` signal emitted
3. `change_language(index, lang_code)` handler called
4. `LanguageManager.set_language(lang_code)` updates state
5. `update_layout_direction()` switches RTL ↔ LTR
6. `update_ui_language()` updates all text elements
7. `setup_language_selector_font()` optimizes fonts
8. Window repaints

**Updated Elements:**
- Window title
- All GroupBox titles
- All button text
- All labels (including dynamic status labels)
- Status bar message
- Language selector fonts

### RTL/LTR Handling

**Hebrew (RTL):**
```python
self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
- Text flows right-to-left
- UI mirrors horizontally
- Language selector stays top-right (visual left)
- Alignment preserved logically
```

**English (LTR):**
```python
self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
- Text flows left-to-right
- Standard UI layout
- Language selector top-right
```

**Font Optimization:**
- Hebrew uses Tahoma (best Hebrew rendering)
- English uses Segoe UI (modern, clean)
- Bold weight for language selector
- Size 12pt for optimal readability

---

## Dialogs

### File Selection Dialog

**Image Selection:**
```python
QFileDialog.getOpenFileName()
- Title: "Select image for lithophane lamp"
- Filters: "Image files (*.png *.jpg *.jpeg *.bmp *.tiff *.gif);;All files (*.*)"
- Returns: file_path
```

**Output Selection:**
```python
QFileDialog.getSaveFileName()
- Title: "Save lithophane lamp as"
- Default: "lithophane_lamp_20251029_134520.stl"
- Filters: "STL files (*.stl);;All files (*.*)"
- Returns: file_path
```

### Message Boxes

**Success:**
```python
QMessageBox.information(
    title="Success!",
    text="Lithophane lamp created successfully!\n\n"
         "File: lamp.stl\n"
         "Size: 2.5 MB\n"
         "Vertices: 1,234,567"
)
```

**Error:**
```python
QMessageBox.critical(
    title="Creation Error",
    text="Failed to create lithophane lamp:\n\n"
         "Error: Unable to read image file"
)
```

**Warning:**
```python
QMessageBox.warning(
    title="Image Quality Notice",
    text="Image selected successfully, but please note:\n\n"
         "• Low resolution (400×400) - will be upscaled\n"
         "• Heavy compression detected - may affect quality"
)
```

**Confirmation (on close during processing):**
```python
QMessageBox.question(
    title="Close Application",
    text="Creation is in progress. Are you sure you want to close?",
    buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
)
```

---

## Animations & Transitions

### Progress Bar
- Smooth fill animation (Qt default)
- Percentage updates in real-time
- Color transition on completion

### Segmented Control
- Instant state change (no animation)
- Hover effect: 50ms fade
- Color transition: background/text

### Language Switching
```python
self.setUpdatesEnabled(False)  # Freeze updates
# ... perform all changes ...
self.setUpdatesEnabled(True)   # Unfreeze
self.repaint()                 # Single repaint
```
Result: Instant, flicker-free language change

---

## Accessibility

### Keyboard Support
- Tab navigation through controls
- Enter/Space to activate buttons
- Escape to close dialogs
- Focus indicators visible

### Visual Accessibility
- High contrast ratios (WCAG AA compliant)
- 11-13px font sizes (readable)
- Clear button states
- Large click targets (35-42px height)

### Screen Reader Support
- Proper widget labels
- Status updates via text labels
- Button text describes action

---

## Customization Guide

### Changing Colors

**Edit `main_window.py`, `apply_styling()` method:**
```python
# Change accent color
QPushButton {
    background-color: #your-color;  # Replace #cc785c
}

QProgressBar::chunk {
    background-color: #your-color;  # Match accent
}
```

### Adding New Language

**1. Add translations to `language_manager.py`:**
```python
self.translations = {
    'he': { ... },
    'en': { ... },
    'fr': {  # New language
        'window_title': 'Générateur de Lampes Lithophane',
        ...
    }
}
```

**2. Update `get_available_languages()`:**
```python
return {
    'he': 'עברית',
    'en': 'English',
    'fr': 'Français'
}
```

**3. Add segment in `main_window.py`, `create_header()`:**
```python
self.language_selector.add_segment(available_langs['fr'], 'fr')
```

### Modifying Layout

**Control panel width:**
```python
# In create_control_panel()
panel.setMinimumWidth(600)  # Change minimum
panel.setMaximumWidth(750)  # Change maximum
```

**Window size:**
```python
# In initialize_interface()
self.setGeometry(100, 100, 900, 750)  # x, y, width, height
self.setMinimumSize(800, 700)         # min width, min height
```

---

## Best Practices

### When Adding UI Elements

1. **Add translations** to both Hebrew and English
2. **Use consistent spacing** (8px grid system)
3. **Follow color palette** (no new colors without reason)
4. **Test RTL layout** (ensure Hebrew display works)
5. **Add to `update_ui_language()`** if text changes

### Maintaining Visual Consistency

1. **Button height:** 35-42px
2. **Border radius:** 6-8px consistently
3. **Font sizes:** Use established sizes (10-13px)
4. **Colors:** Use palette variables, not hardcoded values
5. **Spacing:** Multiples of 8px

### Performance

1. **Batch UI updates** with `setUpdatesEnabled(False/True)`
2. **Heavy operations** in worker thread only
3. **Progress updates** no more than every 100ms
4. **Log entries** batch if rapid updates

---

## Troubleshooting

### Hebrew Text Not Rendering
- Install Tahoma font
- Check font families in `setup_language_selector_font()`
- Verify Unicode encoding (UTF-8)

### Layout Issues After Language Switch
- Ensure `update_layout_direction()` is called
- Check RTL-specific CSS
- Verify `setLayoutDirection()` is set

### Segmented Control Not Responding
- Check signal connection: `selectionChanged.connect()`
- Verify button group exclusivity
- Check button checkable state

### Dark Theme Not Applying
- Ensure `apply_styling()` is called after widget creation
- Check CSS syntax in stylesheet string
- Verify `setStyleSheet()` on correct widget

---

**For architecture details, see [ARCHITECTURE.md](ARCHITECTURE.md)**
**For configuration options, see [CONFIGURATION.md](CONFIGURATION.md)**
