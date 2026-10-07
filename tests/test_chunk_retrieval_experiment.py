import json
from pathlib import Path

from src.processing.cv_extractor import extract_cv_text
from src.processing.semantic_chunker import chunk_text

from src.matching.chunk_similarity_matcher import (
    match_top_k_chunks,
)

from src.matching.chunk_job_scorer import (
    calculate_job_score,
)


BASE_DIR = Path(__file__).resolve().parents[1]

CV_PATH = (
    BASE_DIR
    / "data"
    / "external"
    / "resumes"
    / "ResumesPDF"
    / "sample_cv.pdf"
)

JOBS_PATH = (
    BASE_DIR
    / "data"
    / "filtered_it_jobs.json"
)

CHUNK_SIZE = 120
OVERLAP = 30
TOP_K = 3
TOP_N = 10


def load_jobs() -> list[dict]:
    with JOBS_PATH.open(
        "r",
        encoding="utf-8",
    ) as f:
        return json.load(f)


def main():
    print("=" * 70)
    print("TOP-K CHUNK RETRIEVAL EXPERIMENT")
    print("=" * 70)

    # --------------------------------------------------
    # 1. Extract CV
    # --------------------------------------------------

    cv_text = extract_cv_text(
        str(CV_PATH)
    )

    cv_chunks = chunk_text(
        cv_text,
        words_per_chunk=CHUNK_SIZE,
        overlap=OVERLAP,
    )

    print(f"\nCV chunks: {len(cv_chunks)}")

    # --------------------------------------------------
    # 2. Load jobs
    # --------------------------------------------------

    jobs = load_jobs()

    print(f"Jobs loaded: {len(jobs)}")

    # --------------------------------------------------
    # 3. Process every job
    # --------------------------------------------------

    ranked_results = []

    for index, job in enumerate(
        jobs,
        start=1,
    ):
        description = job.get(
            "description",
            "",
        )

        jd_chunks = chunk_text(
            description,
            words_per_chunk=CHUNK_SIZE,
            overlap=OVERLAP,
        )

        if not jd_chunks:
            continue

        # --------------------------------------------------
        # Top-K retrieval
        # --------------------------------------------------

        chunk_matches = match_top_k_chunks(
            jd_chunks,
            cv_chunks,
            top_k=TOP_K,
        )

        # --------------------------------------------------
        # Job scoring
        # --------------------------------------------------

        score = calculate_job_score(
            chunk_matches
        )

        ranked_results.append(
            {
                "job_id": index,
                "title": job.get("title"),
                "company": job.get("company"),
                "location": job.get("location"),
                "url": job.get("url"),
                "job_score": score["job_score"],
                "coverage": score["coverage"],
                "chunk_scores": score["chunk_scores"],
                "chunk_matches": chunk_matches,
            }
        )

    # --------------------------------------------------
    # 4. Rank jobs
    # --------------------------------------------------

    ranked_results.sort(
        key=lambda job: job["job_score"],
        reverse=True,
    )

    # --------------------------------------------------
    # 5. Display Top N
    # --------------------------------------------------

    print("\n" + "=" * 70)
    print(
        f"TOP {TOP_N} JOB RECOMMENDATIONS"
    )
    print("=" * 70)

    for rank, job in enumerate(
        ranked_results[:TOP_N],
        start=1,
    ):
        print(
            f"\n{rank}. "
            f"{job['company']} | "
            f"{job['title']}"
        )

        print(
            f"   Job Score : "
            f"{job['job_score']:.4f}"
        )

        print(
            f"   Coverage  : "
            f"{job['coverage']:.2%}"
        )

    # --------------------------------------------------
    # 6. Detailed Top 3
    # --------------------------------------------------

    print("\n" + "=" * 70)
    print("TOP 3 DETAILED MATCHES")
    print("=" * 70)

    for rank, job in enumerate(
        ranked_results[:3],
        start=1,
    ):
        print("\n" + "-" * 70)

        print(
            f"{rank}. "
            f"{job['company']} | "
            f"{job['title']}"
        )

        print(
            f"Job Score: "
            f"{job['job_score']:.4f}"
        )

        print(
            f"Coverage: "
            f"{job['coverage']:.2%}"
        )

        for chunk_index, chunk_result in enumerate(
            job["chunk_matches"],
            start=1,
        ):
            print(
                f"\nJD Chunk {chunk_index}"
            )

            matches = chunk_result["matches"]

            for match_rank, match in enumerate(
                matches,
                start=1,
            ):
                print(
                    f"  Top {match_rank}: "
                    f"{match['similarity']:.4f}"
                )

                print(
                    f"      CV: "
                    f"{match['cv_chunk'][:250]}..."
                )


if __name__ == "__main__":
    main()