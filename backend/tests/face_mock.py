"""Mock del motor facial para tests de integración."""

from __future__ import annotations

import hashlib

import numpy as np

from app.modules.face.config import EMBEDDING_DIM
from app.modules.face.schemas import FaceDetection


def _embedding_from_key(key: str) -> np.ndarray:
    digest = hashlib.sha256(key.encode()).digest()
    rng = np.random.default_rng(int.from_bytes(digest[:8], "big"))
    vec = rng.standard_normal(EMBEDDING_DIM).astype(np.float32)
    vec /= np.linalg.norm(vec)
    return vec


def _embedding_from_bytes(data: bytes) -> np.ndarray:
    key = hashlib.sha256(data).hexdigest()[:16]
    return _embedding_from_key(key)


class MockFaceEngine:
    """Motor facial determinista para tests."""

    is_loaded = True

    def __init__(self) -> None:
        self._call_count = 0
        self._enrolled_key: str | None = None
        self._session_key: str | None = None

    def extract_embedding(self, image_bytes: bytes) -> np.ndarray:
        self._enrolled_key = hashlib.sha256(image_bytes).hexdigest()[:16]
        return _embedding_from_key(self._enrolled_key)

    def detect_faces(self, image_bytes: bytes) -> list[FaceDetection]:
        self._call_count += 1
        shift = self._call_count * 12

        if self._enrolled_key is not None:
            key = self._enrolled_key
        else:
            if self._session_key is None:
                self._session_key = hashlib.sha256(image_bytes).hexdigest()[:16]
            key = self._session_key

        embedding = _embedding_from_key(key)

        base_left = 100.0 + shift
        base_right = 200.0 + shift
        eye_center = (base_left + base_right) / 2
        eye_span = base_right - base_left
        pose_index = (self._call_count - 1) % 3
        if pose_index == 0:
            nose_x = eye_center
        elif pose_index == 1:
            nose_x = eye_center + 0.18 * eye_span
        else:
            nose_x = eye_center - 0.18 * eye_span

        kps = np.array(
            [
                [base_left, 100],
                [base_right, 100],
                [nose_x, 150],
                [110 + shift, 190],
                [190 + shift, 190],
            ],
            dtype=np.float32,
        )
        return [
            FaceDetection(
                bbox=(50 + shift, 50, 250 + shift, 250),
                det_score=0.95,
                embedding=embedding,
                kps=kps,
            )
        ]

    def compute_similarity(
        self, embedding_a: np.ndarray, embedding_b: np.ndarray
    ) -> float:
        a = np.asarray(embedding_a, dtype=np.float32).ravel()
        b = np.asarray(embedding_b, dtype=np.float32).ravel()
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def reset(self) -> None:
        self._call_count = 0
        self._session_key = None
