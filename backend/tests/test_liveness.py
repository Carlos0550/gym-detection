"""Tests de liveness checker."""

import math

import numpy as np
import pytest

from app.modules.face.liveness import LivenessFailedError
from app.modules.face.liveness_checker import LivenessChecker
from app.modules.face.schemas import FaceDetection
from tests.face_mock import MockFaceEngine, _embedding_from_key


def _detection(nose_x: float, embedding_key: str = "same") -> FaceDetection:
    kps = np.array(
        [
            [100.0, 100.0],
            [200.0, 100.0],
            [nose_x, 150.0],
            [110.0, 190.0],
            [190.0, 190.0],
        ],
        dtype=np.float32,
    )
    return FaceDetection(
        bbox=(50, 50, 250, 250),
        det_score=0.95,
        embedding=_embedding_from_key(embedding_key),
        kps=kps,
    )


def _embedding_with_similarity(
    base: np.ndarray, target_sim: float, seed: str
) -> np.ndarray:
    """Construye un embedding con similitud coseno controlada respecto a base."""
    base_vec = np.asarray(base, dtype=np.float32).ravel()
    base_vec /= np.linalg.norm(base_vec)
    rng = np.random.default_rng(hash(seed) % 2**32)
    noise = rng.standard_normal(base_vec.shape).astype(np.float32)
    noise -= np.dot(noise, base_vec) * base_vec
    noise_norm = float(np.linalg.norm(noise))
    if noise_norm < 1e-6:
        raise ValueError("No se pudo generar componente ortogonal")
    noise /= noise_norm
    theta = math.acos(max(-1.0, min(1.0, target_sim)))
    vec = math.cos(theta) * base_vec + math.sin(theta) * noise
    return vec.astype(np.float32)


def _guided_detections(
    *,
    center_nose: float = 150.0,
    left_nose: float = 130.0,
    right_nose: float = 170.0,
    center_to_turn_sim: float | None = None,
    left_to_right_sim: float | None = None,
) -> list[FaceDetection]:
    base = _embedding_from_key("person")
    if center_to_turn_sim is None:
        return [
            _detection(center_nose, "person"),
            _detection(left_nose, "person"),
            _detection(right_nose, "person"),
        ]

    left_emb = _embedding_with_similarity(base, center_to_turn_sim, "left")
    if left_to_right_sim is None:
        right_emb = _embedding_with_similarity(base, center_to_turn_sim, "right")
    else:
        right_emb = _embedding_with_similarity(left_emb, left_to_right_sim, "right")
    return [
        FaceDetection(
            bbox=(50, 50, 250, 250),
            det_score=0.95,
            embedding=base,
            kps=_detection(center_nose).kps,
        ),
        FaceDetection(
            bbox=(50, 50, 250, 250),
            det_score=0.95,
            embedding=left_emb,
            kps=_detection(left_nose).kps,
        ),
        FaceDetection(
            bbox=(50, 50, 250, 250),
            det_score=0.95,
            embedding=right_emb,
            kps=_detection(right_nose).kps,
        ),
    ]


def test_liveness_passes_with_movement():
    engine = MockFaceEngine()
    checker = LivenessChecker()
    detection = checker.verify(engine, [b"frame-a", b"frame-b"])
    assert detection.det_score > 0


def test_liveness_fails_with_single_frame():
    engine = MockFaceEngine()
    checker = LivenessChecker()
    with pytest.raises(LivenessFailedError):
        checker.verify(engine, [b"only-one"])


def test_standard_verify_fails_turned_poses_with_fixed_bbox():
    """Reproduce el bug: poses válidas pero verify() estricto falla."""
    engine = MockFaceEngine()
    checker = LivenessChecker()
    detections = _guided_detections(center_to_turn_sim=0.72)

    with pytest.raises(LivenessFailedError, match="no corresponde a la misma persona"):
        checker.verify_detections(engine, detections)


def test_guided_enroll_passes_with_head_turns_and_fixed_bbox():
    engine = MockFaceEngine()
    checker = LivenessChecker()
    detections = _guided_detections(center_to_turn_sim=0.72)

    result = checker.verify_guided_enroll_detections(engine, detections)
    assert result.det_score > 0


def test_guided_enroll_passes_with_same_embedding():
    engine = MockFaceEngine()
    checker = LivenessChecker()
    detections = _guided_detections()

    result = checker.verify_guided_enroll_detections(engine, detections)
    assert result is detections[-1]


def test_guided_enroll_fails_without_yaw_variation():
    engine = MockFaceEngine()
    checker = LivenessChecker()
    detections = _guided_detections(
        center_nose=150.0,
        left_nose=149.0,
        right_nose=151.0,
    )

    with pytest.raises(LivenessFailedError, match="variación de orientación"):
        checker.verify_guided_enroll_detections(engine, detections)


def test_guided_enroll_fails_different_people():
    engine = MockFaceEngine()
    checker = LivenessChecker()
    detections = [
        _detection(150.0, "person-a"),
        _detection(130.0, "person-b"),
        _detection(170.0, "person-c"),
    ]

    with pytest.raises(LivenessFailedError, match="no parece ser la misma persona"):
        checker.verify_guided_enroll_detections(engine, detections)
