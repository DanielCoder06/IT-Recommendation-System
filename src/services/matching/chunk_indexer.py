import logging
import numpy as np
from src.config import settings
from src.services.processing.jd_chunker import chunk_jd_text
from src.services.embeddings.chunk_similarity_matcher import encode_chunks
from src.models.repositories.chunk_repository import (
    hash_description,
    get_job_description_hash,
    save_job_chunks,
)

logger = logging.getLogger(__name__)

# Cache RAM lưu trữ vector embedding của các job
_RAM_EMBEDDING_CACHE: dict[int, list[dict]] = {}

def invalidate_ram_cache() -> None:
    """Xóa sạch cache RAM sau mỗi đợt crawl/cập nhật dữ liệu mới."""
    global _RAM_EMBEDDING_CACHE
    _RAM_EMBEDDING_CACHE.clear()
    logger.info("Đã xóa sạch cache RAM embeddings của JD.")

def index_job_chunks(job_id: int, description: str, force: bool = False) -> bool:
    """Cắt chunk, encode vector và lưu vào bảng job_chunks."""
    if not description:
        return False

    desc_hash = hash_description(description)
    if not force:
        existing_hash = get_job_description_hash(job_id)
        if existing_hash == desc_hash:
            return False

    # Cắt nhỏ văn bản (trả về tất cả category)
    chunks_dict = chunk_jd_text(description, max_words=settings.JD_WORDS_PER_CHUNK)
    
    # Lọc chỉ giữ lại các chunk có category là REQUIREMENT hoặc RESPONSIBILITY
    valid_categories = ("REQUIREMENT", "RESPONSIBILITY")
    filtered_chunks = [
        c for c in chunks_dict
        if c.get("category") in valid_categories
    ]
    
    if not filtered_chunks:
        logger.info("Job %d không có chunk REQUIREMENT hay RESPONSIBILITY nào.", job_id)
        skip_chunk = [{"text": "No requirements found", "category": "SKIPPED"}]
        skip_chunk_embeddings = np.zeros((1,384), dtype=np.float32)
        save_job_chunks (
            job_id=job_id,
            chunks=skip_chunk,
            embeddings=skip_chunk_embeddings,
            description_hash=desc_hash,
        )
        return False
    
    # Sinh vector và lưu
    chunk_texts = [c["text"] for c in filtered_chunks]
    embeddings = encode_chunks(chunk_texts)

    save_job_chunks(
        job_id=job_id,
        chunks=filtered_chunks,
        embeddings=embeddings,
        description_hash=desc_hash,
    )
    return True