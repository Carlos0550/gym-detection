"""Verificación básica de vivacidad anti-spoofing.

Combina movimiento de cabeza (desplazamiento de bbox/keypoints) y
consistencia de identidad entre frames consecutivos.
"""

from __future__ import annotations

import math

import numpy as np

from app.modules.face.engine import FaceEngine
from app.modules.face.exceptions import MultipleFacesError, NoFaceDetectedError
from app.modules.face.liveness import LivenessFailedError
from app.modules.face.schemas import FaceDetection


class LivenessChecker:
    MIN_FRAMES = 2
    MIN_BBOX_MOVEMENT_PX = 5.0
    MIN_KPS_MOVEMENT_PX = 3.0
    MIN_INTER_FRAME_SIMILARITY = 0.85

    def detect_all(self, face_engine: FaceEngine, frames: list[bytes]) -> list[FaceDetection]:
        detections: list[FaceDetection] = []
        for index, frame in enumerate(frames):
            faces = face_engine.detect_faces(frame)
            if not faces:
                raise LivenessFailedError(f"Frame {index + 1}: no se detectó rostro")
            if len(faces) > 1:
                raise LivenessFailedError(
                    f"Frame {index + 1}: se detectaron {len(faces)} rostros"
                )
            detections.append(faces[0])
        return detections

    def verify_detections(
        self, face_engine: FaceEngine, detections: list[FaceDetection]
    ) -> FaceDetection:
        """Valida vivacidad sobre detecciones ya calculadas."""
        if len(detections) < self.MIN_FRAMES:
            raise LivenessFailedError(
                f"Se requieren al menos {self.MIN_FRAMES} frames"
            )
        self._check_identity_consistency(face_engine, detections)
        self._check_movement(detections)
        return detections[-1]

    def verify(self, face_engine: FaceEngine, frames: list[bytes]) -> FaceDetection:
        """Valida vivacidad y devuelve la detección del último frame."""
        if len(frames) < self.MIN_FRAMES:
            raise LivenessFailedError(
                f"Se requieren al menos {self.MIN_FRAMES} frames"
            )

        detections = self.detect_all(face_engine, frames)
        return self.verify_detections(face_engine, detections)

    def _check_identity_consistency(
        self, face_engine: FaceEngine, detections: list[FaceDetection]
    ) -> None:
        base = detections[0].embedding
        for index, detection in enumerate(detections[1:], start=2):
            similarity = face_engine.compute_similarity(base, detection.embedding)
            if similarity < self.MIN_INTER_FRAME_SIMILARITY:
                raise LivenessFailedError(
                    f"Frame {index}: no corresponde a la misma persona "
                    f"(sim={similarity:.2f})"
                )

    def _check_movement(self, detections: list[FaceDetection]) -> None:
        bbox_movement = 0.0
        kps_movement = 0.0

        for prev, curr in zip(detections, detections[1:]):
            bbox_movement += self._bbox_center_distance(prev.bbox, curr.bbox)
            if prev.kps is not None and curr.kps is not None:
                kps_movement += float(np.linalg.norm(curr.kps - prev.kps, axis=1).sum())

        if bbox_movement < self.MIN_BBOX_MOVEMENT_PX and kps_movement < self.MIN_KPS_MOVEMENT_PX:
            raise LivenessFailedError(
                "No se detectó movimiento suficiente (posible foto estática)"
            )

    @staticmethod
    def _bbox_center_distance(
        bbox_a: tuple[int, int, int, int], bbox_b: tuple[int, int, int, int]
    ) -> float:
        ax = (bbox_a[0] + bbox_a[2]) / 2
        ay = (bbox_a[1] + bbox_a[3]) / 2
        bx = (bbox_b[0] + bbox_b[2]) / 2
        by = (bbox_b[1] + bbox_b[3]) / 2
        return math.hypot(bx - ax, by - ay)
