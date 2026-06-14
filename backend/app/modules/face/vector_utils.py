"""Helpers para vectores pgvector."""

from __future__ import annotations

import numpy as np


def to_embedding_list(embedding: np.ndarray | list[float]) -> list[float]:
    if isinstance(embedding, np.ndarray):
        return embedding.astype(np.float32).tolist()
    return list(embedding)
