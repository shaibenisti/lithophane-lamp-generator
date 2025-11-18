#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Custom Success Dialog for Lithophane Lamp Generator
Beautiful, animated success dialog with detailed information display.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QScrollArea, QWidget, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPixmap, QIcon
from typing import Dict, Any

from .animations import AnimationManager, ThemeColors, create_gradient_stylesheet


class SuccessDialog(QDialog):
    """
    Beautiful, animated success dialog for lithophane completion.
    Features modern design with proper text formatting and animations.
    """
    
    def __init__(self, parent=None, statistics: Dict[str, Any] = None):
        super().__init__(parent)
        self.statistics = statistics or {}
        self.animation_manager = AnimationManager()
        
        self.setup_ui()
        self.setup_animations()
    
    def setup_ui(self):
        """Setup the dialog UI with modern styling."""
        self.setWindowTitle("Lithophane Creation Complete!")
        self.setModal(True)
        self.setMinimumSize(600, 500)
        self.setMaximumSize(800, 700)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # Header section
        self.create_header(main_layout)
        
        # Content section with scroll area
        self.create_content_area(main_layout)
        
        # Button section
        self.create_buttons(main_layout)
        
        # Apply styling
        self.apply_modern_styling()
    
    def create_header(self, parent_layout):
        """Create animated header section."""
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.setSpacing(15)
        
        # Success icon/title
        self.success_label = QLabel("✓ SUCCESS!")
        self.success_label.setObjectName("successTitle")
        self.success_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Subtitle
        self.subtitle_label = QLabel("Your Lithophane Lamp is Ready!")
        self.subtitle_label.setObjectName("subtitle")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header_layout.addWidget(self.success_label)
        header_layout.addWidget(self.subtitle_label)
        
        parent_layout.addWidget(header_frame)
    
    def create_content_area(self, parent_layout):
        """Create scrollable content area with statistics."""
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarNever)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        
        # Create information sections
        self.create_physical_specs_section(content_layout)
        self.create_technical_quality_section(content_layout)
        self.create_print_optimization_section(content_layout)
        self.create_timing_section(content_layout)
        
        scroll_area.setWidget(content_widget)
        parent_layout.addWidget(scroll_area)
    
    def create_physical_specs_section(self, parent_layout):
        """Create physical specifications section."""
        section = self.create_info_section(
            "Physical Specifications",
            [
                f"Cylinder Dimensions: {self.statistics.get('cylinder_dimensions', 'N/A')}",
                f"Wall Thickness: {self.statistics.get('wall_thickness', 'N/A')}",
                f"Design: Hollow (optimized for LED integration)",
                f"Inner Diameter: {self._get_inner_diameter()} mm"
            ],
            ThemeColors.PRIMARY_BLUE
        )
        parent_layout.addWidget(section)
    
    def create_technical_quality_section(self, parent_layout):
        """Create technical quality section."""
        vertices = self.statistics.get('vertices_count', 0)
        faces = self.statistics.get('faces_count', 0)
        
        section = self.create_info_section(
            "Technical Quality",
            [
                f"Resolution: {self.statistics.get('resolution_mm', 0):.2f}mm (High Quality)",
                f"Mesh Density: {self.statistics.get('angular_segments', 0):,} × {self.statistics.get('height_segments', 0):,} segments",
                f"Geometry: {vertices:,} vertices, {faces:,} faces",
                f"File Size: {self.statistics.get('file_size_mb', 0):.1f} MB"
            ],
            ThemeColors.PRIMARY_PURPLE
        )
        parent_layout.addWidget(section)
    
    def create_print_optimization_section(self, parent_layout):
        """Create print optimization section."""
        section = self.create_info_section(
            "3D Printing Optimization",
            [
                f"Thickness Range: {self.statistics.get('thickness_range', 'N/A')}",
                "Material: Calibrated for White PLA",
                "Layer Height: 0.12mm recommended",
                "Nozzle: Optimized for 0.4mm nozzle",
                "Support: None required (hollow design)"
            ],
            ThemeColors.ACCENT_GREEN
        )
        parent_layout.addWidget(section)
    
    def create_timing_section(self, parent_layout):
        """Create timing and file information section."""
        processing_time = self.statistics.get('creation_time_seconds', 0)
        filename = self.statistics.get('output_filename', 'Unknown')
        
        section = self.create_info_section(
            "Processing Complete",
            [
                f"Processing Time: {processing_time:.1f} seconds",
                f"Saved As: {filename}",
                "Status: Ready for 3D printing",
                "Quality: High-quality output"
            ],
            ThemeColors.ACCENT_ORANGE
        )
        parent_layout.addWidget(section)
    
    def create_info_section(self, title: str, items: list, accent_color: 'QColor') -> QFrame:
        """Create a styled information section."""
        section_frame = QFrame()
        section_frame.setObjectName("infoSection")
        section_layout = QVBoxLayout(section_frame)
        section_layout.setSpacing(10)
        
        # Section title
        title_label = QLabel(title)
        title_label.setObjectName("sectionTitle")
        title_label.setStyleSheet(f"color: {accent_color.name()}; font-weight: bold; font-size: 14px;")
        section_layout.addWidget(title_label)
        
        # Section items
        for item in items:
            item_label = QLabel(f"• {item}")
            item_label.setObjectName("sectionItem")
            item_label.setWordWrap(True)
            section_layout.addWidget(item_label)
        
        return section_frame
    
    def create_buttons(self, parent_layout):
        """Create dialog buttons."""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        # Open folder button
        self.open_folder_button = QPushButton("Open Output Folder")
        self.open_folder_button.setObjectName("primaryButton")
        self.open_folder_button.clicked.connect(self.open_output_folder)
        
        # Close button
        self.close_button = QPushButton("Close")
        self.close_button.setObjectName("secondaryButton")
        self.close_button.clicked.connect(self.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(self.open_folder_button)
        button_layout.addWidget(self.close_button)
        
        parent_layout.addLayout(button_layout)
    
    def apply_modern_styling(self):
        """Apply modern CSS styling to the dialog."""
        style = f"""
        QDialog {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {ThemeColors.WHITE.name()}, 
                stop:1 {ThemeColors.VERY_LIGHT_GRAY.name()});
            border-radius: 15px;
        }}
        
        #headerFrame {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {ThemeColors.PRIMARY_BLUE.name()}, 
                stop:1 {ThemeColors.PRIMARY_PURPLE.name()});
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 10px;
        }}
        
        #successTitle {{
            color: white;
            font-size: 28px;
            font-weight: bold;
            text-align: center;
        }}
        
        #subtitle {{
            color: white;
            font-size: 16px;
            text-align: center;
            font-weight: 500;
        }}
        
        #infoSection {{
            background-color: {ThemeColors.WHITE.name()};
            border: 2px solid {ThemeColors.LIGHT_GRAY.name()};
            border-radius: 8px;
            padding: 15px;
            margin: 5px 0px;
        }}
        
        #sectionTitle {{
            font-size: 14px;
            font-weight: bold;
            margin-bottom: 8px;
        }}
        
        #sectionItem {{
            color: {ThemeColors.DARK_GRAY.name()};
            font-size: 12px;
            margin-left: 10px;
            line-height: 1.4;
        }}
        
        #primaryButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {ThemeColors.ACCENT_GREEN.name()}, 
                stop:1 {ThemeColors.SUCCESS.name()});
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 600;
            min-width: 140px;
        }}
        
        #primaryButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {ThemeColors.SUCCESS.name()}, 
                stop:1 {ThemeColors.ACCENT_GREEN.name()});
        }}
        
        #secondaryButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {ThemeColors.MEDIUM_GRAY.name()}, 
                stop:1 {ThemeColors.DARK_GRAY.name()});
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 600;
            min-width: 100px;
        }}
        
        #secondaryButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {ThemeColors.DARK_GRAY.name()}, 
                stop:1 {ThemeColors.MEDIUM_GRAY.name()});
        }}
        
        QScrollArea {{
            border: none;
            background: transparent;
        }}
        
        QScrollBar:vertical {{
            background: {ThemeColors.LIGHT_GRAY.name()};
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background: {ThemeColors.MEDIUM_GRAY.name()};
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background: {ThemeColors.DARK_GRAY.name()};
        }}
        """
        
        self.setStyleSheet(style)
    
    def setup_animations(self):
        """Setup entrance animations for the dialog."""
        # Fade in the entire dialog
        QTimer.singleShot(50, lambda: self.animation_manager.fade_in(self, 400))
        
        # Animate header with delay
        QTimer.singleShot(200, lambda: self.animation_manager.pulse_effect(self.success_label, 1.1, 300))
    
    def open_output_folder(self):
        """Open the output folder containing the STL file."""
        import os
        import subprocess
        from pathlib import Path
        
        try:
            # Get the output filename from statistics
            filename = self.statistics.get('output_filename', '')
            if filename:
                # Get the directory containing the file
                file_path = Path.cwd() / filename
                folder_path = file_path.parent
                
                # Open folder in Windows Explorer
                if os.name == 'nt':  # Windows
                    subprocess.run(['explorer', str(folder_path)])
                else:  # macOS/Linux
                    subprocess.run(['open' if os.name == 'darwin' else 'xdg-open', str(folder_path)])
        except Exception as e:
            print(f"Could not open folder: {e}")
    
    def _get_inner_diameter(self) -> str:
        """Calculate inner diameter from statistics."""
        try:
            # Extract diameter from cylinder_dimensions string
            dimensions = self.statistics.get('cylinder_dimensions', '')
            if '⌀' in dimensions:
                diameter_str = dimensions.split('⌀')[1].split('mm')[0]
                diameter = float(diameter_str)
                inner_diameter = diameter - 4.0  # Assuming 2mm wall thickness on each side
                return f"{inner_diameter:.0f}"
        except:
            pass
        return "56"  # Default inner diameter