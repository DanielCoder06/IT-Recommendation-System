from pathlib import Path
from datetime import datetime
from src.processing.cv_structure import read_pdf_lines, split_sections
from src.processing.cv_chunker import structure_chunk
from src.processing.semantic_chunker import SemanticChunker
from src.processing.jd_chunker import chunk_jd_text
from src.matching.chunk_similarity_matcher import match_chunks, encode_chunks
from src.matching.chunk_job_scorer import calculate_job_score
from src.processing.job_filter import is_senior_job
from database.job_repository import get_matchable_jobs
from src.processing.job_lifecycle import (
    MATCH_RECENCY_DAYS,
    job_age_days,
    parse_datetime,
    recency_multiplier,
    utc_now,
)

CV_CORE_SECTIONS = {
    "SKILLS",
    "PROJECTS",
    "EXPERIENCE",
    "WORK EXPERIENCE",
    "PROFILE",
    "SUMMARY",
}

JD_WORDS_PER_CHUNK = 120
SCORE_TOP_K_REQS = 3

# Khởi tạo semantic chunker dùng chung
semantic_chunker = SemanticChunker(
    breakpoint_percentile=70.0,
    min_distance=0.15,
    min_chars=120,
    max_chars=500,
    window=1,
)

def recommend_jobs_for_cv(
    pdf_path: str | Path,
    exclude_senior: bool = True,
    top_k: int = 9,
) -> list[dict]:
    """
    Nhận đường dẫn PDF CV, thực hiện pipeline structure-based + semantic chunking
    và so khớp với các công việc trong database.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        return []

    # 1. Trích xuất CV
    cv_lines = read_pdf_lines(pdf_path)
    cv_sections = split_sections(cv_lines)
    cv_structured_chunks = structure_chunk(cv_sections)
    cv_structured_chunks = [
        c for c in cv_structured_chunks if c.section in CV_CORE_SECTIONS
    ]

    cv_chunks_text = []
    for section_chunk in cv_structured_chunks:
        sub_chunks = semantic_chunker.chunk_text(
            section_chunk.text,
            header=section_chunk.header,
        )
        cv_chunks_text.extend(sub_chunks)

    if not cv_chunks_text:
        return []

    # Encode vector CV chunks
    cv_embeddings = encode_chunks(cv_chunks_text)

    # 2. Lấy Matchable Jobs
    now = utc_now()
    jobs = get_matchable_jobs(recency_days=MATCH_RECENCY_DAYS)

    if exclude_senior:
        jobs = [
            j for j in jobs
            if not is_senior_job(j.get("title", ""), j.get("experience", ""))
        ]

    results = []
    for job in jobs:
        jd_text = job.get("description", "")
        if not jd_text:
            continue

        jd_chunks_dict = chunk_jd_text(
            text=jd_text,
            max_words=JD_WORDS_PER_CHUNK,
            overlap_units=0,
        )

        important_jd_chunks = [
            chunk["text"] for chunk in jd_chunks_dict
            if chunk.get("category") in ["REQUIREMENT", "RESPONSIBILITY"]
        ]

        if not important_jd_chunks:
            continue

        chunk_matches = match_chunks(
            query_chunks=important_jd_chunks,
            candidate_chunks=cv_chunks_text,
            candidate_embeddings=cv_embeddings,
        )

        score = calculate_job_score(chunk_matches, top_k=SCORE_TOP_K_REQS)
        age_days = job_age_days(
            parse_datetime(job.get("posted_date")),
            parse_datetime(job.get("created_at")),
            now,
        )
        ranked_score = score["job_score"] * recency_multiplier(age_days)

        # Tính phần trăm độ phù hợp (0% - 100%)
        match_percentage = min(100, max(0, round(ranked_score * 100, 1)))

        results.append({
            "id": job.get("id"),
            "title": job.get("title") or "N/A",
            "company": job.get("company") or "Chưa rõ",
            "location": job.get("location") or "Toàn quốc",
            "experience": job.get("experience") or "Không yêu cầu",
            "url": job.get("url") or "#",
            "score": ranked_score,
            "match_percentage": match_percentage,
        })

    # Sắp xếp theo điểm số cao nhất
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]
