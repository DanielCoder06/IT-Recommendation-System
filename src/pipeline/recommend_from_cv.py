import json
from pathlib import Path

from src.processing.cv_extractor import extract_cv_text
from src.processing.semantic_chunker import chunk_text
from src.matching.chunk_similarity_matcher import match_cv_chunks_to_jd
from src.matching.chunk_job_scorer import calculate_job_score


BASE_DIR = Path(__file__).resolve().parents[2]

CV_PATH = (
    BASE_DIR
    / "data"
    / "external"
    / "resumes"
    / "ResumesPDF"
    / "sample_cv.pdf"
)

JOBS_PATH = BASE_DIR / "data" / "filtered_it_jobs.json"

TOP_K = 10

CV_WORDS_PER_CHUNK = 120
JD_WORDS_PER_CHUNK = 120
CHUNK_OVERLAP = 30


def load_jobs() -> list[dict]:
    with JOBS_PATH.open(
        "r",
        encoding="utf-8",
    ) as f:
        return json.load(f)


def main():
    print("=" * 70)
    print("CV → JOB CHUNK-BASED RECOMMENDATION")
    print("=" * 70)

    # --------------------------------------------------
    # 1. Extract CV text
    # --------------------------------------------------

    cv_text = extract_cv_text(
        str(CV_PATH)
    )

    print(
        f"\nCV characters: {len(cv_text)}"
    )

    # --------------------------------------------------
    # 2. Chunk CV
    # --------------------------------------------------

    cv_chunks = chunk_text(
        cv_text,
        words_per_chunk=CV_WORDS_PER_CHUNK,
        overlap=CHUNK_OVERLAP,
    )

    print(
        f"CV chunks: {len(cv_chunks)}"
    )

    if not cv_chunks:
        print("CV không có dữ liệu để matching.")
        return

    # --------------------------------------------------
    # 3. Load jobs
    # --------------------------------------------------

    jobs = load_jobs()

    print(
        f"Jobs loaded: {len(jobs)}"
    )

    # --------------------------------------------------
    # 4. Match CV chunks → JD chunks
    # --------------------------------------------------

    results = []

    for index, job in enumerate(
        jobs,
        start=1,
    ):
        jd_text = job.get(
            "description",
            "",
        )

        jd_chunks = chunk_text(
            jd_text,
            words_per_chunk=JD_WORDS_PER_CHUNK,
            overlap=CHUNK_OVERLAP,
        )

        if not jd_chunks:
            continue

        chunk_matches = match_cv_chunks_to_jd(
            cv_chunks,
            jd_chunks,
        )

        score = calculate_job_score(
            chunk_matches
        )

        results.append(
            {
                "job_id": index,
                "title": job["title"],
                "company": job["company"],
                "location": job.get("location"),
                "url": job.get("url"),
                "jd_chunks": jd_chunks,
                "matches": chunk_matches,
                "job_score": score["job_score"],
                "coverage": score["coverage"],
                "chunk_scores": score["chunk_scores"],
            }
        )

    # --------------------------------------------------
    # 5. Rank jobs
    # --------------------------------------------------

    ranked_jobs = sorted(
        results,
        key=lambda job: job["job_score"],
        reverse=True,
    )

    # --------------------------------------------------
    # 6. Display
    # --------------------------------------------------

    print("\n" + "=" * 70)
    print(f"TOP {TOP_K} JOBS")
    print("=" * 70)

    for rank, job in enumerate(
        ranked_jobs[:TOP_K],
        start=1,
    ):
        print(
            f"\n{rank}. "
            f"{job['company']} | "
            f"{job['title']}"
        )

        print(
            f"Score: {job['job_score']:.4f} | "
            f"Coverage: {job['coverage']:.2%}"
        )

        print("\nCV → JD chunk matches:")

        for index, match in enumerate(
            job["matches"],
            start=1,
        ):
            print(
                f"\n  CV chunk {index}"
                f" → JD chunk"
            )

            print(
                f"  Similarity: "
                f"{match['similarity']:.4f}"
            )

            print(
                f"  CV: {match['cv_chunk']}"
            )

            print(
                f"  JD: {match['jd_chunk']}"
            )


if __name__ == "__main__":
    main()