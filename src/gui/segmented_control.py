#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Segmented Control Widget
Modern iOS-style segmented control for language selection.
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QButtonGroup
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen


class SegmentedControl(QWidget):
    """
    Modern segmented control widget for switching between options.

    Features:
    - iOS-style appearance
    - Customizable segments
    - Dark theme compatible
    - Hover effects and visual feedback
    """

    # Signal emitted when selection changes (index, data)
    selectionChanged = pyqtSignal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.segments = []
        self.segment_data = []
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        # Setup layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(3, 3, 3, 3)
        self.layout.setSpacing(2)

        self.setFixedHeight(42)

    def add_segment(self, text: str, data: str):
        """
        Add a segment to the control.

        Args:
            text: Display text for the segment
            data: Associated data value
        """
        button = QPushButton(text)
        button.setCheckable(True)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setMinimumWidth(80)
        button.setFixedHeight(36)

        # Style the button
        button.setStyleSheet(self._get_segment_style())

        # Connect click handler
        index = len(self.segments)
        button.clicked.connect(lambda: self._on_segment_clicked(index))

        self.segments.append(button)
        self.segment_data.append(data)
        self.button_group.addButton(button, index)
        self.layout.addWidget(button)

        # Set first segment as active by default
        if len(self.segments) == 1:
            button.setChecked(True)
            self._update_segment_styles()

    def set_current_index(self, index: int):
        """Set the active segment by index."""
        if 0 <= index < len(self.segments):
            self.segments[index].setChecked(True)
            self._update_segment_styles()

    def current_index(self) -> int:
        """Get the currently selected segment index."""
        return self.button_group.checkedId()

    def current_data(self) -> str:
        """Get the data associated with the current segment."""
        index = self.current_index()
        if 0 <= index < len(self.segment_data):
            return self.segment_data[index]
        return ""

    def _on_segment_clicked(self, index: int):
        """Handle segment click."""
        self._update_segment_styles()
        self.selectionChanged.emit(index, self.segment_data[index])

    def _update_segment_styles(self):
        """Update the visual style of all segments based on active state."""
        for button in self.segments:
            if button.isChecked():
                # Active segment
                button.setStyleSheet(self._get_active_segment_style())
            else:
                # Inactive segment
                button.setStyleSheet(self._get_segment_style())

    def _get_segment_style(self) -> str:
        """Get stylesheet for inactive segments."""
        return """
            QPushButton {
                background-color: transparent;
                color: #999999;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.05);
                color: #bbbbbb;
            }
        """

    def _get_active_segment_style(self) -> str:
        """Get stylesheet for active segment."""
        return """
            QPushButton {
                background-color: #cc785c;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 700;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #d97757;
            }
        """

    def paintEvent(self, event):
        """Custom paint event for background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw rounded background container
        painter.setBrush(QColor(45, 45, 45))  # #2d2d2d
        painter.setPen(QPen(QColor(74, 74, 74), 1))  # #4a4a4a border
        painter.drawRoundedRect(self.rect(), 8, 8)
