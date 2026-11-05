import logging
import threading
from typing import Any
from sentence_transformers import SentenceTransformer
from src.config import settings

logger = logging.getLogger(__name__)
_model_instance = None
_model_lock = threading.Lock()

def get_embedding_model(model_name: str | None = None) -> SentenceTransformer:
    """Lazy singleton để load model AI 1 lần duy nhất."""
    global _model_instance
    name = model_name or settings.MODEL_NAME
    if _model_instance is None:
        with _model_lock:
            if _model_instance is None:
                logger.info("Đang load embedding model: %s", name)
                _model_instance = SentenceTransformer(name)
                logger.info("Model đã load thành công: %s", name)
    return _model_instance

class _ModelProxy:
    """Proxy để gọi model.encode() mà không cần load ngay lập tức."""
    def __getattr__(self, name: str) -> Any:
        real_model = get_embedding_model()
        return getattr(real_model, name)

model = _ModelProxy()