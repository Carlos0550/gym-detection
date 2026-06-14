"""Tests de validación de pose en enrolamiento guiado."""

import numpy as np
import pytest

from app.modules.face.liveness import LivenessFailedError
from app.modules.face.pose_validator import (
    EnrollPoseStep,
    estimate_head_yaw,
    validate_enroll_pose,
    validate_guided_enroll_poses,
)
from app.modules.face.schemas import FaceDetection
from tests.face_mock import _embedding_from_key


def _detection(nose_x: float) -> FaceDetection:
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
        embedding=_embedding_from_key("test"),
        kps=kps,
    )


def test_yaw_center():
    assert abs(estimate_head_yaw(_detection(150.0))) < 0.01


def test_validate_center_rejects_turned_face():
    with pytest.raises(LivenessFailedError, match="Centrá"):
        validate_enroll_pose(_detection(170.0), EnrollPoseStep.CENTER)


def test_validate_left_requires_turn():
    # Frame espejado: izquierda del usuario → nariz desplazada a menor X.
    validate_enroll_pose(_detection(130.0), EnrollPoseStep.LEFT)
    with pytest.raises(LivenessFailedError, match="izquierda"):
        validate_enroll_pose(_detection(150.0), EnrollPoseStep.LEFT)


def test_validate_right_requires_turn():
    # Frame espejado: derecha del usuario → nariz desplazada a mayor X.
    validate_enroll_pose(_detection(170.0), EnrollPoseStep.RIGHT)
    with pytest.raises(LivenessFailedError, match="derecha"):
        validate_enroll_pose(_detection(150.0), EnrollPoseStep.RIGHT)


def test_validate_guided_sequence():
    validate_guided_enroll_poses(
        [_detection(150.0), _detection(130.0), _detection(170.0)]
    )


def test_validate_guided_sequence_rejects_all_center():
    with pytest.raises(LivenessFailedError):
        validate_guided_enroll_poses(
            [_detection(150.0), _detection(151.0), _detection(149.0)]
        )
