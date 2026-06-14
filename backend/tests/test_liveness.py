"""Tests de liveness checker."""

import pytest

from app.modules.face.liveness import LivenessFailedError
from app.modules.face.liveness_checker import LivenessChecker
from tests.face_mock import MockFaceEngine


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
