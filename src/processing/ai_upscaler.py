#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import numpy as np
import logging
from typing import Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class AIUpscaler:

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.upsampler = None
        self.available = False
        self.device = None
        self._initialize_realesrgan()

    def _initialize_realesrgan(self) -> None:
        try:
            import importlib
            try:
                realesrgan = importlib.import_module("realesrgan")
                RealESRGANer = realesrgan.RealESRGANer
            except Exception:
                # Let the outer ImportError handler handle unavailable package
                raise ImportError("realesrgan not available")

            try:
                import importlib
                from typing import TYPE_CHECKING
                if TYPE_CHECKING:
                    # Help static type checkers / linters resolve RRDBNet without importing at runtime.
                    from basicsr.archs.rrdbnet_arch import RRDBNet  # type: ignore

                RRDBNet = importlib.import_module("basicsr.archs.rrdbnet_arch").RRDBNet
            except Exception:
                # Fallback stub for RRDBNet so linters/static analysis don't fail when basicsr is not installed.
                # This stub does NOT implement the real network; it only preserves the constructor signature
                # so the rest of the module can import and run in environments where Real-ESRGAN won't be used.
                class RRDBNet:
                    def __init__(self, num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4):
                        self.num_in_ch = num_in_ch
                        self.num_out_ch = num_out_ch
                        self.num_feat = num_feat
                        self.num_block = num_block
                        self.num_grow_ch = num_grow_ch
                        self.scale = scale

                    def __call__(self, *args, **kwargs):
                        raise RuntimeError("RRDBNet stub used because 'basicsr' is not installed; install basicsr for full functionality.")
            import torch

            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'

            model = RRDBNet(
                num_in_ch=3,
                num_out_ch=3,
                num_feat=64,
                num_block=23,
                num_grow_ch=32,
                scale=4
            )

            model_path = Path.home() / '.cache' / 'realesrgan' / 'RealESRGAN_x4plus.pth'

            self.upsampler = RealESRGANer(
                scale=4,
                model_path=str(model_path) if model_path.exists() else 'RealESRGAN_x4plus.pth',
                model=model,
                tile=400 if self.device == 'cuda' else 200,
                tile_pad=10,
                pre_pad=0,
                half=(self.device == 'cuda'),
                device=self.device
            )

            self.available = True
            self.logger.info(f"Real-ESRGAN initialized on {self.device.upper()}")

            if self.device == 'cpu':
                self.logger.warning("Real-ESRGAN running on CPU")

        except ImportError as e:
            self.logger.warning(f"Real-ESRGAN not available: {e}")
            self.available = False

        except Exception as e:
            self.logger.warning(f"Failed to initialize Real-ESRGAN: {e}")
            self.available = False

    def upscale(self, image: np.ndarray, target_scale: float = 4.0) -> Tuple[np.ndarray, str]:
        if not self.available or self.upsampler is None:
            return self._fallback_upscale(image, target_scale)

        try:
            if len(image.shape) == 2:
                image_bgr = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            else:
                image_bgr = image

            self.logger.info(f"Upscaling {image.shape[1]}x{image.shape[0]} with Real-ESRGAN")

            output, _ = self.upsampler.enhance(image_bgr, outscale=target_scale)

            if len(image.shape) == 2:
                output = cv2.cvtColor(output, cv2.COLOR_BGR2GRAY)

            method = f"AI upscaling (Real-ESRGAN {self.device.upper()})"
            self.logger.info(f"AI upscaling complete: {image.shape[1]}x{image.shape[0]} → {output.shape[1]}x{output.shape[0]}")

            return output, method

        except Exception as e:
            self.logger.error(f"Real-ESRGAN upscaling failed: {e}", exc_info=True)
            self.logger.warning("Falling back to traditional upscaling")
            return self._fallback_upscale(image, target_scale)

    def _fallback_upscale(self, image: np.ndarray, scale: float) -> Tuple[np.ndarray, str]:
        height, width = image.shape[:2]
        new_width = int(width * scale)
        new_height = int(height * scale)

        upscaled = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
        method = "Traditional upscaling (Lanczos4)"

        return upscaled, method

    def is_available(self) -> bool:
        return self.available

    def get_device(self) -> Optional[str]:
        return self.device if self.available else None

    def upscale_to_target_size(self, image: np.ndarray, target_min_dimension: int) -> Tuple[np.ndarray, str]:
        height, width = image.shape[:2]
        current_min = min(width, height)

        if current_min >= target_min_dimension:
            return image, "No upscaling needed"

        required_scale = target_min_dimension / current_min

        if required_scale <= 2.5:
            use_scale = 2.0
        else:
            use_scale = 4.0

        if required_scale > 4.0:
            self.logger.info(f"Large upscaling needed ({required_scale:.1f}x), performing multiple passes")

            result, method1 = self.upscale(image, 4.0)

            current_min_after = min(result.shape[:2])
            remaining_scale = target_min_dimension / current_min_after

            if remaining_scale > 1.1:
                result, method2 = self.upscale(result, remaining_scale)
                method = f"{method1}, then {method2}"
            else:
                method = method1
        else:
            result, method = self.upscale(image, use_scale)

            current_min_after = min(result.shape[:2])
            if current_min_after != target_min_dimension:
                final_scale = target_min_dimension / current_min_after
                h, w = result.shape[:2]
                new_w = int(w * final_scale)
                new_h = int(h * final_scale)
                result = cv2.resize(result, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
                method += f" + fine-tune to exact size"

        return result, method


_global_upscaler: Optional[AIUpscaler] = None


def get_ai_upscaler() -> AIUpscaler:
    global _global_upscaler

    if _global_upscaler is None:
        _global_upscaler = AIUpscaler()

    return _global_upscaler
