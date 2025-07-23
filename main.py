#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import math
import logging
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional
from dataclasses import dataclass

import numpy as np
import cv2
import trimesh
from scipy.interpolate import RegularGridInterpolator

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QLabel, QFileDialog, QProgressBar, QMessageBox,
    QFrame, QTextEdit, QGroupBox, QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('lamp_generator.log'),
        logging.StreamHandler()
    ]
)

class LanguageManager:
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
                'lamp_completed': 'מנורת ליטופן הושלמה בהצלחה!'
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
                'lamp_completed': 'Lithophane lamp completed successfully!'
            }
        }
    
    def get_text(self, key):
        return self.translations[self.current_language].get(key, key)
    
    def set_language(self, language):
        if language in self.translations:
            self.current_language = language

@dataclass
class PremiumSettings:
    cylinder_diameter: float = 60.0
    cylinder_height: float = 130.0
    wall_thickness: float = 2.0
    nozzle_diameter: float = 0.4
    layer_height: float = 0.12
    min_thickness: float = 0.5
    max_thickness: float = 2.2
    resolution: float = 0.12
    mesh_quality_multiplier: float = 1.0
    lithophane_coverage_angle: float = 220.0
    top_margin: float = 2.0
    bottom_margin: float = 2.0
    edge_blend_width: float = 4.0
    detail_enhancement: bool = True
    
    def get_inner_radius(self) -> float:
        return (self.cylinder_diameter / 2) - self.wall_thickness
    
    def get_lithophane_dimensions(self) -> Tuple[int, int, float, float]:
        outer_radius = self.cylinder_diameter / 2
        angle_radians = math.radians(self.lithophane_coverage_angle)
        arc_length = outer_radius * angle_radians
        image_height = self.cylinder_height - self.top_margin - self.bottom_margin
        
        width_pixels = max(1000, int(arc_length / self.resolution))
        height_pixels = max(1200, int(image_height / self.resolution))
        
        return width_pixels, height_pixels, arc_length, image_height
    
    def get_mesh_resolution(self) -> Tuple[int, int]:
        circumference = math.pi * self.cylinder_diameter
        
        angular_segments = int(circumference / (self.resolution * 0.7))
        angular_segments = max(800, min(1400, angular_segments))
        
        height_segments = int(self.cylinder_height / (self.resolution * 0.7))
        height_segments = max(600, min(1200, height_segments))
        
        return angular_segments, height_segments


