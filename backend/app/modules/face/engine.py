from __future__ import annotations

import time
from typing import TYPE_CHECKING, List

from app.core.logging import logger
from app.modules.face import FaceDetection
from numpy.typing import NDArray
from .config import ACCEPTED_IMAGE_FORMATS, EMBEDDING_DIM, MAX_IMAGE_BYTES
from .exceptions import FaceEngineError, FaceExtractionError, LowQualityError, MultipleFacesError, NoFaceDetectedError

import numpy as np
from io import BytesIO
from PIL import Image


if TYPE_CHECKING:
    from insightface.app import FaceAnalysis
    from app.core.config import Settings

class FaceEngine:
    """Motor de reconocimiento facial.

    Attributes:
        model_name: nombre del modelo InsightFace (``buffalo_l`` por default).
        execution_provider: backend de inferencia (``CPU``, ``CUDA``, etc.).
        det_size: tamaño de entrada del detector ``(width, height)``.
        min_det_score: score mínimo de detección para considerar una
            cara como válida (rechaza detecciones de baja confianza).
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.model_name: str = settings.face_model_name
        self.execution_provider: str = settings.face_execution_provider
        self.det_size: tuple[int,int] = (
            settings.face_det_size_width,
            settings.face_det_size_height
        )
        self.min_det_score:float = settings.face_min_det_score
        self.embedding_dim: int = EMBEDDING_DIM
        self.face_min_size: int = settings.face_min_face_size 
        self.allowed_modules: tuple[str,...] = ("detection", "recognition")
        self._app: FaceAnalysis | None = None
        self._load_model()
    
    def _validate_size(self, image_bytes:bytes) -> None:
        if len(image_bytes) > MAX_IMAGE_BYTES:
            mb = MAX_IMAGE_BYTES // (1024 * 1024)
            raise FaceExtractionError(
                f"Imagen demasiado grande: {len(image_bytes):,} bytes "
                f"(máx permitido: {mb} MB)"
            )

    def _decode_image(self, image_bytes: bytes) -> NDArray[np.uint8]:
        """Decodifica bytes crudos a un array numpy (H, W, 3) en RGB.

        Raises:
            FaceExtractionError: si los bytes son inválidos, el formato
                no está soportado, o el tamaño excede el máximo.

        Notes:
            Validamos en este orden: tamaño → magic bytes (Pillow) →
            formato en whitelist → conversión a RGB.
        """
        self._validate_size(image_bytes)

    
        try:
            img = Image.open(BytesIO(image_bytes))
            # Forzar la decodificación real (catches corruption)
            img.load()
        except Exception as exc:
            raise FaceExtractionError(
                f"Imagen corrupta o formato inválido: {exc}"
            ) from exc

        # Capa 3: whitelist de formatos
        if img.format not in ACCEPTED_IMAGE_FORMATS:
            raise FaceExtractionError(
                f"Formato no soportado: {img.format or 'desconocido'}. "
                f"Aceptados: {sorted(ACCEPTED_IMAGE_FORMATS)}"
            )

        # Capa 4: convertir a RGB (insightface espera 3 canales)
        if img.mode != "RGB":
            img = img.convert("RGB")

        return np.array(img, dtype=np.uint8)

    def detect_faces(self, image_bytes: bytes) -> List[FaceDetection]:
        img_array = self._decode_image(image_bytes)
        raw_faces = self.app.get(img_array)
        detections: list[FaceDetection] = []

        for raw in raw_faces:
            bbox_int = tuple(int(round(x)) for x in raw["bbox"])
            embedding = np.asarray(raw["embedding"], dtype=np.float32)
            detections.append(
                FaceDetection(
                    bbox=bbox_int,
                    det_score=float(raw["det_score"]),
                    embedding=embedding,
                )
            )
        return detections

    def extract_embedding(self, image_bytes: bytes) -> NDArray[np.float32]:
        """Extrae el embedding de una (y solo una) cara de buena calidad.

        Raises:
            NoFaceDetectedError: 0 caras.
            MultipleFacesError: más de 1 cara.
            LowQualityError: det_score bajo o cara demasiado chica.
        """
        faces = self.detect_faces(image_bytes)

        if not faces:
            raise NoFaceDetectedError("No se detectó ninguna cara")
        if len(faces) > 1:
            raise MultipleFacesError(count=len(faces))

        face = faces[0]

        if face.det_score < self.min_det_score:
            raise LowQualityError(
                f"det_score={face.det_score:.3f} < mínimo {self.min_det_score:.3f}"
            )

        x1, y1, x2, y2 = face.bbox
        width, height = x2 - x1, y2 - y1
        if width < self.face_min_size or height < self.face_min_size:
            raise LowQualityError(
                f"cara demasiado chica ({width}x{height}px, "
                f"mínimo {self.face_min_size}px por lado)"
            )

        return face.embedding

    def compute_similarity(
        self,
        embedding_a: NDArray[np.float32],
        embedding_b: NDArray[np.float32]
    ) -> float:
        a = np.asarray(embedding_a, dtype=np.float32).ravel()
        b = np.asarray(embedding_b, dtype=np.float32).ravel()

        norm_a = float(np.linalg.norm(a))
        norm_b = float(np.linalg.norm(b))

        if norm_a == 0.0 or norm_b == 0.0:
            raise FaceEngineError(
                "No se puede calcular similitud con embedding de norma 0"
            )

        return float(np.dot(a,b) / (norm_a * norm_b))

    def _load_model(self) -> None:
        """Carga el model de insightface y si falla deja _app = NOne"""
        from insightface.app import FaceAnalysis

        start = time.perf_counter()
        logger.info(
            "face.model_load.start",
            model=self.model_name,
            provider= self.execution_provider,
            det_size=self.det_size
        )

        try:
            app = FaceAnalysis(
                name=self.model_name,
                allowed_modules=self.allowed_modules,
                providers=[self.execution_provider]
            )
            app.prepare(ctx_id=0, det_size=self.det_size)
        except Exception as exc:
            elapsed = time.perf_counter() - start
            logger.error(
                "face.model_load.failed",
                model=self.model_name,
                elapsed_s=round(elapsed, 2),
                error=str(exc),
                exc_info=True,
            )
            self._app = None
            return

        self._app = app
        elapsed = time.perf_counter() - start
        logger.info(
            "face.model_load.success",
            model=self.model_name,
            provider=self.execution_provider,
            elapsed_s=round(elapsed, 2),
        )
    
    @property
    def is_loaded(self) -> bool:
        """True si el modelo cargó OK y se puede usar para inferencia."""
        return self._app is not None

    @property
    def app(self) -> FaceAnalysis:
        """Devuelve la instancia de ``FaceAnalysis`` lista para inferir.

        Raises:
            FaceEngineError: si el modelo no cargó (degraded mode activo).
        """
        if self._app is None:
            raise FaceEngineError(
                "El motor facial no está cargado. "
                "Revisar logs de startup para más detalles."
            )
        return self._app