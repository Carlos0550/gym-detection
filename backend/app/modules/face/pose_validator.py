"""Validación de pose guiada para enrolamiento (centro / izquierda / derecha)."""

from __future__ import annotations

from enum import StrEnum

import numpy as np

from app.modules.face.liveness import LivenessFailedError
from app.modules.face.schemas import FaceDetection


class EnrollPoseStep(StrEnum):
    CENTER = "center"
    LEFT = "left"
    RIGHT = "right"


GUIDED_ENROLL_STEPS: tuple[EnrollPoseStep, ...] = (
    EnrollPoseStep.CENTER,
    EnrollPoseStep.LEFT,
    EnrollPoseStep.RIGHT,
)

# Offset normalizado de la nariz respecto al centro de los ojos (eye span = 1.0).
CENTER_MAX_YAW = 0.08
TURN_MIN_YAW = 0.12


def estimate_head_yaw(detection: FaceDetection) -> float:
    """Estima yaw horizontal aproximado desde landmarks 2D (InsightFace 5 puntos)."""
    if detection.kps is None:
        raise LivenessFailedError("No se detectaron landmarks faciales")

    left_eye = detection.kps[0]
    right_eye = detection.kps[1]
    nose = detection.kps[2]

    eye_span = float(abs(right_eye[0] - left_eye[0]))
    if eye_span < 1e-3:
        raise LivenessFailedError("No se pudo estimar la orientación del rostro")

    eye_center_x = (float(left_eye[0]) + float(right_eye[0])) / 2
    return (float(nose[0]) - eye_center_x) / eye_span


def validate_enroll_pose(detection: FaceDetection, step: EnrollPoseStep) -> None:
    """Valida que un frame cumpla la pose pedida en el paso guiado.

    Los frames del enrolamiento guiado vienen espejados (vista selfie del
    frontend), por lo que el signo del yaw queda invertido respecto a una foto
    estándar: girar a la izquierda del usuario desplaza la nariz hacia la
    izquierda de la imagen (yaw negativo).
    """
    yaw = estimate_head_yaw(detection)

    if step == EnrollPoseStep.CENTER:
        if abs(yaw) > CENTER_MAX_YAW:
            raise LivenessFailedError(
                "Centrá tu rostro: mirá de frente a la cámara"
            )
        return

    if step == EnrollPoseStep.LEFT:
        if yaw > -TURN_MIN_YAW:
            raise LivenessFailedError(
                "Girá la cabeza hacia tu izquierda (mostrá el costado izquierdo)"
            )
        return

    if step == EnrollPoseStep.RIGHT:
        if yaw < TURN_MIN_YAW:
            raise LivenessFailedError(
                "Girá la cabeza hacia tu derecha (mostrá el costado derecho)"
            )
        return

    raise LivenessFailedError(f"Paso de pose inválido: {step}")


def validate_guided_enroll_poses(detections: list[FaceDetection]) -> None:
    """Valida la secuencia completa centro → izquierda → derecha."""
    if len(detections) != len(GUIDED_ENROLL_STEPS):
        raise LivenessFailedError(
            f"Se requieren {len(GUIDED_ENROLL_STEPS)} frames guiados "
            "(centro, izquierda, derecha)"
        )

    yaws = [estimate_head_yaw(detection) for detection in detections]

    for detection, step in zip(detections, GUIDED_ENROLL_STEPS, strict=True):
        validate_enroll_pose(detection, step)

    if yaws[1] >= yaws[0] - 0.05:
        raise LivenessFailedError(
            "Paso izquierda: girá más hacia la izquierda respecto al centro"
        )
    if yaws[2] <= yaws[0] + 0.05:
        raise LivenessFailedError(
            "Paso derecha: girá más hacia la derecha respecto al centro"
        )
