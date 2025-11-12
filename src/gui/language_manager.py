#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Language Manager for Lithophane Lamp Generator
Handles multilingual support with Hebrew and English translations.
"""

from typing import Dict, Any


class LanguageManager:
    """
    Manages application translations and language switching.
    
    Supports Hebrew (RTL) and English (LTR) languages with
    complete UI text translations.
    """
    
    def __init__(self):
        self.current_language = 'he'
        self.translations = {
            'he': {
                'window_title': 'מחולל מנורות ליטופן',
                'main_title': 'מחולל מנורות ליטופן',
                'file_selection': 'בחירת קבצים',
                'select_image': '📁 בחר תמונה',
                'no_image_selected': 'לא נבחרה תמונה',
                'select_output': '💾 בחר מיקום שמירה',
                'no_output_selected': 'לא נבחר מיקום שמירה',
                'create_lamp': 'יצירת מנורה',
                'create_button': '🌟 צור מנורה',
                'specs': 'מפרטים: גליל ⌀60mm × 130mm, חלול',
                'progress': 'התקדמות',
                'activity_log': 'לוג פעילות',
                'preview': 'תצוגה מקדימה',
                'preview_text': '''יצירת מנורות ליטופן

בחר תמונה להתחלת תהליך יצירת 
מנורת הליטופן שלך.

פורמטים נתמכים:
• JPEG, PNG, BMP, TIFF
• כל גודל ורזולוציה
• צבע או גווני אפור

מושלם עבור:
• תמונות זוגיות רומנטיות
• זכרונות משפחתיים
• מתנות אישיות מיוחדות

איכות פרימיום מובטחת!''',
                'ready_status': 'מוכן ליצירת מנורות ליטופן',
                'image_selected': 'תמונה נבחרה: {}',
                'output_selected': 'שמירה ב: {}',
                'creation_success': 'יצירה הושלמה בהצלחה',
                'creation_failed': 'יצירה נכשלה',
                'analyzing_image': 'מנתח מאפייני תמונה...',
                'processing_image': 'מעבד תמונה לאיכות פרימיום...',
                'building_cylinder': 'בונה גליל תלת מימדי באיכות פרימיום...',
                'exporting_stl': 'מייצא קובץ STL מוכן להדפסה...',
                'lamp_completed': 'מנורת ליטופן הושלמה בהצלחה!',
                'file_selected_prefix': 'נבחר:',
                'save_as_prefix': 'שמירה בשם:',

                # Settings dialog
                'settings_button': 'הגדרות',
                'specs_format': 'מפרטים: גליל ⌀{diameter}mm × {height}mm, זווית {angle}°',
                'error_title': 'שגיאה',
                'settings_title': 'הגדרות',
                'settings_subtitle': 'בחרו פרופיל איכות והתאימו לפי הצורך',
                'quick_presets_section': '⚡ פרופילים מהירים',
                'presets_info': 'בחרו פרופיל בהתאם לצורך:',
                'preset_fast_title': '⚡ מהיר',
                'preset_fast_desc': 'עיבוד מהיר לבדיקות או טיוטות',
                'preset_fast_time': '~5-10 דקות',
                'preset_balanced_title': '⚖️ מאוזן',
                'preset_balanced_desc': 'איכות טובה עם זמן עיבוד סביר (מומלץ)',
                'preset_balanced_time': '~10-15 דקות',
                'preset_quality_title': '💎 איכות גבוהה',
                'preset_quality_desc': 'מקסימום פרטים ואיכות להדפסות סופיות',
                'preset_quality_time': '~20-30 דקות',
                'basic_settings_section': '🔧 הגדרות בסיסיות',
                'cylinder_size_label': 'גודל גליל:',
                'size_small': 'קטן (⌀40mm × 100mm)',
                'size_standard': 'סטנדרטי (⌀60mm × 130mm)',
                'size_large': 'גדול (⌀80mm × 150mm)',
                'size_custom': 'מותאם אישית...',
                'size_note': '💡 הקוטר הפנימי מתאים לסרטי LED סטנדרטיים',
                'diameter_label': 'קוטר:',
                'height_label': 'גובה:',
                'advanced_toggle_show': '▶ הצג הגדרות מתקדמות',
                'advanced_toggle_hide': '▼ הסתר הגדרות מתקדמות',
                'light_range_group': '💡 טווח מעבר אור',
                'bright_areas': 'אזורים בהירים:',
                'dark_areas': 'אזורים כהים:',
                'light_range_warning': '⚠️  0.5-2.2mm מכויל ל-PLA לבן עם תאורת LED',
                'other_settings_group': '⚙️ הגדרות נוספות',
                'coverage_angle_label': 'זווית כיסוי:',
                'detail_enhancement_label': 'שיפור פרטים',
                'reset_defaults': '↺ אפס לברירות מחדל',
                'cancel': 'ביטול',
                'save_apply': '✓ שמור והחל',
                'back': '← חזרה',

                # 2025 Simplified Settings
                'coverage_angle_section_title': 'זווית כיסוי ליטופן',
                'coverage_angle_description': 'קבעו כמה מהגליל יכוסה בתמונה. 200° מומלץ לרוב התמונות.',
                'coverage_angle_guide': '💡 טיפ: 200° = כיסוי מפואר | 180° = חצי גליל | 360° = מעגל שלם',
                'quality_locked_title': 'איכות נעולה למקסימום',
                'quality_locked_description': 'כל ההגדרות נעולות לאיכות מקסימלית. אין צורך בפשרות.',
                'resolution_section_title': 'רזולוציית עיבוד',
                'resolution_description': 'רזולוציה נמוכה יותר = פרטים עדינים יותר אך עיבוד איטי יותר.',
                'resolution_label': 'רזולוציה',
                'resolution_guide': '⏱️ 0.06mm = איכות מקסימלית (~25 דק) | 0.08mm = מומלץ (~15 דק) | 0.15mm = מהיר (~8 דק)',
                'gamma_section_title': 'תיקון גאמא',
                'gamma_description': 'קבעו את בהירות התמונה. ערכים נמוכים = בהיר יותר, ערכים גבוהים = כהה יותר.',
                'gamma_auto_label': 'זיהוי אוטומטי (מומלץ)',
                'gamma_value_label': 'ערך גאמא',
                'gamma_guide': '💡 ערכים: <1.0 = מבהיר | 1.0 = מקורי | >1.0 = מכהה',
                'autocrop_section_title': 'חיתוך אוטומטי חכם לפורטרטים',
                'autocrop_description': 'כאשר פנים קטנות מדי בתמונה, המערכת חותכת אוטומטית להתמקדות בפנים.',
                'autocrop_enable_label': 'אפשר חיתוך אוטומטי (מומלץ לתמונות עם פנים קטנות)',
                'autocrop_guide': '💡 מופעל רק כאשר הפנים תופסות פחות מ-30% מהתמונה. משפר באופן דרמטי את איכות פרטי הפנים.',
                'optimized_pipeline_section_title': 'מנוע עיבוד חדש ומשופר',
                'optimized_pipeline_description': 'מנוע עיבוד חדש לחלוטין המשמר פרטי פנים. ללא החלקה מזיקה!',
                'optimized_pipeline_enable_label': '✨ השתמש במנוע החדש (מומלץ מאוד לפורטרטים)',
                'optimized_pipeline_guide': '🚀 חדש! שומר על עיניים, אף ופה. קוד פשוט וברור ב-70% פחות שורות.',
                'always_enabled': 'פעיל תמיד'
            },
            'en': {
                'window_title': 'Lithophane Lamp Generator',
                'main_title': 'Lithophane Lamp Generator',
                'file_selection': 'File Selection',
                'select_image': '📁 Select Image',
                'no_image_selected': 'No image selected',
                'select_output': '💾 Select Save Location',
                'no_output_selected': 'No save location selected',
                'create_lamp': 'Create Lamp',
                'create_button': '🌟 Create Lamp',
                'specs': 'Specs: Cylinder ⌀60mm × 130mm, hollow',
                'progress': 'Progress',
                'activity_log': 'Activity Log',
                'preview': 'Preview',
                'preview_text': '''Lithophane Lamp Creation

Select an image to start creating 
your lithophane lamp.

Supported formats:
• JPEG, PNG, BMP, TIFF
• Any size and resolution
• Color or grayscale

Perfect for:
• Romantic couple photos
• Family memories
• Special personal gifts

High quality guaranteed!''',
                'ready_status': 'Ready to create lithophane lamps',
                'image_selected': 'Image selected: {}',
                'output_selected': 'Save to: {}',
                'creation_success': 'Creation completed successfully',
                'creation_failed': 'Creation failed',
                'analyzing_image': 'Analyzing image characteristics...',
                'processing_image': 'Processing image to high quality...',
                'building_cylinder': 'Building 3D cylinder with high quality...',
                'exporting_stl': 'Exporting STL file ready for printing...',
                'lamp_completed': 'Lithophane lamp completed successfully!',
                'file_selected_prefix': 'Selected:',
                'save_as_prefix': 'Save as:',

                # Settings dialog
                'settings_button': 'Settings',
                'specs_format': 'Specs: Cylinder ⌀{diameter}mm × {height}mm, {angle}° coverage',
                'error_title': 'Error',
                'settings_title': 'Settings',
                'settings_subtitle': 'Choose a quality preset and adjust if needed',
                'quick_presets_section': '⚡ Quick Presets',
                'presets_info': 'Choose a preset based on your needs:',
                'preset_fast_title': '⚡ Fast',
                'preset_fast_desc': 'Quick processing for testing or drafts',
                'preset_fast_time': '~5-10 minutes',
                'preset_balanced_title': '⚖️ Balanced',
                'preset_balanced_desc': 'Good quality with reasonable processing time (Recommended)',
                'preset_balanced_time': '~10-15 minutes',
                'preset_quality_title': '💎 High Quality',
                'preset_quality_desc': 'Maximum detail and quality for final prints',
                'preset_quality_time': '~20-30 minutes',
                'basic_settings_section': '🔧 Basic Settings',
                'cylinder_size_label': 'Cylinder Size:',
                'size_small': 'Small (⌀40mm × 100mm)',
                'size_standard': 'Standard (⌀60mm × 130mm)',
                'size_large': 'Large (⌀80mm × 150mm)',
                'size_custom': 'Custom...',
                'size_note': '💡 The inner diameter will fit standard LED strips',
                'diameter_label': 'Diameter:',
                'height_label': 'Height:',
                'advanced_toggle_show': '▶ Show Advanced Settings',
                'advanced_toggle_hide': '▼ Hide Advanced Settings',
                'light_range_group': '💡 Light Transmission Range',
                'bright_areas': 'Bright areas:',
                'dark_areas': 'Dark areas:',
                'light_range_warning': '⚠️  0.5-2.2mm is calibrated for white PLA with LED lighting',
                'other_settings_group': '⚙️ Other Settings',
                'coverage_angle_label': 'Coverage Angle:',
                'detail_enhancement_label': 'Detail enhancement',
                'reset_defaults': '↺ Reset to Defaults',
                'cancel': 'Cancel',
                'save_apply': '✓ Save & Apply',
                'back': '← Back',

                # 2025 Simplified Settings
                'coverage_angle_section_title': 'Lithophane Coverage Angle',
                'coverage_angle_description': 'Set how much of the cylinder will be covered by the image. 200° is recommended for most images.',
                'coverage_angle_guide': '💡 Tip: 200° = nice wrap | 180° = half cylinder | 360° = full circle',
                'quality_locked_title': 'Quality Locked to Maximum',
                'quality_locked_description': 'All settings are locked to maximum quality. No compromises needed.',
                'resolution_section_title': 'Processing Resolution',
                'resolution_description': 'Lower resolution = finer details but slower processing.',
                'resolution_label': 'Resolution',
                'resolution_guide': '⏱️ 0.06mm = max quality (~25 min) | 0.08mm = recommended (~15 min) | 0.15mm = fast (~8 min)',
                'gamma_section_title': 'Gamma Correction',
                'gamma_description': 'Control image brightness. Lower values = brighter, higher values = darker.',
                'gamma_auto_label': 'Auto-detect (Recommended)',
                'gamma_value_label': 'Gamma Value',
                'gamma_guide': '💡 Values: <1.0 = brighten | 1.0 = original | >1.0 = darken',
                'autocrop_section_title': 'Smart Portrait Auto-Crop',
                'autocrop_description': 'When face is too small in image, system automatically crops to focus on face.',
                'autocrop_enable_label': 'Enable auto-crop (recommended for images with small faces)',
                'autocrop_guide': '💡 Only activates when face is less than 30% of image. Dramatically improves facial detail quality.',
                'optimized_pipeline_section_title': 'New Optimized Processing Engine',
                'optimized_pipeline_description': 'Brand new processing engine that preserves facial details. NO harmful smoothing!',
                'optimized_pipeline_enable_label': '✨ Use new engine (highly recommended for portraits)',
                'optimized_pipeline_guide': '🚀 NEW! Preserves eyes, nose, mouth. Simpler code with 70% fewer lines.',
                'always_enabled': 'Always enabled'
            }
        }
    
    def get_text(self, key: str) -> str:
        """
        Get translated text for the given key.
        
        Args:
            key: Translation key
            
        Returns:
            Translated text or the key itself if not found
        """
        return self.translations[self.current_language].get(key, key)
    
    def set_language(self, language: str) -> bool:
        """
        Set the current language.
        
        Args:
            language: Language code ('he' or 'en')
            
        Returns:
            True if language was set successfully, False otherwise
        """
        if language in self.translations:
            self.current_language = language
            return True
        return False
    
    def get_available_languages(self) -> Dict[str, str]:
        """
        Get available languages with their display names.
        
        Returns:
            Dictionary mapping language codes to display names
        """
        return {
            'he': 'עברית',
            'en': 'English'
        }
    
    def is_rtl(self) -> bool:
        """
        Check if current language is right-to-left.
        
        Returns:
            True if RTL language (Hebrew), False otherwise
        """
        return self.current_language == 'he'
