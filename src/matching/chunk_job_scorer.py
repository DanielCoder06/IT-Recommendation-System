import numpy as np


def calculate_job_score(
    matches: list[dict],
) -> dict:
    """
    Tính điểm phù hợp giữa CV và một JD.

    Mỗi CV chunk được ghép với JD chunk
    có similarity cao nhất.

    Quality:
        Similarity trung bình của các CV chunks.

    Coverage:
        Tỷ lệ CV chunks có similarity
        cao hơn mức similarity trung bình của chính job.

    Job score:
        Kết hợp Quality và Coverage.
    """

    if not matches:
        return {
            "job_score": 0.0,
            "quality": 0.0,
            "coverage": 0.0,
            "chunk_scores": [],
        }

    similarities = [
        match["similarity"]
        for match in matches
    ]

    quality = float(
        np.mean(similarities)
    )

    # Dùng median làm mốc tương đối,
    # chưa áp threshold cố định.
    reference = float(
        np.median(similarities)
    )

    matched_chunks = [
        similarity
        for similarity in similarities
        if similarity >= reference
    ]

    coverage = (
        len(matched_chunks)
        / len(similarities)
    )

    # Cân bằng chất lượng và độ phủ.
    job_score = (
        0.7 * quality
        + 0.3 * coverage
    )

    return {
        "job_score": job_score,
        "quality": quality,
        "coverage": coverage,
        "chunk_scores": similarities,
    }