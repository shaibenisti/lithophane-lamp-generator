#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
UI Animations and Visual Effects for Lithophane Lamp Generator
Modern, smooth animations to bring the interface to life.
"""

from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QTimer, pyqtSignal, QObject
from PyQt6.QtWidgets import QWidget, QGraphicsOpacityEffect, QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor, QPalette
from typing import Optional, Callable


class AnimationManager(QObject):
    """
    Manages UI animations and visual effects.
    Provides smooth, professional animations for better user experience.
    """
    
    animation_finished = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.animations = []
        self.effects = []
    
    def fade_in(self, widget: QWidget, duration: int = 300, delay: int = 0) -> Optional[QPropertyAnimation]:
        """
        Smooth fade-in animation for widgets.
        
        Args:
            widget: Widget to animate
            duration: Animation duration in milliseconds
            delay: Delay before starting animation
            
        Returns:
            QPropertyAnimation object or None if animation cannot be created
        """
        try:
            # Skip animation if widget doesn't exist or isn't visible
            if not widget or not hasattr(widget, 'setGraphicsEffect'):
                return None
            
            # Create opacity effect if not exists
            if not widget.graphicsEffect():
                effect = QGraphicsOpacityEffect()
                widget.setGraphicsEffect(effect)
            
            effect = widget.graphicsEffect()
            if not effect:
                return None
            
            # Create animation
            animation = QPropertyAnimation(effect, b"opacity")
            animation.setDuration(duration)
            animation.setStartValue(0.0)
            animation.setEndValue(1.0)
            animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            
            if delay > 0:
                QTimer.singleShot(delay, animation.start)
            else:
                animation.start()
            
            self.animations.append(animation)
            animation.finished.connect(lambda: self._safe_remove_animation(animation))
            
            return animation
            
        except Exception:
            # Silently fail if animation cannot be created
            return None
    
    def fade_out(self, widget: QWidget, duration: int = 300, callback: Optional[Callable] = None) -> Optional[QPropertyAnimation]:
        """
        Smooth fade-out animation for widgets.
        
        Args:
            widget: Widget to animate
            duration: Animation duration in milliseconds
            callback: Function to call when animation finishes
            
        Returns:
            QPropertyAnimation object or None if animation cannot be created
        """
        try:
            # Skip animation if widget doesn't exist or isn't visible
            if not widget or not hasattr(widget, 'setGraphicsEffect'):
                if callback:
                    callback()
                return None
            
            # Create opacity effect if not exists
            if not widget.graphicsEffect():
                effect = QGraphicsOpacityEffect()
                widget.setGraphicsEffect(effect)
            
            effect = widget.graphicsEffect()
            if not effect:
                if callback:
                    callback()
                return None
            
            # Create animation
            animation = QPropertyAnimation(effect, b"opacity")
            animation.setDuration(duration)
            animation.setStartValue(1.0)
            animation.setEndValue(0.0)
            animation.setEasingCurve(QEasingCurve.Type.InCubic)
            
            if callback:
                animation.finished.connect(callback)
            
            animation.start()
            
            self.animations.append(animation)
            animation.finished.connect(lambda: self._safe_remove_animation(animation))
            
            return animation
            
        except Exception:
            # Silently fail and execute callback if provided
            if callback:
                callback()
            return None
    
    def slide_in_from_left(self, widget: QWidget, distance: int = 50, duration: int = 400) -> Optional[QPropertyAnimation]:
        """
        Slide-in animation from left side.
        
        Args:
            widget: Widget to animate
            distance: Distance to slide in pixels
            duration: Animation duration in milliseconds
            
        Returns:
            QPropertyAnimation object or None if animation cannot be created
        """
        try:
            # Skip animation if widget doesn't exist or doesn't support position animation
            if not widget or not hasattr(widget, 'pos') or not hasattr(widget, 'move'):
                return None
            
            # Store original position
            original_pos = widget.pos()
            
            # Move widget to starting position (off-screen left)
            widget.move(original_pos.x() - distance, original_pos.y())
            
            # Create animation
            animation = QPropertyAnimation(widget, b"pos")
            animation.setDuration(duration)
            animation.setStartValue(widget.pos())
            animation.setEndValue(original_pos)
            animation.setEasingCurve(QEasingCurve.Type.OutBack)
            
            animation.start()
            
            self.animations.append(animation)
            animation.finished.connect(lambda: self._safe_remove_animation(animation))
            
            return animation
            
        except Exception:
            # Silently fail if animation cannot be created
            return None
    
    def pulse_effect(self, widget: QWidget, scale_factor: float = 1.1, duration: int = 200) -> None:
        """
        Creates a pulse effect on widget (scale up then down).
        
        Args:
            widget: Widget to animate
            scale_factor: How much to scale up
            duration: Duration of each phase
        """
        # Scale up animation
        scale_up = QPropertyAnimation(widget, b"geometry")
        scale_up.setDuration(duration)
        
        original_rect = widget.geometry()
        center = original_rect.center()
        
        # Calculate scaled rectangle
        scaled_width = int(original_rect.width() * scale_factor)
        scaled_height = int(original_rect.height() * scale_factor)
        scaled_rect = original_rect
        scaled_rect.setSize(scaled_rect.size())
        scaled_rect.setWidth(scaled_width)
        scaled_rect.setHeight(scaled_height)
        scaled_rect.moveCenter(center)
        
        scale_up.setStartValue(original_rect)
        scale_up.setEndValue(scaled_rect)
        scale_up.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Scale down animation
        scale_down = QPropertyAnimation(widget, b"geometry")
        scale_down.setDuration(duration)
        scale_down.setStartValue(scaled_rect)
        scale_down.setEndValue(original_rect)
        scale_down.setEasingCurve(QEasingCurve.Type.InCubic)
        
        # Connect animations
        scale_up.finished.connect(scale_down.start)
        scale_up.start()
        
        self.animations.extend([scale_up, scale_down])
        scale_down.finished.connect(lambda: self.animations.clear())
    
    def add_glow_effect(self, widget: QWidget, color: QColor = QColor(100, 149, 237), blur_radius: float = 15.0) -> None:
        """
        Add a glow effect to a widget.
        
        Args:
            widget: Widget to add glow to
            color: Glow color
            blur_radius: Blur radius for glow
        """
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setBlurRadius(blur_radius)
        shadow_effect.setColor(color)
        shadow_effect.setOffset(0, 0)
        
        widget.setGraphicsEffect(shadow_effect)
        self.effects.append(shadow_effect)
    
    def add_shadow_effect(self, widget: QWidget, offset_x: float = 3.0, offset_y: float = 3.0, 
                         blur_radius: float = 10.0, color: QColor = QColor(0, 0, 0, 80)) -> None:
        """
        Add a drop shadow effect to a widget.
        
        Args:
            widget: Widget to add shadow to
            offset_x: Horizontal shadow offset
            offset_y: Vertical shadow offset
            blur_radius: Blur radius for shadow
            color: Shadow color
        """
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setBlurRadius(blur_radius)
        shadow_effect.setColor(color)
        shadow_effect.setOffset(offset_x, offset_y)
        
        widget.setGraphicsEffect(shadow_effect)
        self.effects.append(shadow_effect)
    
    def animate_progress_bar(self, progress_bar, target_value: int, duration: int = 1000) -> QPropertyAnimation:
        """
        Smooth progress bar animation.
        
        Args:
            progress_bar: QProgressBar to animate
            target_value: Target percentage value
            duration: Animation duration in milliseconds
            
        Returns:
            QPropertyAnimation object
        """
        animation = QPropertyAnimation(progress_bar, b"value")
        animation.setDuration(duration)
        animation.setStartValue(progress_bar.value())
        animation.setEndValue(target_value)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        animation.start()
        
        self.animations.append(animation)
        animation.finished.connect(lambda: self.animations.remove(animation))
        
        return animation
    
    def cleanup(self) -> None:
        """Clean up all animations and effects."""
        for animation in self.animations:
            if animation.state() == QPropertyAnimation.State.Running:
                animation.stop()
        
        self.animations.clear()
        self.effects.clear()
    
    def _safe_remove_animation(self, animation: QPropertyAnimation) -> None:
        """Safely remove animation from list."""
        try:
            if animation in self.animations:
                self.animations.remove(animation)
        except Exception:
            pass


class HoverAnimator(QObject):
    """
    Handles hover animations for buttons and widgets.
    """
    
    def __init__(self, widget: QWidget):
        super().__init__()
        self.widget = widget
        self.original_stylesheet = ""
        self.hover_stylesheet = ""
        self.animation_duration = 200
        
        # Store original stylesheet
        self.original_stylesheet = widget.styleSheet()
        
        # Install event filter
        widget.installEventFilter(self)
    
    def set_hover_style(self, hover_stylesheet: str) -> None:
        """Set the stylesheet to use on hover."""
        self.hover_stylesheet = hover_stylesheet
    
    def eventFilter(self, obj, event):
        """Handle hover events."""
        if obj == self.widget:
            if event.type() == event.Type.Enter:
                self._on_hover_enter()
            elif event.type() == event.Type.Leave:
                self._on_hover_leave()
        
        return super().eventFilter(obj, event)
    
    def _on_hover_enter(self):
        """Handle mouse enter event."""
        if self.hover_stylesheet:
            self.widget.setStyleSheet(self.hover_stylesheet)
        
        # Add subtle glow effect
        animation_manager = AnimationManager()
        animation_manager.add_glow_effect(self.widget, QColor(100, 149, 237, 100), 10.0)
    
    def _on_hover_leave(self):
        """Handle mouse leave event."""
        # Restore original stylesheet
        self.widget.setStyleSheet(self.original_stylesheet)
        
        # Remove glow effect
        self.widget.setGraphicsEffect(None)


class ThemeColors:
    """
    Modern minimalist color palette for the UI.
    """
    
    # Primary brand colors - Deep navy and electric blue
    PRIMARY_NAVY = QColor(15, 23, 42)         # #0f172a - Dark navy
    PRIMARY_BLUE = QColor(59, 130, 246)       # #3b82f6 - Electric blue  
    PRIMARY_LIGHT = QColor(147, 197, 253)     # #93c5fd - Light blue
    
    # Accent colors - Modern and vibrant
    ACCENT_PURPLE = QColor(139, 92, 246)      # #8b5cf6 - Purple
    ACCENT_GREEN = QColor(34, 197, 94)        # #22c55e - Green
    ACCENT_ORANGE = QColor(251, 146, 60)      # #fb923c - Orange
    ACCENT_RED = QColor(239, 68, 68)          # #ef4444 - Red
    
    # Neutral grays - Clean and modern
    GRAY_50 = QColor(248, 250, 252)           # #f8fafc
    GRAY_100 = QColor(241, 245, 249)          # #f1f5f9
    GRAY_200 = QColor(226, 232, 240)          # #e2e8f0
    GRAY_300 = QColor(203, 213, 225)          # #cbd5e1
    GRAY_400 = QColor(148, 163, 184)          # #94a3b8
    GRAY_500 = QColor(100, 116, 139)          # #64748b
    GRAY_600 = QColor(71, 85, 105)            # #475569
    GRAY_700 = QColor(51, 65, 85)             # #334155
    GRAY_800 = QColor(30, 41, 59)             # #1e293b
    GRAY_900 = QColor(15, 23, 42)             # #0f172a
    
    # Background colors
    WHITE = QColor(255, 255, 255)             # #ffffff
    BACKGROUND = QColor(248, 250, 252)        # #f8fafc
    SURFACE = QColor(255, 255, 255)           # #ffffff
    
    # Status colors
    SUCCESS = QColor(34, 197, 94)             # #22c55e
    WARNING = QColor(251, 146, 60)            # #fb923c
    ERROR = QColor(239, 68, 68)               # #ef4444
    INFO = QColor(59, 130, 246)               # #3b82f6


def create_gradient_stylesheet(start_color: QColor, end_color: QColor, 
                             direction: str = "vertical") -> str:
    """
    Create a gradient stylesheet string.
    
    Args:
        start_color: Starting color
        end_color: Ending color
        direction: "vertical" or "horizontal"
        
    Returns:
        CSS gradient string
    """
    if direction == "vertical":
        return f"""
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {start_color.name()}, stop:1 {end_color.name()});
        """
    else:
        return f"""
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {start_color.name()}, stop:1 {end_color.name()});
        """