class IntelligentImageProcessor:
    """
    מעבד תמונות אינטליגנטי מתקדם לליטופן באיכות פרימיום.
    כולל זיהוי אוטומטי של סוג התמונה ועיבוד מותאם.
    """
    
    def __init__(self, settings: PremiumSettings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
    
    def analyze_image_characteristics(self, image: np.ndarray) -> dict:
        """
        ניתוח מתקדם של מאפייני התמונה לעיבוד אופטימלי.
        
        Args:
            image: תמונה בגווני אפור כ-numpy array
            
        Returns:
            מילון עם תוצאות ניתוח התמונה
        """
        mean_brightness = np.mean(image)
        std_deviation = np.std(image)
        
        hist = cv2.calcHist([image], [0], None, [256], [0, 256])
        hist_normalized = hist.flatten() / hist.sum()
        
        shadows = np.sum(hist_normalized[:64])
        highlights = np.sum(hist_normalized[192:])
        
        edges = cv2.Canny(image, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(image, 1.1, 4)
        has_faces = len(faces) > 0
        
        characteristics = {
            'mean_brightness': mean_brightness,
            'contrast_level': std_deviation,
            'shadow_ratio': shadows,
            'highlight_ratio': highlights,
            'edge_density': edge_density,
            'has_faces': has_faces,
            'face_count': len(faces),
            'faces': faces,
            'image_type': self._classify_image_type(mean_brightness, std_deviation, shadows, highlights, has_faces)
        }
        
        self.logger.info(f"ניתוח תמונה: {characteristics['image_type']}, "
                        f"בהירות={mean_brightness:.1f}, קונטרסט={std_deviation:.1f}, "
                        f"פנים={'כן' if has_faces else 'לא'}")
        
        return characteristics
    
    def _classify_image_type(self, brightness: float, contrast: float, 
                           shadows: float, highlights: float, has_faces: bool) -> str:
        """סיווג סוג התמונה לאסטרטגיית עיבוד מתאימה."""
        if has_faces:
            return "portrait" if contrast > 25 else "portrait_low_contrast"
        elif contrast < 25:
            return "low_contrast"
        elif brightness < 70:
            return "underexposed"
        elif brightness > 185:
            return "overexposed"
        elif shadows > 0.4:
            return "shadow_heavy"
        elif highlights > 0.3:
            return "highlight_heavy"
        else:
            return "balanced"
    
    def process_image_for_lithophane(self, image_path: str) -> np.ndarray:
        """
        עיבוד תמונה מתקדם לליטופן איכותי.
        
        Args:
            image_path: נתיב לתמונת הקלט
            
        Returns:
            מערך 2D המייצג מפת עובי במילימטרים
        """
        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        if image is None:
            raise ValueError(f"לא ניתן לטעון תמונה מ: {image_path}")
        
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        characteristics = self.analyze_image_characteristics(gray)
        processed = self._apply_intelligent_enhancement(gray, characteristics)
        
        target_width, target_height, _, _ = self.settings.get_lithophane_dimensions()
        resized = self._premium_resize(processed, target_width, target_height)
        
        thickness_map = self._create_calibrated_thickness_map(resized, characteristics)
        
        return thickness_map
    
    def _apply_intelligent_enhancement(self, image: np.ndarray, characteristics: dict) -> np.ndarray:
        """יישום שיפורי תמונה אינטליגנטיים לפי סוג התמונה."""
        enhanced = image.astype(np.float64)
        image_type = characteristics['image_type']
        
        if image_type == "portrait" or image_type == "portrait_low_contrast":
            enhanced = self._enhance_portrait(enhanced, characteristics)
        elif image_type == "underexposed":
            enhanced = self._correct_underexposure(enhanced)
        elif image_type == "overexposed":
            enhanced = self._recover_highlights(enhanced)
        elif image_type == "low_contrast":
            enhanced = self._enhance_contrast(enhanced)
        elif image_type == "shadow_heavy":
            enhanced = self._lift_shadows(enhanced)
        elif image_type == "highlight_heavy":
            enhanced = self._compress_highlights(enhanced)
        
        enhanced = self._apply_universal_enhancement(enhanced)
        
        return np.clip(enhanced, 0, 255).astype(np.uint8)
    
    def _enhance_portrait(self, image: np.ndarray, characteristics: dict) -> np.ndarray:
        gaussian_1 = cv2.GaussianBlur(image, (0, 0), 1.0)
        gaussian_2 = cv2.GaussianBlur(image, (0, 0), 2.5)
        
        detail_mask = image - gaussian_1
        structure_mask = gaussian_1 - gaussian_2
        
        sharpened = image + (detail_mask * 0.2) + (structure_mask * 0.1)
        
        clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
        enhanced = clahe.apply(sharpened.astype(np.uint8)).astype(np.float64)
        
        return enhanced
    
    def _correct_underexposure(self, image: np.ndarray) -> np.ndarray:
        normalized = image / 255.0
        corrected = np.power(normalized, 0.7)
        shadow_mask = normalized < 0.3
        corrected[shadow_mask] += 0.1 * (0.3 - normalized[shadow_mask])
        return corrected * 255.0
    
    def _recover_highlights(self, image: np.ndarray) -> np.ndarray:
        normalized = image / 255.0
        highlight_mask = normalized > 0.8
        compressed = np.power(normalized, 1.3)
        compressed[highlight_mask] = 0.8 + (normalized[highlight_mask] - 0.8) * 0.4
        return compressed * 255.0
    
    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """שיפור ניגודיות אדפטיבי."""
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        enhanced = clahe.apply(image.astype(np.uint8))
        return enhanced.astype(np.float64)
    
    def _lift_shadows(self, image: np.ndarray) -> np.ndarray:
        """הרמת פרטי צללים."""
        normalized = image / 255.0
        shadow_mask = normalized < 0.4
        enhanced = normalized.copy()
        enhanced[shadow_mask] = np.power(normalized[shadow_mask], 0.6)
        return enhanced * 255.0
    
    def _compress_highlights(self, image: np.ndarray) -> np.ndarray:
        """דחיסת הבהרות לשימור פרטים."""
        normalized = image / 255.0
        highlight_mask = normalized > 0.7
        compressed = normalized.copy()
        compressed[highlight_mask] = 0.7 + (normalized[highlight_mask] - 0.7) * 0.6
        return compressed * 255.0
    
    def _apply_universal_enhancement(self, image: np.ndarray) -> np.ndarray:
        denoised = cv2.bilateralFilter(image.astype(np.uint8), d=5, sigmaColor=30, sigmaSpace=30)
        denoised = cv2.bilateralFilter(denoised, d=7, sigmaColor=40, sigmaSpace=40)
        
        if self.settings.detail_enhancement:
            enhanced = self._professional_sharpening(denoised.astype(np.float64))
        else:
            enhanced = denoised.astype(np.float64)
        
        return enhanced
    
    def _professional_sharpening(self, image: np.ndarray) -> np.ndarray:
        gaussian_1 = cv2.GaussianBlur(image, (0, 0), 1.0)
        gaussian_2 = cv2.GaussianBlur(image, (0, 0), 3.0)
        
        detail_mask = image - gaussian_1
        structure_mask = gaussian_1 - gaussian_2
        
        sharpened = image + (detail_mask * 0.25) + (structure_mask * 0.15)
        return sharpened
    
    def _premium_resize(self, image: np.ndarray, target_width: int, target_height: int) -> np.ndarray:
        """שינוי גודל באיכות פרימיום לשימור פרטים מקסימלי."""
        current_height, current_width = image.shape
        
        if max(current_width, current_height) > max(target_width, target_height) * 2.5:
            intermediate_scale = max(target_width, target_height) * 2.0 / max(current_width, current_height)
            temp = cv2.resize(image, None, fx=intermediate_scale, fy=intermediate_scale, 
                             interpolation=cv2.INTER_CUBIC)
            final = cv2.resize(temp, (target_width, target_height), interpolation=cv2.INTER_LANCZOS4)
        else:
            final = cv2.resize(image, (target_width, target_height), interpolation=cv2.INTER_LANCZOS4)
        
        return final
    
    def _create_calibrated_thickness_map(self, processed_image: np.ndarray, 
                                       characteristics: dict) -> np.ndarray:
        normalized = processed_image.astype(np.float64) / 255.0
        
        gamma = self._calculate_optimal_gamma(characteristics)
        gamma_corrected = np.power(normalized, gamma)
        
        thickness_range = self.settings.max_thickness - self.settings.min_thickness
        base_thickness = self.settings.min_thickness + (gamma_corrected * thickness_range)
        
        blended_thickness = self._apply_cylindrical_blending(base_thickness)
        
        return blended_thickness
    
    def _calculate_optimal_gamma(self, characteristics: dict) -> float:
        """חישוב גמא אופטימלי לפי סוג התמונה."""
        image_type = characteristics['image_type']
        
        gamma_map = {
            'portrait': 0.9,
            'portrait_low_contrast': 0.8,
            'underexposed': 0.7,
            'overexposed': 1.2,
            'low_contrast': 0.85,
            'shadow_heavy': 0.75,
            'highlight_heavy': 1.1,
            'balanced': 1.0
        }
        
        return gamma_map.get(image_type, 1.0)
    
    def _apply_cylindrical_blending(self, thickness_map: np.ndarray) -> np.ndarray:
        height, width = thickness_map.shape
        blend_pixels = max(2, int(self.settings.edge_blend_width / self.settings.resolution))
        
        blend_mask = np.ones_like(thickness_map)
        
        for i in range(blend_pixels):
            factor = (i + 1) / blend_pixels
            if i < height:
                blend_mask[i, :] = np.minimum(blend_mask[i, :], factor)
                blend_mask[-(i+1), :] = np.minimum(blend_mask[-(i+1), :], factor)
            if i < width:
                blend_mask[:, i] = np.minimum(blend_mask[:, i], factor)
                blend_mask[:, -(i+1)] = np.minimum(blend_mask[:, -(i+1)], factor)
        
        blended = (thickness_map * blend_mask + 
                  self.settings.min_thickness * (1 - blend_mask))
        
        return blended


class PremiumCylinderBuilder:
    """
    בונה גלילים באיכות פרימיום למנורות ליטופן מסחריות.
    יוצר גלילים חלולים נקיים עם ליטופן משולב באיכות מקסימלית.
    """
    
    def __init__(self, settings: PremiumSettings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
    
    def create_premium_lithophane_cylinder(self, thickness_map: np.ndarray) -> trimesh.Trimesh:
        """
        יצירת גליל ליטופן פרימיום חלול עם איכות מקסימלית.
        
        Args:
            thickness_map: מערך 2D של ערכי עובי במילימטרים
            
        Returns:
            אובייקט trimesh איכותי מוכן לייצוא STL
        """
        self.logger.info("יוצר גליל ליטופן פרימיום...")
        
        outer_radius = self.settings.cylinder_diameter / 2
        inner_radius = self.settings.get_inner_radius()
        
        lithophane_angle_rad = math.radians(self.settings.lithophane_coverage_angle)
        start_angle = -lithophane_angle_rad / 2
        end_angle = lithophane_angle_rad / 2
        
        lithophane_start_z = self.settings.bottom_margin
        lithophane_end_z = self.settings.cylinder_height - self.settings.top_margin
        
        angular_segments, height_segments = self.settings.get_mesh_resolution()
        
        self.logger.info(f"רזולוציית mesh: {angular_segments} × {height_segments} segments")
        
        interpolator = self._create_precision_interpolator(thickness_map)
        
        vertices = self._generate_premium_vertices(
            interpolator, outer_radius, inner_radius,
            start_angle, end_angle, lithophane_start_z, lithophane_end_z,
            angular_segments, height_segments
        )
        
        faces = self._generate_optimized_faces(angular_segments, height_segments)
        
        mesh = self._create_validated_premium_mesh(vertices, faces)
        
        self.logger.info(f"גליל הושלם: {len(vertices)} vertices, {len(faces)} faces")
        
        return mesh
    
    def _create_precision_interpolator(self, thickness_map: np.ndarray) -> RegularGridInterpolator:
        """יצירת interpolator דיוק גבוה למיפוי עובי חלק."""
        img_height, img_width = thickness_map.shape
        
        pad_size = max(6, int(self.settings.edge_blend_width / self.settings.resolution))
        padded_map = np.pad(thickness_map, pad_size, mode='edge')
        
        kernel_size = max(5, pad_size // 2)
        if kernel_size % 2 == 0:
            kernel_size += 1
        smoothed_edges = cv2.GaussianBlur(padded_map.astype(np.float32), 
                                        (kernel_size, kernel_size), kernel_size / 2.5)
        
        blend_mask = np.ones_like(padded_map)
        for i in range(pad_size):
            factor = i / pad_size if pad_size > 0 else 1.0
            blend_mask[i, :] = np.minimum(blend_mask[i, :], factor)
            blend_mask[-(i+1), :] = np.minimum(blend_mask[-(i+1), :], factor)
            blend_mask[:, i] = np.minimum(blend_mask[:, i], factor)
            blend_mask[:, -(i+1)] = np.minimum(blend_mask[:, -(i+1)], factor)
        
        final_map = padded_map * blend_mask + smoothed_edges * (1 - blend_mask)
        
        y_coords = np.linspace(-pad_size, img_height + pad_size - 1, final_map.shape[0])
        x_coords = np.linspace(-pad_size, img_width + pad_size - 1, final_map.shape[1])
        
        return RegularGridInterpolator(
            (y_coords, x_coords), final_map,
            method='cubic', bounds_error=False, 
            fill_value=self.settings.min_thickness
        )
    
    def _generate_premium_vertices(self, interpolator, outer_radius: float, inner_radius: float,
                                 start_angle: float, end_angle: float,
                                 lithophane_start_z: float, lithophane_end_z: float,
                                 angular_segments: int, height_segments: int) -> np.ndarray:
        """יצירת vertices דיוק גבוה לגליל המש."""
        vertices = []
        
        angular_step = 2 * math.pi / angular_segments
        height_step = self.settings.cylinder_height / height_segments
        
        img_height, img_width = interpolator.values.shape
        lithophane_angle_range = end_angle - start_angle
        lithophane_height_range = lithophane_end_z - lithophane_start_z
        
        for height_idx in range(height_segments + 1):
            z_position = height_idx * height_step
            
            for angle_idx in range(angular_segments):
                current_angle = angle_idx * angular_step
                
                normalized_angle = current_angle if current_angle <= math.pi else current_angle - 2*math.pi
                
                effective_outer_radius = outer_radius
                
                if (lithophane_start_z <= z_position <= lithophane_end_z and
                    start_angle <= normalized_angle <= end_angle):
                    
                    u_coordinate = (normalized_angle - start_angle) / lithophane_angle_range
                    v_coordinate = (z_position - lithophane_start_z) / lithophane_height_range
                    
                    img_x = u_coordinate * (img_width - 1)
                    img_y = (1.0 - v_coordinate) * (img_height - 1)
                    
                    thickness_value = float(interpolator([img_y, img_x]))
                    
                    curvature_compensation = 1.0 + 0.03 * math.cos(normalized_angle * 0.8)
                    adjusted_thickness = thickness_value * curvature_compensation
                    
                    effective_outer_radius = outer_radius + adjusted_thickness
                
                x_outer = effective_outer_radius * math.cos(current_angle)
                y_outer = effective_outer_radius * math.sin(current_angle)
                vertices.append([x_outer, y_outer, z_position])
                
                x_inner = inner_radius * math.cos(current_angle)
                y_inner = inner_radius * math.sin(current_angle)
                vertices.append([x_inner, y_inner, z_position])
        
        return np.array(vertices)
    
    def _generate_optimized_faces(self, angular_segments: int, height_segments: int) -> np.ndarray:
        """יצירת faces מאופטמים לפני שטח חלק."""
        faces = []
        
        for height_idx in range(height_segments):
            for angle_idx in range(angular_segments):
                current_layer_base = height_idx * angular_segments * 2
                next_layer_base = (height_idx + 1) * angular_segments * 2
                
                current_angle_base = angle_idx * 2
                next_angle_base = ((angle_idx + 1) % angular_segments) * 2
                
                p1_outer = current_layer_base + current_angle_base
                p1_inner = current_layer_base + current_angle_base + 1
                p2_outer = current_layer_base + next_angle_base
                p2_inner = current_layer_base + next_angle_base + 1
                p3_outer = next_layer_base + current_angle_base
                p3_inner = next_layer_base + current_angle_base + 1
                p4_outer = next_layer_base + next_angle_base
                p4_inner = next_layer_base + next_angle_base + 1
                
                faces.extend([
                    [p1_outer, p2_outer, p4_outer],
                    [p1_outer, p4_outer, p3_outer]
                ])
                
                faces.extend([
                    [p1_inner, p3_inner, p4_inner],
                    [p1_inner, p4_inner, p2_inner]
                ])
        
        return np.array(faces)
    
    def _create_validated_premium_mesh(self, vertices: np.ndarray, faces: np.ndarray) -> trimesh.Trimesh:
        """יצירה ואימות mesh איכות פרימיום."""
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        
        mesh.remove_duplicate_faces()
        mesh.remove_degenerate_faces() 
        mesh.remove_unreferenced_vertices()
        
        mesh.fix_normals()
        
        try:
            if hasattr(mesh, 'smoothed'):
                smoothed_mesh = mesh.smoothed()
                if (hasattr(smoothed_mesh, 'is_valid') and smoothed_mesh.is_valid and
                    len(smoothed_mesh.vertices) > 0 and len(smoothed_mesh.faces) > 0):
                    mesh = smoothed_mesh
        except Exception as e:
            self.logger.warning(f"החלקה נכשלה, משתמש במש מקורי: {e}")
        
        if not mesh.is_watertight:
            try:
                mesh.fill_holes()
            except Exception as e:
                self.logger.warning(f"סגירת חורים נכשלה: {e}")
        
        if len(mesh.vertices) == 0 or len(mesh.faces) == 0:
            raise ValueError("mesh שנוצר לא תקף - אין נתוני גיאומטריה")
        
        return mesh


class LithophaneLampWorker(QThread):
    """
    Worker thread לייצור מנורת ליטופן ברקע.
    מטפל בעיבוד כבד מבלי לחסום את הממשק.
    """
    
    progress_updated = pyqtSignal(int, str)
    creation_completed = pyqtSignal(bool, str, dict)
    
    def __init__(self, image_path: str, output_path: str):
        super().__init__()
        self.image_path = image_path
        self.output_path = output_path
        self.settings = PremiumSettings()
        self.logger = logging.getLogger(__name__)
        self.start_time = None
    
    def run(self):
        """ביצוע תהליך יצירת מנורת הליטופן המלא."""
        self.start_time = datetime.now()
        
        try:
            self.logger.info(f"מתחיל יצירת מנורת ליטופן: {Path(self.image_path).name}")
            
            self.progress_updated.emit(15, "מנתח מאפייני תמונה...")
            processor = IntelligentImageProcessor(self.settings)
            
            self.progress_updated.emit(35, "מעבד תמונה לאיכות פרימיום...")
            thickness_map = processor.process_image_for_lithophane(self.image_path)
            
            self.progress_updated.emit(60, "בונה גליל תלת מימדי באיכות פרימיום...")
            builder = PremiumCylinderBuilder(self.settings)
            mesh = builder.create_premium_lithophane_cylinder(thickness_map)
            
            self.progress_updated.emit(85, "מייצא קובץ STL מוכן להדפסה...")
            self._export_premium_stl(mesh)
            
            self.progress_updated.emit(100, "מנורת ליטופן הושלמה בהצלחה!")
            
            statistics = self._generate_completion_statistics(mesh)
            success_message = self._format_premium_success_message(statistics)
            
            self.creation_completed.emit(True, success_message, statistics)
            
        except Exception as e:
            error_message = f"יצירה נכשלה: {str(e)}"
            self.logger.error(error_message, exc_info=True)
            self.creation_completed.emit(False, error_message, {})
    
    def _export_premium_stl(self, mesh: trimesh.Trimesh):
        try:
            Path(self.output_path).parent.mkdir(parents=True, exist_ok=True)
            
            mesh.export(self.output_path)
            
            self.logger.info(f"STL יוצא בהצלחה: {self.output_path}")
            
        except Exception as e:
            raise RuntimeError(f"ייצוא קובץ STL נכשל: {str(e)}")
    
    def _generate_completion_statistics(self, mesh: trimesh.Trimesh) -> dict:
        """יצירת סטטיסטיקות מפורטות על מנורת הליטופן שנוצרה."""
        creation_time = datetime.now() - self.start_time
        file_size = Path(self.output_path).stat().st_size / (1024 * 1024)  # MB
        
        angular_segments, height_segments = self.settings.get_mesh_resolution()
        
        return {
            'vertices_count': len(mesh.vertices),
            'faces_count': len(mesh.faces),
            'file_size_mb': file_size,
            'creation_time_seconds': creation_time.total_seconds(),
            'angular_segments': angular_segments,
            'height_segments': height_segments,
            'resolution_mm': self.settings.resolution,
            'thickness_range': f"{self.settings.min_thickness}-{self.settings.max_thickness}mm",
            'output_filename': Path(self.output_path).name
        }
    
    def _format_premium_success_message(self, stats: dict) -> str:
        """עיצוב הודעת השלמה מקצועית."""
        return f"""🌟 מנורת ליטופן פרימיום הושלמה בהצלחה! 🌟

📐 מפרטים פיזיים:
• גליל: ⌀{self.settings.cylinder_diameter}mm × {self.settings.cylinder_height}mm
• עובי דופן: {self.settings.wall_thickness}mm (עיצוב חלול)
• כיסוי ليتופن: {self.settings.lithophane_coverage_angle}°

⚙️ איכות טכנית:
• רזולוציה: {stats['resolution_mm']:.2f}mm (איכות פרימיום)
• צפיפות mesh: {stats['angular_segments']:,} × {stats['height_segments']:,} segments
• גיאומטריה: {stats['vertices_count']:,} vertices, {stats['faces_count']:,} faces
• גודל קובץ: {stats['file_size_mb']:.1f} MB

🎯 אופטימיזציית הדפסה:
• טווח עובי: {stats['thickness_range']} (מכויל ל-PLA לבן)
• מותאם ל-Creality K2 Plus (זרבובית 0.4mm)
• מוכן לאינטגרציה עם LED (קוטר פנימי 56mm)

⏱️ עיבוד הושלם תוך {stats['creation_time_seconds']:.1f} שניות
💾 נשמר בשם: {stats['output_filename']}

🏆 מנורת הליטופן הפרימיום שלך מוכנה להדפסה תלת מימדית!
התמונה תאיר בצורה מושלמת עם תאורת LED אחורית."""


class PremiumLampGeneratorApp(QMainWindow):
    
    def __init__(self):
        super().__init__()
        
        self.selected_image_path = ""
        self.selected_output_path = ""
        self.creation_worker = None
        self.logger = logging.getLogger(__name__)
        self.language_manager = LanguageManager()
        
        self.initialize_premium_interface()
        self.logger.info("מחולל מנורות ליטופן אותחל")
    
    def initialize_premium_interface(self):
        self.setWindowTitle(self.language_manager.get_text('window_title'))
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(1000, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(25)
        main_layout.setContentsMargins(40, 40, 40, 40)
        
        self.create_premium_header(main_layout)
        
        content_layout = QHBoxLayout()
        content_layout.setSpacing(35)
        
        control_panel = self.create_premium_control_panel()
        preview_area = self.create_premium_preview_area()
        
        content_layout.addWidget(control_panel, 1)
        content_layout.addWidget(preview_area, 2)
        
        main_layout.addLayout(content_layout)
        
        self.statusBar().showMessage(self.language_manager.get_text('ready_status'))
        self.apply_premium_styling()
    
    def create_premium_header(self, parent_layout):
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        header_layout = QVBoxLayout(header_frame)
        
        title_and_language_layout = QHBoxLayout()
        
        title_and_language_layout.addStretch()
        
        self.title_label = QLabel(self.language_manager.get_text('main_title'))
        title_font = QFont()
        title_font.setPointSize(28)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("""
            color: #1a365d; 
            padding: 15px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(26, 54, 93, 0.05), 
                stop:0.5 rgba(26, 54, 93, 0.1), 
                stop:1 rgba(26, 54, 93, 0.05));
            border-radius: 12px;
            margin: 5px;
        """)
        title_and_language_layout.addWidget(self.title_label)
        
        title_and_language_layout.addStretch()
        
        self.language_selector = QComboBox()
        self.language_selector.addItems(['עברית', 'English'])
        self.language_selector.setCurrentIndex(0)
        
        # Enhanced font setup for Hebrew and English support
        self.setup_language_selector_font()
        self.language_selector.setStyleSheet(self.get_language_selector_stylesheet())
        self.language_selector.currentIndexChanged.connect(self.change_language)
        title_and_language_layout.addWidget(self.language_selector)
        
        header_layout.addLayout(title_and_language_layout)
        parent_layout.addWidget(header_frame)
    
    def create_premium_control_panel(self) -> QWidget:
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setMinimumWidth(380)
        panel.setMaximumWidth(450)
        layout = QVBoxLayout(panel)
        layout.setSpacing(20)
        
        file_section = self.create_file_selection_section()
        layout.addWidget(file_section, 0)
        
        action_section = self.create_premium_action_section()
        layout.addWidget(action_section, 0)
        
        progress_section = self.create_progress_section()
        layout.addWidget(progress_section, 0)
        
        log_section = self.create_activity_log_section()
        layout.addWidget(log_section, 1)
        
        return panel
    
    def create_file_selection_section(self) -> QWidget:
        self.file_section = QGroupBox(self.language_manager.get_text('file_selection'))
        self.file_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 15px;
                color: #2d3748;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
                background-color: #f8fafc;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                background-color: #f8fafc;
            }
        """)
        self.file_section.setMinimumHeight(130)
        self.file_section.setMaximumHeight(150)
        layout = QVBoxLayout(self.file_section)
        layout.setSpacing(8)
        
        self.select_image_button = QPushButton(self.language_manager.get_text('select_image'))
        self.select_image_button.setFixedHeight(32)
        self.select_image_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4299e1, stop:1 #3182ce);
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 13px;
                padding: 0 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #63b3ed, stop:1 #4299e1);
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2b77cb, stop:1 #2c5aa0);
            }
        """)
        self.select_image_button.clicked.connect(self.select_image_file)
        layout.addWidget(self.select_image_button)
        
        self.image_status_label = QLabel(self.language_manager.get_text('no_image_selected'))
        self.image_status_label.setStyleSheet("color: #718096; font-style: italic; font-size: 11px;")
        layout.addWidget(self.image_status_label)
        
        self.select_output_button = QPushButton(self.language_manager.get_text('select_output'))
        self.select_output_button.setFixedHeight(32)
        self.select_output_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #48bb78, stop:1 #38a169);
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 13px;
                padding: 0 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #68d391, stop:1 #48bb78);
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2f855a, stop:1 #276749);
            }
        """)
        self.select_output_button.clicked.connect(self.select_output_location)
        layout.addWidget(self.select_output_button)
        
        self.output_status_label = QLabel(self.language_manager.get_text('no_output_selected'))
        self.output_status_label.setStyleSheet("color: #718096; font-style: italic; font-size: 11px;")
        layout.addWidget(self.output_status_label)
        
        return self.file_section
    
    def create_premium_action_section(self) -> QWidget:
        self.action_section = QGroupBox(self.language_manager.get_text('create_lamp'))
        self.action_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 15px;
                color: #2d3748;
                border: 2px solid #fed7aa;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
                background-color: #fffaf0;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                background-color: #fffaf0;
            }
        """)
        self.action_section.setMinimumHeight(95)
        self.action_section.setMaximumHeight(115)
        layout = QVBoxLayout(self.action_section)
        layout.setSpacing(8)
        
        self.create_lamp_button = QPushButton(self.language_manager.get_text('create_button'))
        self.create_lamp_button.setFixedHeight(40)
        self.create_lamp_button.setEnabled(False)
        self.create_lamp_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ed8936, stop:1 #dd6b20);
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                padding: 0 16px;
            }
            QPushButton:hover:enabled {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f6ad55, stop:1 #ed8936);
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(237, 137, 54, 0.3);
            }
            QPushButton:pressed:enabled {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #c05621, stop:1 #9c4221);
                transform: translateY(0px);
            }
            QPushButton:disabled {
                background: #e2e8f0;
                color: #a0aec0;
            }
        """)
        self.create_lamp_button.clicked.connect(self.create_premium_lithophane_lamp)
        layout.addWidget(self.create_lamp_button)
        
        self.specs_label = QLabel(self.language_manager.get_text('specs'))
        self.specs_label.setStyleSheet("color: #4a5568; font-size: 11px; text-align: center;")
        self.specs_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.specs_label)
        
        return self.action_section
    
    def create_progress_section(self) -> QWidget:
        self.progress_section = QGroupBox(self.language_manager.get_text('progress'))
        self.progress_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 15px;
                color: #2d3748;
                border: 2px solid #bee3f8;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
                background-color: #ebf8ff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                background-color: #ebf8ff;
            }
        """)
        self.progress_section.setMinimumHeight(80)
        self.progress_section.setMaximumHeight(100)
        layout = QVBoxLayout(self.progress_section)
        layout.setSpacing(8)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(24)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #e2e8f0;
                border-radius: 12px;
                background-color: #f7fafc;
                text-align: center;
                font-weight: 600;
                font-size: 11px;
                color: #2d3748;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 10px;
                margin: 2px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        self.progress_status_label = QLabel("")
        self.progress_status_label.setStyleSheet("color: #3182ce; font-size: 11px;")
        layout.addWidget(self.progress_status_label)
        
        return self.progress_section
    
    def create_activity_log_section(self) -> QWidget:
        self.log_section = QGroupBox(self.language_manager.get_text('activity_log'))
        self.log_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 15px;
                color: #2d3748;
                border: 2px solid #d6f5d6;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
                background-color: #f0fff4;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                background-color: #f0fff4;
            }
        """)
        layout = QVBoxLayout(self.log_section)
        
        self.activity_log = QTextEdit()
        self.activity_log.setMinimumHeight(150)
        self.activity_log.setReadOnly(True)
        self.activity_log.setStyleSheet("""
            QTextEdit {
                background-color: #f7fafc;
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                padding: 8px;
                color: #2d3748;
            }
        """)
        layout.addWidget(self.activity_log)
        
        return self.log_section
    
    def create_premium_preview_area(self) -> QWidget:
        """יצירת אזור תצוגה מקדימה מתקדם."""
        area = QFrame()
        area.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(area)
        
        self.preview_title = QLabel(self.language_manager.get_text('preview'))
        self.preview_title.setStyleSheet("font-weight: bold; font-size: 16px; color: #2d3748;")
        self.preview_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.preview_title)
        
        self.preview_label = QLabel()
        self.preview_label.setMinimumSize(600, 500)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("""
            border: 3px dashed #cbd5e0;
            border-radius: 12px;
            background-color: #f7fafc;
            color: #4a5568;
            font-size: 16px;
            padding: 30px;
        """)
        self.preview_label.setText(self.language_manager.get_text('preview_text'))
        
        layout.addWidget(self.preview_label)
        
        return area
    
    def apply_premium_styling(self):
        """יישום עיצוב מקצועי לאפליקציה."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }
            
            QFrame {
                background-color: #f7fafc;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                padding: 20px;
            }
            
            QGroupBox {
                background-color: #ffffff;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 15px;
                margin-top: 10px;
            }
            
            QPushButton {
                background-color: #3182ce;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px 25px;
                font-size: 14px;
                font-weight: 600;
                min-height: 20px;
            }
            
            QPushButton:hover {
                background-color: #2c5aa0;
            }
            
            QPushButton:pressed {
                background-color: #2a4d8a;
            }
            
            QPushButton:disabled {
                background-color: #cbd5e0;
                color: #718096;
            }
            
            QPushButton#create_lamp_button {
                background-color: #38a169;
                font-size: 18px;
                font-weight: bold;
                padding: 18px 30px;
            }
            
            QPushButton#create_lamp_button:hover {
                background-color: #2f855a;
            }
            
            QPushButton#create_lamp_button:disabled {
                background-color: #a0aec0;
            }
            
            QProgressBar {
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                text-align: center;
                font-weight: bold;
                height: 25px;
            }
            
            QProgressBar::chunk {
                background-color: #3182ce;
                border-radius: 4px;
            }
        """)
        
        self.create_lamp_button.setObjectName("create_lamp_button")
    
    def change_language(self, index):
        # Prevent UI flickering during language change
        self.setUpdatesEnabled(False)
        
        try:
            if index == 0:
                self.language_manager.set_language('he')
            else:
                self.language_manager.set_language('en')
            
            # Update UI layout direction for Hebrew/English
            self.update_layout_direction()
            
            # Update all UI text
            self.update_ui_language()
            
            # Update font for better Hebrew/English rendering
            self.setup_language_selector_font()
            
        finally:
            # Re-enable updates and force repaint
            self.setUpdatesEnabled(True)
            self.repaint()
    
    def update_ui_language(self):
        """Update all UI text elements with current language."""
        # Update window and main title
        self.setWindowTitle(self.language_manager.get_text('window_title'))
        self.title_label.setText(self.language_manager.get_text('main_title'))
        
        # Update file selection section
        self.file_section.setTitle(self.language_manager.get_text('file_selection'))
        self.select_image_button.setText(self.language_manager.get_text('select_image'))
        self.select_output_button.setText(self.language_manager.get_text('select_output'))
        
        # Update action section
        self.action_section.setTitle(self.language_manager.get_text('create_lamp'))
        self.create_lamp_button.setText(self.language_manager.get_text('create_button'))
        self.specs_label.setText(self.language_manager.get_text('specs'))
        
        # Update progress and log sections
        self.progress_section.setTitle(self.language_manager.get_text('progress'))
        self.log_section.setTitle(self.language_manager.get_text('activity_log'))
        self.preview_title.setText(self.language_manager.get_text('preview'))
        
        # Update status labels if no files selected
        if not self.selected_image_path:
            self.image_status_label.setText(self.language_manager.get_text('no_image_selected'))
        if not self.selected_output_path:
            self.output_status_label.setText(self.language_manager.get_text('no_output_selected'))
        
        # Update preview and status bar
        self.preview_label.setText(self.language_manager.get_text('preview_text'))
        self.statusBar().showMessage(self.language_manager.get_text('ready_status'))
    
    def select_image_file(self):
        """טיפול בבחירת קובץ תמונה."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "בחר תמונה למנורת ליטופן",
            "",
            "קבצי תמונה (*.png *.jpg *.jpeg *.bmp *.tiff *.gif);;כל הקבצים (*.*)"
        )
        
        if file_path:
            self.selected_image_path = file_path
            filename = Path(file_path).name
            self.image_status_label.setText(f"נבחר: {filename}")
            self.image_status_label.setStyleSheet("color: #38a169; font-weight: 600;")
            
            self.update_image_preview(file_path)
            self.update_create_button_state()
            self.log_activity(f"תמונה נבחרה: {filename}")
            
            self.logger.info(f"תמונה נבחרה: {filename}")
    
    def select_output_location(self):
        """טיפול בבחירת מיקום שמירה."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"lithophane_lamp_{timestamp}.stl"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "שמור מנורת ליטופן בשם",
            default_filename,
            "קבצי STL (*.stl);;כל הקבצים (*.*)"
        )
        
        if file_path:
            if not file_path.lower().endswith('.stl'):
                file_path += '.stl'
            
            self.selected_output_path = file_path
            filename = Path(file_path).name
            self.output_status_label.setText(f"שמירה בשם: {filename}")
            self.output_status_label.setStyleSheet("color: #38a169; font-weight: 600;")
            
            self.update_create_button_state()
            self.log_activity(f"מיקום שמירה נבחר: {filename}")
            
            self.logger.info(f"מיקום שמירה נבחר: {filename}")
    
    def setup_language_selector_font(self):
        """Setup optimal font for Hebrew and English text rendering."""
        font = QFont()
        font.setPointSize(12)
        
        if self.language_manager.current_language == 'he':
            # Hebrew-optimized font families
            font.setFamilies(["Tahoma", "Arial Unicode MS", "Segoe UI", "Arial"])
        else:
            # English-optimized font families
            font.setFamilies(["Segoe UI", "Arial", "sans-serif"])
        
        font.setBold(True)
        self.language_selector.setFont(font)
    
    def get_language_selector_stylesheet(self):
        """Get improved stylesheet for language selector without unsupported properties."""
        return """
            QComboBox {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                padding: 8px 16px;
                min-width: 130px;
            }
            QComboBox:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7c3aed, stop:1 #8b5cf6);
            }
            QComboBox:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a2d91, stop:1 #6b46c1);
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                width: 0;
                height: 0;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid white;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                selection-background-color: #667eea;
                selection-color: white;
                color: #2d3748;
                font-size: 14px;
                font-weight: 600;
                padding: 4px;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                padding: 10px 16px;
                border-radius: 4px;
                margin: 2px;
                border: none;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #f0f4ff;
                color: #2d3748;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #667eea;
                color: white;
            }
        """
    
    def update_layout_direction(self):
        """Update UI layout direction based on current language."""
        if self.language_manager.current_language == 'he':
            # Set Right-to-Left layout for Hebrew
            self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            # Also update the title label alignment for Hebrew
            self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            # Set Left-to-Right layout for English
            self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
            self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    def update_image_preview(self, image_path: str):
        """עדכון תצוגת התמונה המקדימה."""
        try:
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    self.preview_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled_pixmap)
            else:
                self.preview_label.setText("לא ניתן להציג את התמונה")
        except Exception as e:
            self.logger.warning(f"תצוגה מקדימה נכשלה: {e}")
            self.preview_label.setText("תצוגה מקדימה לא זמינה")
    
    def update_create_button_state(self):
        """עדכון מצב כפתור היצירה."""
        can_create = bool(self.selected_image_path and self.selected_output_path)
        self.create_lamp_button.setEnabled(can_create)
    
    def create_premium_lithophane_lamp(self):
        """התחלת תהליך יצירת מנורת ליטופן פרימיום."""
        if not self.selected_image_path or not self.selected_output_path:
            QMessageBox.warning(self, "בחירה חסרה", 
                              "אנא בחר גם תמונה וגם מיקום שמירה.")
            return
        
        self.set_ui_processing_state(True)
        
        self.creation_worker = LithophaneLampWorker(
            self.selected_image_path, 
            self.selected_output_path
        )
        
        self.creation_worker.progress_updated.connect(self.update_progress)
        self.creation_worker.creation_completed.connect(self.creation_finished)
        
        self.creation_worker.start()
        self.log_activity("התחיל תהליך יצירת מנורת ליטופן פרימיום...")
        
        self.logger.info("תהליך יצירת מנורת ליטופן התחיל")
    
    def set_ui_processing_state(self, processing: bool):
        self.select_image_button.setEnabled(not processing)
        self.select_output_button.setEnabled(not processing)
        self.create_lamp_button.setEnabled(not processing)
        
        self.progress_bar.setVisible(processing)
        if processing:
            self.progress_bar.setValue(0)
            self.progress_status_label.setText("מאתחל...")
        else:
            self.progress_status_label.setText("")
    
    def update_progress(self, percentage: int, status_message: str):
        """עדכון תצוגת התקדמות."""
        self.progress_bar.setValue(percentage)
        self.progress_status_label.setText(status_message)
        self.statusBar().showMessage(f"[{percentage}%] {status_message}")
        
        self.log_activity(f"[{percentage}%] {status_message}")
    
    def creation_finished(self, success: bool, message: str, statistics: dict):
        """טיפול בסיום יצירת מנורת ליטופן."""
        self.set_ui_processing_state(False)
        
        if success:
            QMessageBox.information(self, "יצירה הושלמה בהצלחה", message)
            self.statusBar().showMessage("מנורת ליטופן פרימיום הושלמה בהצלחה")
            self.log_activity("✅ מנורת ליטופן הושלמה בהצלחה!")
            self.logger.info("יצירת מנורת ליטופן הושלמה בהצלחה")
        else:
            QMessageBox.critical(self, "יצירה נכשלה", message)
            self.statusBar().showMessage("יצירת מנורת ליטופן נכשלה")
            self.log_activity(f"❌ שגיאה: {message}")
            self.logger.error(f"יצירת מנורת ליטופן נכשלה: {message}")
        
        if self.creation_worker:
            self.creation_worker.deleteLater()
            self.creation_worker = None
    
    def log_activity(self, message: str):
        """רישום פעילות בלוג."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.activity_log.append(f"[{timestamp}] {message}")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("מחולל מנורות ליטופן פרימיום")
    app.setOrganizationName("פתרונות תלת מימד מקצועיים")
    
    window = PremiumLampGeneratorApp()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()