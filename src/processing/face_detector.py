#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import numpy as np
import logging
from typing import List, Tuple, Optional, Dict, Any

logger = logging.getLogger(__name__)


class FaceDetector:

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.detector = None
        self.detection_method = "none"

        if self._initialize_mediapipe():
            self.detection_method = "mediapipe"
        elif self._initialize_haar_cascade():
            self.detection_method = "haar_cascade"
        else:
            self.logger.warning("No face detection method available")

    def _initialize_mediapipe(self) -> bool:
        try:
            import importlib
            try:
                mp = importlib.import_module("mediapipe")
            except ImportError:
                self.logger.info("MediaPipe not available")
                return False

            mp_face_detection = mp.solutions.face_detection
            self.detector = mp_face_detection.FaceDetection(
                model_selection=1,
                min_detection_confidence=0.5
            )

            self.logger.info("MediaPipe Face Detection initialized")
            return True

        except Exception as e:
            self.logger.warning(f"Failed to initialize MediaPipe: {e}")
            return False

    def _initialize_haar_cascade(self) -> bool:
        try:
            import os

            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'

            if not os.path.exists(cascade_path):
                self.logger.warning(f"Haar cascade file not found: {cascade_path}")
                return False

            self.detector = cv2.CascadeClassifier(cascade_path)

            if self.detector.empty():
                self.logger.warning("Haar cascade failed to load")
                self.detector = None
                return False

            self.logger.info("Haar Cascade face detection initialized")
            return True

        except Exception as e:
            self.logger.warning(f"Failed to initialize Haar Cascade: {e}")
            return False

    def detect_faces(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        if self.detector is None:
            return []

        try:
            if self.detection_method == "mediapipe":
                return self._detect_faces_mediapipe(image)
            elif self.detection_method == "haar_cascade":
                return self._detect_faces_haar(image)
            else:
                return []

        except Exception as e:
            self.logger.warning(f"Face detection failed: {e}")
            return []

    def _detect_faces_mediapipe(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        if len(image.shape) == 2:
            image_bgr = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        else:
            image_bgr = image

        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

        results = self.detector.process(image_rgb)

        if not results.detections:
            return []

        faces = []
        height, width = image.shape[:2]

        for detection in results.detections:
            bbox = detection.location_data.relative_bounding_box

            x = int(bbox.xmin * width)
            y = int(bbox.ymin * height)
            w = int(bbox.width * width)
            h = int(bbox.height * height)

            x = max(0, x)
            y = max(0, y)
            w = min(w, width - x)
            h = min(h, height - y)

            if w > 0 and h > 0:
                faces.append((x, y, w, h))

        return faces

    def _detect_faces_haar(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        faces = self.detector.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=4,
            minSize=(30, 30)
        )

        return faces.tolist() if len(faces) > 0 else []

    def detect_faces_with_confidence(self, image: np.ndarray) -> List[Dict[str, Any]]:
        if self.detector is None or self.detection_method != "mediapipe":
            faces = self.detect_faces(image)
            return [{'bbox': face, 'confidence': 0.8} for face in faces]

        try:
            if len(image.shape) == 2:
                image_bgr = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            else:
                image_bgr = image

            image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

            results = self.detector.process(image_rgb)

            if not results.detections:
                return []

            detections = []
            height, width = image.shape[:2]

            for detection in results.detections:
                bbox = detection.location_data.relative_bounding_box
                x = int(bbox.xmin * width)
                y = int(bbox.ymin * height)
                w = int(bbox.width * width)
                h = int(bbox.height * height)

                x = max(0, x)
                y = max(0, y)
                w = min(w, width - x)
                h = min(h, height - y)

                if w > 0 and h > 0:
                    confidence = detection.score[0] if hasattr(detection, 'score') else 0.8

                    landmarks = []
                    if hasattr(detection.location_data, 'relative_keypoints'):
                        for keypoint in detection.location_data.relative_keypoints:
                            landmarks.append({
                                'x': int(keypoint.x * width),
                                'y': int(keypoint.y * height)
                            })

                    detections.append({
                        'bbox': (x, y, w, h),
                        'confidence': float(confidence),
                        'landmarks': landmarks
                    })

            return detections

        except Exception as e:
            self.logger.warning(f"Detailed face detection failed: {e}")
            faces = self.detect_faces(image)
            return [{'bbox': face, 'confidence': 0.8} for face in faces]

    def is_available(self) -> bool:
        return self.detector is not None

    def get_method(self) -> str:
        return self.detection_method


_global_face_detector: Optional[FaceDetector] = None


def get_face_detector() -> FaceDetector:
    global _global_face_detector

    if _global_face_detector is None:
        _global_face_detector = FaceDetector()

    return _global_face_detector
