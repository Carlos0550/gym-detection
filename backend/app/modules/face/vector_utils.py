"""Helpers para vectores pgvector."""

from __future__ import annotations

import numpy as np


def to_embedding_list(embedding: np.ndarray | list[float]) -> list[float]:
    if isinstance(embedding, np.ndarray):
        return embedding.astype(np.float32).tolist()
    return list(embedding)


def average_embeddings(embeddings: list[np.ndarray]) -> np.ndarray:
    """Promedia varios embeddings en una referencia única y robusta.

    Cada vector se normaliza a magnitud 1 antes de promediar para que ninguna
    pose pese más que otra; el resultado se vuelve a normalizar para obtener la
    dirección media. Así la referencia representa el rostro en conjunto
    (centro + giros) en lugar de una sola pose.
    """
    if not embeddings:
        raise ValueError("Se requiere al menos un embedding para promediar")

    stacked = np.stack(
        [np.asarray(e, dtype=np.float32).ravel() for e in embeddings]
    )
    norms = np.linalg.norm(stacked, axis=1, keepdims=True)
    norms[norms == 0.0] = 1.0
    unit = stacked / norms

    mean = unit.mean(axis=0)
    mean_norm = float(np.linalg.norm(mean))
    if mean_norm == 0.0:
        return mean.astype(np.float32)
    return (mean / mean_norm).astype(np.float32)
