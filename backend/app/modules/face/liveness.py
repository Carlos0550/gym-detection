"""Excepciones de vivacidad (anti-spoofing básico)."""


class LivenessError(Exception):
    """Base para errores de verificación de vivacidad."""


class LivenessFailedError(LivenessError):
    """Los frames no demuestran vivacidad suficiente."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Vivacidad no verificada: {reason}")
