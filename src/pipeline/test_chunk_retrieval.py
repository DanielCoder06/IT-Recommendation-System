import json
from pathlib import Path

from src.processing.cv_extractor import extract_cv_text
from src.processing.semantic_chunker import chunk_text
from src.matching.chunk_retriever import retrieve_best_matches
from src.matching.chunk_similarity_matcher import match_cv_chunks_to_jd


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

CV_WORDS_PER_CHUNK = 120
JD_WORDS_PER_CHUNK = 120
OVERLAP = 30

TOP_JOBS = 5


def load_jobs():
    with JOBS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def main():
    print("=" * 70)
    print("CV ↔ JD CHUNK RETRIEVAL EXPERIMENT")
    print("=" * 70)

    # --------------------------------------------------
    # 1. CV
    # --------------------------------------------------

    cv_text = extract_cv_text(str(CV_PATH))

    cv_chunks = chunk_text(
        cv_text,
        words_per_chunk=CV_WORDS_PER_CHUNK,
        overlap=OVERLAP,
    )

    print(f"\nCV chunks: {len(cv_chunks)}")

    # --------------------------------------------------
    # 2. Jobs
    # --------------------------------------------------

    jobs = load_jobs()

    print(f"Jobs loaded: {len(jobs)}")

    job_results = []

    # --------------------------------------------------
    # 3. JD → CV + CV → JD retrieval
    # --------------------------------------------------

    for job in jobs[:TOP_JOBS]:

        jd_chunks = chunk_text(
            job["description"],
            words_per_chunk=JD_WORDS_PER_CHUNK,
            overlap=OVERLAP,
        )

        # --------------------------------------------------
        # 3.1 JD → CV
        # --------------------------------------------------

        jd_to_cv_matches = retrieve_best_matches(
            jd_chunks,
            cv_chunks,
        )

        if not jd_to_cv_matches:
            continue

        similarities = [
            match["similarity"]
            for match in jd_to_cv_matches
        ]

        average_similarity = (
            sum(similarities)
            / len(similarities)
        )

        best_similarity = max(similarities)

        # --------------------------------------------------
        # 3.2 CV → JD
        # --------------------------------------------------

        cv_to_jd_matches = match_cv_chunks_to_jd(
            cv_chunks,
            jd_chunks,
        )

        job_results.append(
            {
                "title": job["title"],
                "company": job["company"],
                "chunks": len(jd_chunks),
                "average_similarity": average_similarity,
                "best_similarity": best_similarity,
                "jd_to_cv_matches": jd_to_cv_matches,
                "cv_to_jd_matches": cv_to_jd_matches,
            }
        )

    # --------------------------------------------------
    # 4. Display results
    # --------------------------------------------------

    for job in job_results:

        print("\n" + "=" * 70)

        print(
            f"{job['company']} | "
            f"{job['title']}"
        )

        print(
            f"JD chunks: {job['chunks']}"
        )

        print(
            f"Average similarity: "
            f"{job['average_similarity']:.4f}"
        )

        print(
            f"Best similarity: "
            f"{job['best_similarity']:.4f}"
        )

        # --------------------------------------------------
        # 4.1 JD → CV
        # --------------------------------------------------

        print("\n" + "-" * 70)
        print("JD → CV MATCHES")
        print("-" * 70)

        for match in job["jd_to_cv_matches"]:

            print(
                f"\nJD chunk "
                f"{match['jd_chunk_index'] + 1}"
                f" → CV chunk "
                f"{match['cv_chunk_index'] + 1}"
            )

            print(
                f"Similarity: "
                f"{match['similarity']:.4f}"
            )

            print(
                f"JD: {match['jd_chunk'][:300]}..."
            )

            print(
                f"CV: {match['cv_chunk'][:300]}..."
            )

        # --------------------------------------------------
        # 4.2 CV → JD
        # --------------------------------------------------

        print("\n" + "-" * 70)
        print("CV → JD MATCHES")
        print("-" * 70)

        for index, match in enumerate(
            job["cv_to_jd_matches"],
            start=1,
        ):

            print(
                f"\nCV chunk {index}"
                f" → JD chunk"
            )

            print(
                f"Similarity: "
                f"{match['similarity']:.4f}"
            )

            print(
                f"CV: {match['cv_chunk'][:300]}..."
            )

            print(
                f"JD: {match['jd_chunk'][:300]}..."
            )


if __name__ == "__main__":
    main()