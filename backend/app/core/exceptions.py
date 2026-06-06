"""Excepciones de dominio y helpers para FastAPI."""

from fastapi import HTTPException, status


class DomainError(HTTPException):
    """Error de dominio base. Status 422 por defecto."""

    def __init__(self, detail: str, status_code: int = status.HTTP_422_UNPROCESSABLE_ENTITY):
        super().__init__(status_code=status_code, detail=detail)


class NotFoundError(DomainError):
    def __init__(self, detail: str = "Recurso no encontrado"):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class ForbiddenError(DomainError):
    def __init__(self, detail: str = "Sin permisos para esta acción"):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)


class UnauthorizedError(DomainError):
    def __init__(self, detail: str = "No autenticado"):
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)


class ConflictError(DomainError):
    def __init__(self, detail: str = "Conflicto con el estado actual"):
        super().__init__(detail=detail, status_code=status.HTTP_409_CONFLICT)
