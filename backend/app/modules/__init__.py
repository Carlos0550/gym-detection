"""Módulos de negocio (auth, gyms, members, memberships, face, access_logs).

Cada módulo sigue la convención:
    schemas.py  -> Pydantic DTOs (request/response)
    service.py  -> lógica de negocio
    router.py   -> endpoints FastAPI
    repository.py (opcional) -> queries a DB aisladas

Los módulos concretos se implementan en Etapas 1–5.
"""
