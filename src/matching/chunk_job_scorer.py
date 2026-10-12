import numpy as np


def calculate_job_score(
    matches: list[dict],
    top_k: int = 3,
) -> dict:
    """
    Tính điểm phù hợp giữa JD và CV.
    
    Với mỗi JD requirement/responsibility chunk được match với CV chunk tốt nhất,
    lấy trung bình top_k similarities cao nhất để đánh giá mức độ đáp ứng các yêu cầu cốt lõi.
    """
    if not matches:
        return {
            "job_score": 0.0,
            "quality": 0.0,
            "chunk_scores": [],
        }

    similarities = sorted(
        [match["similarity"] for match in matches],
        reverse=True,
    )

    actual_k = min(len(similarities), top_k) if top_k > 0 else len(similarities)
    top_k_similarities = similarities[:actual_k]

    job_score = float(np.mean(top_k_similarities)) if top_k_similarities else 0.0
    quality = float(np.mean(similarities))

    return {
        "job_score": job_score,
        "quality": quality,
        "chunk_scores": similarities,
    }