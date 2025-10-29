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
                'save_as_prefix': 'שמירה בשם:'
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

Premium quality guaranteed!''',
                'ready_status': 'Ready to create lithophane lamps',
                'image_selected': 'Image selected: {}',
                'output_selected': 'Save to: {}',
                'creation_success': 'Creation completed successfully',
                'creation_failed': 'Creation failed',
                'analyzing_image': 'Analyzing image characteristics...',
                'processing_image': 'Processing image to premium quality...',
                'building_cylinder': 'Building 3D cylinder with premium quality...',
                'exporting_stl': 'Exporting STL file ready for printing...',
                'lamp_completed': 'Lithophane lamp completed successfully!',
                'file_selected_prefix': 'Selected:',
                'save_as_prefix': 'Save as:'
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