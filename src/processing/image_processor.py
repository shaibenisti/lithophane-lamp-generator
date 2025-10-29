#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import numpy as np
import logging
from typing import Dict, Any, Optional

from ..core.settings import PremiumSettings
from ..utils.validation import ImageValidator, ValidationError
from .image_rescue import ImageRescueSystem
from .image_analyzer import ImageAnalyzer
from .image_enhancement import ImageEnhancer
from .image_smoother import ImageSmoother
from .thickness_mapper import ThicknessMapper
from .image_resizer import ImageResizer

logger = logging.getLogger(__name__)


class ImageProcessingError(Exception):
    pass


class IntelligentImageProcessor:

    def __init__(self, settings: PremiumSettings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)

        self.rescue_system = ImageRescueSystem()
        self.analyzer = ImageAnalyzer()
        self.enhancer = ImageEnhancer()
        self.smoother = ImageSmoother()
        self.thickness_mapper = ThicknessMapper(settings)
        self.resizer = ImageResizer()

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

            characteristics = self.analyzer.analyze_image_characteristics(image)
            self.settings._current_has_faces = characteristics['has_faces']

            processed = self._apply_processing_pipeline(image, characteristics)

            smoothed = self.smoother.apply_lithophane_smoothing(processed, characteristics)

            thickness_map = self.thickness_mapper.create_thickness_map(processed, characteristics, smoothed)

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
            image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
            if image is None:
                raise ImageProcessingError(f"Cannot load image from: {image_path}")

            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            return gray

        except Exception as e:
            raise ImageProcessingError(f"Failed to load image: {e}")

    def _apply_processing_pipeline(self, image: np.ndarray,
                                  characteristics: Dict[str, Any]) -> np.ndarray:
        processed = image.astype(np.float64)

        if characteristics['problems']['needs_special_processing']:
            processed = self.resizer.fix_problematic_areas(processed, characteristics['problems'])
            self.logger.info("Applied gentle fixes to problematic areas")

        processed = self._apply_intelligent_enhancement(processed, characteristics)

        target_width, target_height, _, _ = self.settings.get_lithophane_dimensions()
        skip_sharpen = characteristics['image_type'] in ["portrait", "portrait_low_contrast"]
        processed = self.resizer.premium_resize(processed, target_width, target_height, skip_sharpen)

        return np.clip(processed, 0, 255).astype(np.uint8)

    def _apply_intelligent_enhancement(self, image: np.ndarray,
                                     characteristics: Dict[str, Any]) -> np.ndarray:
        image_type = characteristics['image_type']

        if image_type in ["portrait", "portrait_low_contrast"]:
            enhanced = self.enhancer.enhance_portrait(image, characteristics)
        elif image_type == "underexposed":
            enhanced = self.enhancer.correct_underexposure(image)
        elif image_type == "overexposed":
            enhanced = self.enhancer.recover_highlights(image)
        elif image_type == "low_contrast":
            enhanced = self.enhancer.enhance_contrast(image)
        elif image_type == "shadow_heavy":
            enhanced = self.enhancer.lift_shadows(image)
        elif image_type == "highlight_heavy":
            enhanced = self.enhancer.compress_highlights(image)
        else:
            enhanced = image

        enhanced = self.enhancer.apply_universal_enhancement(enhanced, characteristics)

        return enhanced

    def get_last_rescue_report(self) -> Optional[Dict[str, Any]]:
        return self._last_rescue_report

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
