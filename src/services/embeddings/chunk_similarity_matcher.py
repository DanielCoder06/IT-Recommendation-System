import numpy as np
from src.services.embeddings.embedding_model import model

def encode_chunks(chunks: list[str]) -> np.ndarray:
    """Encode danh sách chunks thành vector (đã chuẩn hóa L2)."""
    if not chunks:
        return np.empty((0, 0))
    return model.encode(chunks, normalize_embeddings=True)  