#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main Window for Lithophane Lamp Generator
Clean GUI with multilingual support and simple styling.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QLabel, QFileDialog, QProgressBar, QMessageBox,
    QFrame, QTextEdit, QGroupBox, QStackedWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QCloseEvent

from .language_manager import LanguageManager
from .segmented_control import SegmentedControl
from ..core.settings import Settings, ConfigManager
from ..utils.worker import LithophaneLampWorker
from ..utils.validation import ImageValidator, FileValidator, ValidationError


logger = logging.getLogger(__name__)


class LampGeneratorApp(QMainWindow):
    """
    Main application window for the Lithophane Lamp Generator.
    
    Features:
    - Bilingual interface (Hebrew/English)
    - Clean styling and layout
    - Real-time progress tracking
    - Comprehensive error handling
    - Image preview and validation
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        """Initialize the main application window."""
        super().__init__()
        
        # Initialize core components
        self.settings = settings or Settings()
        self.language_manager = LanguageManager()
        self.logger = logging.getLogger(__name__)
        
        # State variables
        self.selected_image_path = ""
        self.selected_output_path = ""
        self.creation_worker: Optional[LithophaneLampWorker] = None
        
        # Initialize UI
        self.initialize_interface()
        self.update_specs_label()  # Update specs with current settings
        self.logger.info("Main window initialized successfully")
    
    def initialize_interface(self) -> None:
        """Initialize the complete user interface."""
        # Window configuration
        self.setWindowTitle(self.language_manager.get_text('window_title'))
        self.setGeometry(100, 100, 900, 750)
        self.setMinimumSize(800, 700)
        
        # Central widget setup as stacked pages (main <-> settings)
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Main page container
        self.main_page = QWidget()
        self.stack.addWidget(self.main_page)

        main_layout = QVBoxLayout(self.main_page)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Create UI components
        self.create_header(main_layout)

        # Create centered control panel layout
        content_layout = QHBoxLayout()
        content_layout.addStretch(1)

        control_panel = self.create_control_panel()
        content_layout.addWidget(control_panel, 0)

        content_layout.addStretch(1)

        main_layout.addLayout(content_layout)
        
        # Status bar and styling
        self.statusBar().showMessage(self.language_manager.get_text('ready_status'))
        self.apply_styling()

        # Ensure main page is visible initially
        self.stack.setCurrentWidget(self.main_page)
    
    def create_header(self, parent_layout: QVBoxLayout) -> None:
        """Create clean header with language selector."""
        header_layout = QHBoxLayout()

        header_layout.addStretch()

        # Language selector (top-right corner) - Modern segmented control
        self.language_selector = SegmentedControl()
        available_langs = self.language_manager.get_available_languages()
        # Add Hebrew first, then English to maintain order
        self.language_selector.add_segment(available_langs['he'], 'he')
        self.language_selector.add_segment(available_langs['en'], 'en')
        self.language_selector.set_current_index(0)
        self.setup_language_selector_font()
        self.language_selector.selectionChanged.connect(self.change_language)
        header_layout.addWidget(self.language_selector)

        parent_layout.addLayout(header_layout)  
  
    def create_control_panel(self) -> QWidget:
        """Create the main control panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setMinimumWidth(600)
        panel.setMaximumWidth(750)
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        
        # Add sections
        file_section = self.create_file_selection_section()
        layout.addWidget(file_section, 0)
        
        action_section = self.create_action_section()
        layout.addWidget(action_section, 0)
        
        progress_section = self.create_progress_section()
        layout.addWidget(progress_section, 0)
        
        log_section = self.create_activity_log_section()
        layout.addWidget(log_section, 1)
        
        return panel
    
    def create_file_selection_section(self) -> QWidget:
        """Create file selection section."""
        self.file_section = QGroupBox(self.language_manager.get_text('file_selection'))
        self.file_section.setMinimumHeight(120)
        layout = QVBoxLayout(self.file_section)
        layout.setSpacing(10)
        
        # Image selection button
        self.select_image_button = QPushButton(self.language_manager.get_text('select_image'))
        self.select_image_button.clicked.connect(self.select_image_file)
        layout.addWidget(self.select_image_button)
        
        self.image_status_label = QLabel(self.language_manager.get_text('no_image_selected'))
        self.image_status_label.setStyleSheet("color: #888888; font-style: italic; font-size: 11px; padding: 2px;")
        self.image_status_label.setWordWrap(True)
        layout.addWidget(self.image_status_label)

        # Output selection button
        self.select_output_button = QPushButton(self.language_manager.get_text('select_output'))
        self.select_output_button.clicked.connect(self.select_output_location)
        layout.addWidget(self.select_output_button)

        self.output_status_label = QLabel(self.language_manager.get_text('no_output_selected'))
        self.output_status_label.setStyleSheet("color: #888888; font-style: italic; font-size: 11px; padding: 2px;")
        self.output_status_label.setWordWrap(True)
        layout.addWidget(self.output_status_label)
        
        return self.file_section
    
    def create_action_section(self) -> QWidget:
        """Create action section with creation button."""
        self.action_section = QGroupBox(self.language_manager.get_text('create_lamp'))
        self.action_section.setMinimumHeight(90)
        layout = QVBoxLayout(self.action_section)
        layout.setSpacing(8)
        
        # Create lamp button
        self.create_lamp_button = QPushButton(self.language_manager.get_text('create_button'))
        self.create_lamp_button.setMinimumHeight(35)
        self.create_lamp_button.setEnabled(False)
        self.create_lamp_button.setStyleSheet("""
            QPushButton {
                background-color: #cc785c;
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
                border: 1px solid #cc785c;
            }
            QPushButton:hover:enabled {
                background-color: #d97757;
                border-color: #d97757;
            }
            QPushButton:pressed:enabled {
                background-color: #b56849;
            }
            QPushButton:disabled {
                background-color: #252525;
                color: #666666;
                border-color: #333333;
            }
        """)
        self.create_lamp_button.clicked.connect(self.create_lithophane_lamp)
        layout.addWidget(self.create_lamp_button)
        
        # Specifications label
        self.specs_label = QLabel(self.language_manager.get_text('specs'))
        self.specs_label.setStyleSheet("color: #999999; font-size: 10px; text-align: center; padding: 4px;")
        self.specs_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.specs_label.setWordWrap(True)
        layout.addWidget(self.specs_label)
        
        return self.action_section
    
    def create_progress_section(self) -> QWidget:
        """Create progress tracking section."""
        self.progress_section = QGroupBox(self.language_manager.get_text('progress'))
        self.progress_section.setMinimumHeight(75)
        layout = QVBoxLayout(self.progress_section)
        layout.setSpacing(8)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Progress status label
        self.progress_status_label = QLabel("")
        self.progress_status_label.setStyleSheet("color: #cc785c; font-size: 11px; padding: 2px;")
        self.progress_status_label.setWordWrap(True)
        layout.addWidget(self.progress_status_label)
        
        return self.progress_section
    
    def create_activity_log_section(self) -> QWidget:
        """Create activity log section."""
        self.log_section = QGroupBox(self.language_manager.get_text('activity_log'))
        layout = QVBoxLayout(self.log_section)

        # Activity log text area (expanded for better visibility)
        self.activity_log = QTextEdit()
        self.activity_log.setMinimumHeight(300)
        self.activity_log.setReadOnly(True)
        layout.addWidget(self.activity_log)

        return self.log_section
    
    
    def apply_styling(self) -> None:
        """Apply refined dark theme styling for a cleaner UI."""
        style = """
            QMainWindow { background-color: #171717; font-family: 'Segoe UI', Arial, sans-serif; font-size: 12px; }

            QFrame { background-color: #1f1f1f; border: 1px solid #2b2b2b; border-radius: 10px; padding: 12px; }

            QGroupBox { font-weight: 600; font-size: 13px; color: #e7e7e7; border: 1px solid #2b2b2b; border-radius: 8px; margin-top: 10px; padding-top: 10px; background-color: #212121; }
            QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 8px; background-color: #212121; color: #e7e7e7; }

            QPushButton { background-color: #2b2b2b; color: #e7e7e7; border: 1px solid #363636; border-radius: 8px; font-weight: 500; font-size: 12px; padding: 9px 14px; min-height: 20px; }
            QPushButton:hover { background-color: #333; border-color: #3a3a3a; }
            QPushButton:pressed { background-color: #262626; }
            QPushButton:disabled { background-color: #232323; color: #6e6e6e; border-color: #2d2d2d; }

            QProgressBar { border: 1px solid #2b2b2b; border-radius: 6px; background-color: #1f1f1f; text-align: center; font-weight: 500; font-size: 11px; color: #e7e7e7; height: 20px; }
            QProgressBar::chunk { background-color: #cc785c; border-radius: 5px; }

            QTextEdit { background-color: #1f1f1f; border: 1px solid #2b2b2b; border-radius: 8px; font-family: 'Consolas', 'Courier New', monospace; font-size: 11px; padding: 8px; color: #cfcfcf; line-height: 1.4; }

            QLabel { color: #d0d0d0; font-size: 12px; }

            QStatusBar { background-color: #1f1f1f; color: #e7e7e7; font-weight: 500; padding: 6px; border-top: 1px solid #2b2b2b; }
        """
        self.setStyleSheet(style)
    
    def setup_language_selector_font(self) -> None:
        """Setup optimal font for Hebrew and English text rendering."""
        font = QFont()
        font.setPointSize(12)

        if self.language_manager.current_language == 'he':
            font.setFamilies(["Tahoma", "Arial Unicode MS", "Segoe UI", "Arial"])
        else:
            font.setFamilies(["Segoe UI", "Arial", "sans-serif"])

        font.setBold(True)

        # Apply font to all segment buttons
        for segment in self.language_selector.segments:
            segment.setFont(font)
    
    def _sanitize_filename_for_display(self, filename: str) -> str:
        """
        Sanitize filename for safe display in GUI.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename safe for display
        """
        # Import constants
        from ..core import constants as const

        # Remove any control characters and limit length
        sanitized = ''.join(char for char in filename if ord(char) >= const.MIN_PRINTABLE_CHAR_CODE)

        # Limit length for display
        if len(sanitized) > const.MAX_FILENAME_DISPLAY_LENGTH:
            name_part = sanitized[:const.MAX_FILENAME_DISPLAY_LENGTH - 3]
            sanitized = f"{name_part}..."

        return sanitized

    # Event handlers
    def change_language(self, index: int, lang_code: str) -> None:
        """Handle language change."""
        self.setUpdatesEnabled(False)

        try:
            self.language_manager.set_language(lang_code)

            self.update_layout_direction()
            self.update_ui_language()
            self.setup_language_selector_font()

        finally:
            self.setUpdatesEnabled(True)
            self.repaint()
    
    def update_layout_direction(self) -> None:
        """Update UI layout direction based on current language."""
        if self.language_manager.current_language == 'he':
            self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        else:
            self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
    
    def update_ui_language(self) -> None:
        """Update all UI text elements with current language."""
        # Update window title
        self.setWindowTitle(self.language_manager.get_text('window_title'))

        # Update sections
        self.file_section.setTitle(self.language_manager.get_text('file_selection'))
        self.select_image_button.setText(self.language_manager.get_text('select_image'))
        self.select_output_button.setText(self.language_manager.get_text('select_output'))

        self.action_section.setTitle(self.language_manager.get_text('create_lamp'))
        self.create_lamp_button.setText(self.language_manager.get_text('create_button'))
        self.specs_label.setText(self.language_manager.get_text('specs'))

        self.progress_section.setTitle(self.language_manager.get_text('progress'))
        self.log_section.setTitle(self.language_manager.get_text('activity_log'))

        # Update status labels if no files selected
        if not self.selected_image_path:
            self.image_status_label.setText(self.language_manager.get_text('no_image_selected'))
        if not self.selected_output_path:
            self.output_status_label.setText(self.language_manager.get_text('no_output_selected'))

        # Update status bar
        self.statusBar().showMessage(self.language_manager.get_text('ready_status'))

    def update_specs_label(self) -> None:
        """Update the specifications label with current settings."""
        specs_text = self.language_manager.get_text('specs_format').format(
            diameter=self.settings.cylinder_diameter,
            height=self.settings.cylinder_height,
            angle=self.settings.lithophane_coverage_angle
        )
        self.specs_label.setText(specs_text)

    def select_image_file(self) -> None:
        """Handle image file selection with validation."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select image for lithophane lamp",
            "",
            "Image files (*.png *.jpg *.jpeg *.bmp *.tiff *.gif);;All files (*.*)"
        )

        if file_path:
            try:
                # Validate image
                validation_result = ImageValidator.validate_image_file(file_path)

                self.selected_image_path = file_path
                filename = self._sanitize_filename_for_display(Path(file_path).name)

                # Use localized text
                prefix = self.language_manager.get_text('file_selected_prefix')
                self.image_status_label.setText(f"{prefix} {filename}")
                self.image_status_label.setStyleSheet("color: #7fb069; font-weight: 600; font-size: 11px; padding: 2px;")

                self.update_create_button_state()
                self.log_activity(f"Image selected: {filename}")

                # Show quality warnings if any
                warnings = validation_result['quality_metrics']['warnings']
                if warnings:
                    warning_text = "\n".join(warnings)
                    QMessageBox.warning(self, "Image Quality Notice",
                                      f"Image selected successfully, but please note:\n\n{warning_text}")

                self.logger.info(f"Image selected: {filename}")

            except ValidationError as e:
                QMessageBox.critical(self, "Image Validation Error", str(e))
                self.logger.error(f"Image validation failed: {e}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to process image: {e}")
                self.logger.error(f"Image selection error: {e}")
    
    def select_output_location(self) -> None:
        """Handle output location selection."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"lithophane_lamp_{timestamp}.stl"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save lithophane lamp as",
            default_filename,
            "STL files (*.stl);;All files (*.*)"
        )

        if file_path:
            try:
                validated_path = FileValidator.validate_output_path(file_path)

                self.selected_output_path = validated_path
                filename = self._sanitize_filename_for_display(Path(validated_path).name)

                # Use localized text
                prefix = self.language_manager.get_text('save_as_prefix')
                self.output_status_label.setText(f"{prefix} {filename}")
                self.output_status_label.setStyleSheet("color: #7fb069; font-weight: 600; font-size: 11px; padding: 2px;")

                self.update_create_button_state()
                self.log_activity(f"Output location selected: {filename}")
                self.logger.info(f"Output location selected: {filename}")

            except ValidationError as e:
                QMessageBox.critical(self, "Output Path Error", str(e))
                self.logger.error(f"Output path validation failed: {e}")
    
    def update_create_button_state(self) -> None:
        """Update the create button state based on file selections."""
        can_create = bool(self.selected_image_path and self.selected_output_path)
        self.create_lamp_button.setEnabled(can_create)
    
    def log_activity(self, message: str) -> None:
        """Add message to activity log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.activity_log.append(formatted_message)
        
        # Auto-scroll to bottom
        scrollbar = self.activity_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def create_lithophane_lamp(self) -> None:
        """Create lithophane lamp with high quality."""
        if not self.selected_image_path or not self.selected_output_path:
            QMessageBox.warning(self, "Missing Files",
                              "Please select both image and output location.")
            return

        # Check if worker is already running
        if self.creation_worker and self.creation_worker.isRunning():
            QMessageBox.warning(self, "Processing In Progress",
                              "Lithophane creation is already in progress. Please wait for it to complete.")
            return

        try:
            # Disable UI during processing
            self.create_lamp_button.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            # Create and start worker
            self.creation_worker = LithophaneLampWorker(
                self.selected_image_path,
                self.selected_output_path,
                self.settings
            )
            
            # Connect worker signals
            self.creation_worker.progress_updated.connect(self.update_progress_and_status)
            self.creation_worker.creation_completed.connect(self.on_creation_completed)
            
            # Start processing
            self.creation_worker.start()
            self.log_activity("Starting lithophane lamp creation...")

        except Exception as e:
            self.on_creation_completed(False, str(e), {})
    
    def update_progress_and_status(self, value: int, message: str) -> None:
        """Update progress bar and status message."""
        self.progress_bar.setValue(value)
        self.progress_status_label.setText(message)
        self.log_activity(message)

    def on_creation_completed(self, success: bool, message: str, statistics: dict) -> None:
        """Handle creation completion (success or failure)."""
        self.progress_bar.setVisible(False)
        self.progress_status_label.setText("")
        self.create_lamp_button.setEnabled(True)

        if success:
            # Show success message with statistics
            QMessageBox.information(self, "Success!", message)
            self.log_activity("Lithophane lamp creation completed successfully!")
            self.logger.info(f"Lithophane creation completed successfully: {statistics}")
        else:
            # Show error message
            QMessageBox.critical(self, "Creation Error", message)
            self.log_activity(f"Error: {message}")
            self.logger.error(f"Lithophane creation failed: {message}")
    
    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event with graceful shutdown."""
        if self.creation_worker and self.creation_worker.isRunning():
            reply = QMessageBox.question(self, 'Close Application',
                                       'Creation is in progress. Are you sure you want to close?',
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                       QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.Yes:
                # Import constants
                from ..core import constants as const

                # Request graceful cancellation
                self.creation_worker.cancel()

                # Wait for graceful shutdown
                if not self.creation_worker.wait(const.WORKER_SHUTDOWN_TIMEOUT_MS):
                    self.logger.warning("Worker thread did not stop gracefully, forcing termination")
                    self.creation_worker.terminate()
                    self.creation_worker.wait()

                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
