from pathlib import Path

# --- Import CV Pipeline ---
from src.processing.cv_structure import read_pdf_lines, split_sections
from src.processing.cv_chunker import structure_chunk
from src.processing.semantic_chunker import SemanticChunker

# --- Import JD Pipeline ---
from src.processing.jd_chunker import chunk_jd_text

# --- Import Matching ---
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

BASE_DIR = Path(__file__).resolve().parents[2]
CV_PATH = BASE_DIR / "data" / "No-Name.pdf"
TOP_K = 10
JD_WORDS_PER_CHUNK = 120
EXCLUDE_SENIOR = True  # Đặt True để loại bỏ các job Senior / Lead / Principal / Architect / Manager
SCORE_TOP_K_REQS = 3  # Đánh giá dựa trên Top-K requirements/responsibilities khớp nhất của JD

# Section kỹ thuật cốt lõi của CV
CV_CORE_SECTIONS = {
    "SKILLS",
    "PROJECTS",
    "EXPERIENCE",
    "WORK EXPERIENCE",
    "PROFILE",
    "SUMMARY",
}

def load_jobs() -> list[dict]:
    """
    Chỉ lấy job đang active và còn trong cửa sổ re cency.
    """
    return get_matchable_jobs(recency_days=MATCH_RECENCY_DAYS)

def main():
    print("=" * 70)
    print("CV → JOB CHUNK-BASED RECOMMENDATION (SEMANTIC HYBRID)")
    print("=" * 70)

    # --------------------------------------------------
    # 1. XỬ LÝ CV (Structure-Based + Semantic Boundary Chunking)
    # --------------------------------------------------
    cv_lines = read_pdf_lines(CV_PATH)
    cv_sections = split_sections(cv_lines)
    
    # Trích xuất các Section quan trọng
    cv_structured_chunks = structure_chunk(cv_sections)

    # Lọc lấy các Section chuyên môn cốt lõi
    cv_structured_chunks = [
        chunk for chunk in cv_structured_chunks
        if chunk.section in CV_CORE_SECTIONS
    ]

    # Khởi tạo SemanticChunker tinh chỉnh theo ngữ nghĩa
    semantic_chunker = SemanticChunker(
        breakpoint_percentile=70.0,
        min_distance=0.15,
        min_chars=120,
        max_chars=500,
        window=1,
    )

    cv_chunks_text = []
    for section_chunk in cv_structured_chunks:
        # Cắt theo ngữ nghĩa (Semantic Boundary), giữ header ngữ cảnh
        sub_chunks = semantic_chunker.chunk_text(
            section_chunk.text,
            header=section_chunk.header,
        )
        cv_chunks_text.extend(sub_chunks)

    print(f"CV Extracted Core Sections: {len(cv_structured_chunks)}")
    print(f"CV Final Core Semantic Chunks: {len(cv_chunks_text)}")

    if not cv_chunks_text:
        print("CV không có dữ liệu để matching.")
        return

    # TỐI ƯU HIỆU NĂNG: Encode CV chunks 1 lần duy nhất tại đây (thay vì lặp lại ở mỗi job)
    cv_embeddings = encode_chunks(cv_chunks_text)

    # --------------------------------------------------
    # 2. XỬ LÝ JD & MATCHING
    # --------------------------------------------------
    now = utc_now()
    jobs = load_jobs()
    if EXCLUDE_SENIOR:
        jobs = [
            job for job in jobs
            if not is_senior_job(job.get("title", ""), job.get("experience", ""))
        ]
        print(
            f"Jobs loaded (active, last {MATCH_RECENCY_DAYS} days, "
            f"exclude senior): {len(jobs)}"
        )
    else:
        print(
            f"Jobs loaded (active, last {MATCH_RECENCY_DAYS} days): "
            f"{len(jobs)}"
        )

    results = []

    for index, job in enumerate(jobs, start=1):
        jd_text = job.get("description", "")
        
        # Chia JD kèm nhãn Category
        jd_chunks_dict = chunk_jd_text(
            text=jd_text,
            max_words=JD_WORDS_PER_CHUNK,
            overlap_units=0
        )

        # LỌC JD: Chỉ lấy REQUIREMENT và RESPONSIBILITY
        important_jd_chunks = [
            chunk["text"] for chunk in jd_chunks_dict 
            if chunk.get("category") in ["REQUIREMENT", "RESPONSIBILITY"]
        ]

        if not important_jd_chunks:
            continue

        # Đổi chiều matching (Mỗi JD Requirement tìm CV Chunk phù hợp nhất)
        # Sử dụng cv_embeddings đã encode sẵn
        chunk_matches = match_chunks(
            query_chunks=important_jd_chunks,
            candidate_chunks=cv_chunks_text,
            candidate_embeddings=cv_embeddings,
        )

        # Tính điểm dựa trên Top-K requirements khớp nhất của JD
        score = calculate_job_score(chunk_matches, top_k=SCORE_TOP_K_REQS)
        age_days = job_age_days(
            parse_datetime(job.get("posted_date")),
            parse_datetime(job.get("created_at")),
            now,
        )
        ranked_score = score["job_score"] * recency_multiplier(age_days)

        results.append({
            "job_id": index,
            "title": job["title"],
            "company": job["company"],
            "location": job.get("location"),
            "url": job.get("url"),
            "job_score": ranked_score,
        })

    # --------------------------------------------------
    # 3. RANKING & HIỂN THỊ
    # --------------------------------------------------
    ranked_jobs = sorted(results, key=lambda job: job["job_score"], reverse=True)

    print("\n" + "=" * 70)
    print(f"TOP {TOP_K} JOBS MATCHED")
    print("=" * 70)

    for rank, job in enumerate(ranked_jobs[:TOP_K], start=1):
        print(f"\n{rank}. {job['company']} | {job['title']}")
        print(f"   Score: {job['job_score']:.4f}")

if __name__ == "__main__":
    main()