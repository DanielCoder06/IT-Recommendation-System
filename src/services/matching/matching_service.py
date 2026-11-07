from pathlib import Path
import numpy as np
import logging

from src.models.repositories.chunk_repository import get_chunks_for_jobs
from src.models.repositories.job_repository import get_matchable_jobs
from src.config import settings
from src.services.matching.chunk_job_scorer import calculate_job_score
from src.services.embeddings.chunk_similarity_matcher import encode_chunks
from src.services.matching.chunk_indexer import _RAM_EMBEDDING_CACHE, index_job_chunks
from src.services.processing.cv_chunker import MATCHING_SECTIONS, structure_chunk
from src.services.processing.cv_structure import read_pdf_lines, split_sections
from src.services.processing.job_filter import is_senior_job
from src.services.processing.job_lifecycle import (
    job_age_days,
    parse_datetime,
    recency_multiplier,
    utc_now,
)
from src.services.processing.semantic_chunker import SemanticChunker

logger = logging.getLogger(__name__)

# Khởi tạo chunker
_semantic_chunker = SemanticChunker(
    breakpoint_percentile=settings.BREAKPOINT_PERCENTILE,
    min_distance=settings.MIN_DISTANCE,
    min_chars=settings.MIN_CHARS,
    max_chars=settings.MAX_CHARS,
    window=settings.WINDOW,
)

class CVContentError(ValueError):
    """Ngoại lệ khi CV không có nội dung ở các mục cốt lõi."""
    pass


def _get_jd_embeddings_for_jobs(jobs: list[dict]) -> dict[int, list[dict]]:
    """
    Lấy danh sách các chunk (gồm embedding numpy vector và text) cho các jobs.
    Ưu tiên lấy từ cache RAM, nếu thiếu lấy từ database theo batch.
    """
    job_ids = [j["id"] for j in jobs if j.get("id")]
    missing_ids = [jid for jid in job_ids if jid not in _RAM_EMBEDDING_CACHE]

    if missing_ids:
        db_chunks_map = get_chunks_for_jobs(
            missing_ids,
            categories=("REQUIREMENT", "RESPONSIBILITY"),
        )
        for jid in missing_ids:
            chunks = db_chunks_map.get(jid, [])
            if not chunks:
                job_dict = next((j for j in jobs if j.get("id") == jid), None)
                if job_dict and job_dict.get("description"):
                    index_job_chunks(jid, job_dict["description"])
                    chunks = get_chunks_for_jobs([jid]).get(jid, [])
            _RAM_EMBEDDING_CACHE[jid] = chunks

    return {jid: _RAM_EMBEDDING_CACHE.get(jid, []) for jid in job_ids}


def recommend_jobs_for_cv(
    pdf_path: str | Path,
    exclude_senior: bool = True,
    top_k: int = settings.TOP_K,
    return_details: bool = False,
) -> list[dict]:
    """
    Nhận file CV, phân tích và trả về danh sách việc làm đã xếp hạng.
    """
    if top_k is None:
        top_k = settings.TOP_K

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise CVContentError("Không tìm thấy file CV.")

    # 1. Trích xuất và chunking CV theo cấu trúc section
    cv_lines = read_pdf_lines(pdf_path)
    cv_sections = split_sections(cv_lines)
    cv_structured_chunks = structure_chunk(cv_sections)
    cv_structured_chunks = [c for c in cv_structured_chunks if c.section in MATCHING_SECTIONS]

    cv_chunks_text = []
    for section_chunk in cv_structured_chunks:
        sub_chunks = _semantic_chunker.chunk_text(
            section_chunk.text,
            header=section_chunk.header,
        )
        cv_chunks_text.extend(sub_chunks)

    if not cv_chunks_text:
        raise CVContentError(
            "CV không có nội dung ở các mục cốt lõi (SKILLS, EXPERIENCE, PROJECTS, SUMMARY). "
            "Vui lòng kiểm tra định dạng hoặc nội dung file CV."
        )

    # Encode vector cho tất cả CV chunks
    cv_embeddings = encode_chunks(cv_chunks_text)

    # 2. Lấy các job có thể match từ database
    now = utc_now()
    jobs = get_matchable_jobs(recency_days=settings.MATCH_RECENCY_DAYS)

    if exclude_senior:
        jobs = [j for j in jobs if not is_senior_job(j.get("title", ""), j.get("experience", ""))]

    if not jobs:
        return []

    # 3. Lấy pre-computed embeddings từ DB / RAM Cache
    jd_embeddings_map = _get_jd_embeddings_for_jobs(jobs)

    # 4. Tính điểm từng job
    results = []
    for job in jobs:
        job_id = job.get("id")
        jd_chunks = jd_embeddings_map.get(job_id, [])
        if not jd_chunks:
            continue

        # Ma trận embeddings của JD: shape (M_jd, D)
        jd_embs = np.array([c["embedding"] for c in jd_chunks], dtype=np.float32)

        # Tính similarity: (M_jd, N_cv)
        sim_matrix = np.dot(jd_embs, cv_embeddings.T)

        # Với mỗi JD chunk, lấy similarity lớn nhất (CV chunk phù hợp nhất)
        best_indices = np.argmax(sim_matrix, axis=1)
        best_similarities = np.max(sim_matrix, axis=1)

        chunk_matches = [{"similarity": float(sim)} for sim in best_similarities]

        score = calculate_job_score(chunk_matches, top_k=settings.SCORE_TOP_K_REQS)
        
        # Tính tuổi job và áp dụng hệ số giảm điểm
        age_days = job_age_days(
            parse_datetime(job.get("posted_date")),
            parse_datetime(job.get("created_at")),
            now,
        )

        ranked_score = score["job_score"] * recency_multiplier(
            age_days,
            recency_days=settings.MATCH_RECENCY_DAYS,
            floor=settings.RECENCY_SCORE_FLOOR,
        )

        job_result = {
            "id": job.get("id"),
            "title": job.get("title") or "N/A",
            "company": job.get("company") or "N/A",
            "location": job.get("location") or "N/A",
            "experience": job.get("experience") or "N/A",
            "url": job.get("url") or "",
            "_score": ranked_score,
        }

        if return_details:
            details = []
            for i, cv_idx in enumerate(best_indices):
                details.append({
                    "jd_text": jd_chunks[i]["text"],
                    "cv_text": cv_chunks_text[cv_idx],
                    "similarity": float(best_similarities[i])
                })
            details.sort(key=lambda x: x["similarity"], reverse=True)
            job_result["_details"] = details

        results.append(job_result)

    # 5. Xếp hạng theo điểm giảm dần, lấy top_k
    results.sort(key=lambda x: x["_score"], reverse=True)
    results = results[:top_k]

    # 6. Gán rank (1..N)
    for rank, item in enumerate(results, start=1):
        item["rank"] = rank

    return results