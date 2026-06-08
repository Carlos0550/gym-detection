"""Módulo del motor facial: wrapper de InsightFace."""

from .exceptions import (
    FaceEngineError,
    FaceExtractionError,
    LowQualityError,
    MultipleFacesError,
    NoFaceDetectedError,
)
from .schemas import FaceDetection

__all__ = [
    "FaceDetection",
    "FaceEngineError",
    "FaceExtractionError",
    "NoFaceDetectedError",
    "MultipleFacesError",
    "LowQualityError",
]