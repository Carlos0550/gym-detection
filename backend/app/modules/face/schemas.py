from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from .config import EMBEDDING_DIM

if TYPE_CHECKING:
    from numpy.typing import NDArray

@dataclass(frozen=True)
class FaceDetection:
    bbox: tuple[int,int,int,int]
    det_score: float
    embedding: NDArray[np.float32]

    def __post_init__(self) -> None:
        if self.embedding.shape != (EMBEDDING_DIM,):
            raise ValueError(
                f"embedding debe tener shape ({EMBEDDING_DIM},), "
                f"Recibido: {self.embedding.shape}"
            )
        if not 0.0 <= self.det_score <= 1.0:
            raise ValueError(
                f"det_score fuera de rango [0,1]: {self.det_score}"
            )
