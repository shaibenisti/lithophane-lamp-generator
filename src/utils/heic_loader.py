#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
import logging
from pathlib import Path
from typing import Optional
import tempfile

logger = logging.getLogger(__name__)


class HEICLoader:

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.available = False

        try:
            from pillow_heif import register_heif_opener
            from PIL import Image
            register_heif_opener()
            self.available = True
            self.logger.info("HEIC support available")
        except ImportError:
            self.logger.info("HEIC support not available")

    def is_heic_file(self, file_path: str) -> bool:
        path = Path(file_path)
        return path.suffix.lower() in {'.heic', '.heif'}

    def load_heic(self, file_path: str) -> Optional[np.ndarray]:
        if not self.available:
            self.logger.error("HEIC support not available")
            return None

        try:
            from PIL import Image
            import cv2

            image = Image.open(file_path)

            if image.mode != 'RGB':
                image = image.convert('RGB')

            image_np = np.array(image)
            image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

            self.logger.info(f"Successfully loaded HEIC image: {image_bgr.shape[1]}x{image_bgr.shape[0]}")

            return image_bgr

        except Exception as e:
            self.logger.error(f"Failed to load HEIC file: {e}")
            return None

    def load_heic_as_grayscale(self, file_path: str) -> Optional[np.ndarray]:
        image_bgr = self.load_heic(file_path)

        if image_bgr is None:
            return None

        try:
            import cv2
            gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
            return gray

        except Exception as e:
            self.logger.error(f"Failed to convert HEIC to grayscale: {e}")
            return None

    def convert_heic_to_jpeg(self, heic_path: str, jpeg_path: Optional[str] = None) -> Optional[str]:
        if not self.available:
            self.logger.error("HEIC support not available")
            return None

        try:
            from PIL import Image

            image = Image.open(heic_path)

            if image.mode != 'RGB':
                image = image.convert('RGB')

            if jpeg_path is None:
                temp_fd, jpeg_path = tempfile.mkstemp(suffix='.jpg')
                import os
                os.close(temp_fd)

            image.save(jpeg_path, 'JPEG', quality=95)

            self.logger.info(f"Converted HEIC to JPEG: {jpeg_path}")
            return jpeg_path

        except Exception as e:
            self.logger.error(f"Failed to convert HEIC to JPEG: {e}")
            return None

    def get_heic_metadata(self, file_path: str) -> Optional[dict]:
        if not self.available:
            return None

        try:
            from PIL import Image
            from PIL.ExifTags import TAGS

            image = Image.open(file_path)

            exif_data = image.getexif()

            if exif_data is None:
                return {}

            metadata = {}
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                metadata[tag] = value

            return metadata

        except Exception as e:
            self.logger.warning(f"Failed to extract HEIC metadata: {e}")
            return None


_global_heic_loader: Optional[HEICLoader] = None


def get_heic_loader() -> HEICLoader:
    global _global_heic_loader

    if _global_heic_loader is None:
        _global_heic_loader = HEICLoader()

    return _global_heic_loader


def is_heic_supported() -> bool:
    loader = get_heic_loader()
    return loader.available


def load_image_with_heic_support(file_path: str) -> Optional[np.ndarray]:
    import cv2

    loader = get_heic_loader()

    if loader.is_heic_file(file_path):
        if loader.available:
            return loader.load_heic(file_path)
        else:
            logger.error(f"HEIC file detected but support not available: {file_path}")
            return None

    try:
        image = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
        return image
    except Exception as e:
        logger.error(f"Failed to load image: {e}")
        return None
