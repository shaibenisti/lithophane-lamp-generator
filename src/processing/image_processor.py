#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import numpy as np
import logging
from typing import Dict, Any, Optional

from ..core.settings import Settings
from ..utils.validation import ImageValidator, ValidationError
from ..utils.heic_loader import load_image_with_heic_support
from .image_rescue import ImageRescueSystem
from .image_analyzer import ImageAnalyzer
from .thickness_mapper import ThicknessMapper
from .lithophane_optimizer import LithophaneOptimizer

logger = logging.getLogger(__name__)


class ImageProcessingError(Exception):
    pass


class IntelligentImageProcessor:

    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)

        self.rescue_system = ImageRescueSystem()
        self.analyzer = ImageAnalyzer()
        self.thickness_mapper = ThicknessMapper(settings)
        self.optimizer = LithophaneOptimizer()

        self._last_rescue_report = None

        cv2.setNumThreads(settings.opencv_threads)

    def process_image_for_lithophane(self, image_path: str) -> np.ndarray:
        try:
            validation_result = ImageValidator.validate_image_file(image_path)
            self._log_image_info(validation_result)

            image = self._load_and_convert_image(image_path)

            rescued_image, rescue_report = self.rescue_system.analyze_and_rescue(image)

            if rescue_report['problems_detected']:
                self.logger.info(f"Image rescue applied: {len(rescue_report['problems_detected'])} issues fixed")
                if rescue_report['customer_warning']:
                    self.logger.warning(f"Customer warning generated: Quality score {rescue_report['quality_score']}/100")

            self._last_rescue_report = rescue_report
            image = rescued_image

            # Apply intelligent auto-crop if enabled and beneficial
            if self.settings.enable_portrait_autocrop:
                try:
                    image = self._intelligent_portrait_autocrop(image)
                except Exception as e:
                    self.logger.warning(f"Portrait auto-crop failed, using original image: {e}")

            characteristics = self.analyzer.analyze_image_characteristics(image)
            self.settings._current_has_faces = characteristics['has_faces']

            # Apply optimized processing pipeline
            processed = self._apply_optimized_pipeline(image, characteristics)

            # Generate thickness map
            thickness_map = self.thickness_mapper.create_thickness_map(processed, characteristics, processed)

            self.logger.info(f"Image processing completed successfully")
            return thickness_map

        except ValidationError as e:
            raise ImageProcessingError(f"Image validation failed: {e}")
        except (IOError, OSError) as e:
            self.logger.error(f"File I/O error: {e}", exc_info=True)
            raise ImageProcessingError(f"Failed to read image file: {e}")
        except cv2.error as e:
            self.logger.error(f"OpenCV error: {e}", exc_info=True)
            raise ImageProcessingError(f"Image processing error: {e}")
        except (ValueError, TypeError) as e:
            self.logger.error(f"Invalid image data: {e}", exc_info=True)
            raise ImageProcessingError(f"Invalid image format or data: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error in image processing: {e}", exc_info=True)
            raise ImageProcessingError(f"Unexpected error during image processing: {e}")

    def _load_and_convert_image(self, image_path: str) -> np.ndarray:
        try:
            # Use HEIC-aware loader for broader format support
            image = load_image_with_heic_support(image_path)
            if image is None:
                raise ImageProcessingError(f"Cannot load image from: {image_path}")

            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            return gray

        except Exception as e:
            raise ImageProcessingError(f"Failed to load image: {e}")

    def _apply_optimized_pipeline(self, image: np.ndarray,
                                  characteristics: Dict[str, Any]) -> np.ndarray:
        """
        Optimized processing pipeline.

        Single-pass optimization that preserves facial details.
        No smoothing, no multiple enhancement layers - just clean, effective processing.
        """
        # Get target dimensions
        target_width, target_height, _, _ = self.settings.get_lithophane_dimensions()

        # Single-pass optimization
        optimized = self.optimizer.optimize(image, characteristics, (target_width, target_height))

        self.logger.info(f"Processing complete: {optimized.shape[1]}×{optimized.shape[0]}")
        return optimized

    def get_last_rescue_report(self) -> Optional[Dict[str, Any]]:
        return self._last_rescue_report

    def _intelligent_portrait_autocrop(self, image: np.ndarray) -> np.ndarray:
        """
        Intelligently crop to focus on face when face is too small in frame.

        Only activates when:
        - Face detected
        - Face < 30% of image area

        Returns cropped image with face as primary subject.
        Safe with full error handling - returns original on any failure.
        """
        try:
            # Import here to avoid circular dependencies
            from .face_detector import get_face_detector

            detector = get_face_detector()
            if not detector.is_available():
                return image

            faces = detector.detect_faces(image)
            if not faces or len(faces) == 0:
                return image

            # Get largest face
            primary_face = max(faces, key=lambda f: f[2] * f[3])
            fx, fy, fw, fh = primary_face

            img_height, img_width = image.shape[:2]

            # Calculate face ratio
            face_area = fw * fh
            image_area = img_width * img_height
            face_ratio = face_area / image_area

            self.logger.info(f"Face detection: {fw}×{fh} pixels, {face_ratio*100:.1f}% of image")

            # Only auto-crop if face is small
            AUTOCROP_THRESHOLD = 0.30  # 30%

            if face_ratio >= AUTOCROP_THRESHOLD:
                self.logger.info(f"Face size adequate ({face_ratio*100:.1f}%), no auto-crop needed")
                return image

            self.logger.info(f"Face too small ({face_ratio*100:.1f}%), applying intelligent auto-crop")

            # Target: face should be 55-65% of frame
            target_ratio = 0.60
            scale = (target_ratio / face_ratio) ** 0.5

            # Calculate crop dimensions
            crop_w = int(fw / scale)
            crop_h = int(fh / scale)

            # Ensure portrait orientation
            if crop_h / crop_w < 1.2:
                crop_h = int(crop_w * 1.3)

            # Center on face with slight upward bias (rule of thirds)
            face_cx = fx + fw // 2
            face_cy = fy + fh // 2

            # Place eyes in upper third (not center)
            vertical_offset = -int(crop_h * 0.08)

            # Calculate crop box
            x1 = max(0, face_cx - crop_w // 2)
            y1 = max(0, face_cy - crop_h // 2 + vertical_offset)
            x2 = min(img_width, x1 + crop_w)
            y2 = min(img_height, y1 + crop_h)

            # Adjust if out of bounds
            if x2 - x1 < crop_w:
                x1 = max(0, x2 - crop_w)
            if y2 - y1 < crop_h:
                y1 = max(0, y2 - crop_h)

            # Apply crop
            cropped = image[y1:y2, x1:x2].copy()

            # Validate crop result
            if cropped.shape[0] < 100 or cropped.shape[1] < 100:
                self.logger.warning("Crop result too small, using original")
                return image

            self.logger.info(f"✓ Auto-cropped: {img_width}×{img_height} → {cropped.shape[1]}×{cropped.shape[0]} "
                           f"(face now ~{target_ratio*100:.0f}% of frame)")

            return cropped

        except Exception as e:
            self.logger.error(f"Auto-crop failed: {e}", exc_info=True)
            return image

    def _log_image_info(self, validation_result: Dict[str, Any]) -> None:
        quality = validation_result['quality_metrics']
        self.logger.info(
            f"Image loaded: {validation_result['width']}x{validation_result['height']}, "
            f"{validation_result['file_size_mb']:.1f}MB, "
            f"quality score: {quality['quality_score']:.1f}/100"
        )

        if quality['warnings']:
            for warning in quality['warnings']:
                self.logger.warning(f"Image quality: {warning}")
