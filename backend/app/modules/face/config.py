MAX_IMAGE_BYTES: int = 10 *1024*1024

ACCEPTED_IMAGE_FORMATS:frozenset[str] = frozenset({
    "JPEG", "PNG", "WEBP"
})

EMBEDDING_DIM: int = 512