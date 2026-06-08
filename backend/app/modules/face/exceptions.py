"""Excepciones de dominio del motor facial.
"""


class FaceEngineError(Exception):
    """Base para todos los errores del motor facial."""


class FaceExtractionError(FaceEngineError):
    """La imagen no se pudo procesar (formato inválido, bytes corruptos,
    tamaño excedido, etc.)."""


class NoFaceDetectedError(FaceExtractionError):
    """La imagen es válida pero no contiene ninguna cara."""


class MultipleFacesError(FaceExtractionError):
    """La imagen contiene más de una cara. En algunos contextos
    (enrolamiento) querés exactamente una."""

    def __init__(self, count: int) -> None:
        self.count = count
        super().__init__(f"Se detectaron {count} caras; se esperaba 1")


class LowQualityError(FaceExtractionError):
    """La cara detectada no cumple los umbrales de calidad mínimos
    (det_score bajo, cara muy chica, etc.)."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Calidad insuficiente: {reason}")