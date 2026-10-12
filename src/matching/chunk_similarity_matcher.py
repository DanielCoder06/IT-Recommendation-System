import numpy as np

from src.models.embedding_model import model


def encode_chunks(chunks: list[str]) -> np.ndarray:
    """
    Encode danh sách chunks thành các vector embedding.

    normalize_embeddings=True giúp cosine similarity
    có thể tính bằng tích vô hướng.
    """

    if not chunks:
        return np.empty((0, 0))

    return model.encode(
        chunks,
        normalize_embeddings=True,
    )


def match_chunks(
    query_chunks: list[str],
    candidate_chunks: list[str],
    candidate_embeddings: np.ndarray | None = None,
) -> list[dict]:
    """
    Tìm candidate chunk có similarity cao nhất cho từng query chunk.
    Hỗ trợ truyền trước candidate_embeddings để tối ưu hiệu năng (tránh re-encode lặp lại).
    """

    if not query_chunks or not candidate_chunks:
        return []

    query_embeddings = encode_chunks(query_chunks)
    if candidate_embeddings is None:
        candidate_embeddings = encode_chunks(candidate_chunks)

    results = []

    for index, query_embedding in enumerate(query_embeddings):

        similarities = np.dot(
            candidate_embeddings,
            query_embedding,
        )

        best_index = int(np.argmax(similarities))
        best_similarity = float(
            similarities[best_index]
        )
        results.append(
            {
                "jd_chunk": query_chunks[index],
                "cv_chunk": candidate_chunks[best_index],
                "similarity": best_similarity,
            }
        )

    return results


def match_top_k_chunks(
    query_chunks: list[str],
    candidate_chunks: list[str],
    top_k: int = 3,
) -> list[dict]:
    """
    Tìm Top-K CV chunks có similarity cao nhất
    cho từng JD chunk.
    """

    if not query_chunks or not candidate_chunks:
        return []

    if top_k <= 0:
        raise ValueError(
            "top_k must be greater than 0"
        )

    query_embeddings = encode_chunks(
        query_chunks
    )

    candidate_embeddings = encode_chunks(
        candidate_chunks
    )

    results = []

    actual_top_k = min(
        top_k,
        len(candidate_chunks),
    )

    for index, query_embedding in enumerate(
        query_embeddings
    ):

        similarities = np.dot(
            candidate_embeddings,
            query_embedding,
        )

        top_indices = np.argsort(
            similarities
        )[::-1][:actual_top_k]

        matches = []

        for candidate_index in top_indices:

            matches.append(
                {
                    "cv_chunk": candidate_chunks[
                        int(candidate_index)
                    ],
                    "similarity": float(
                        similarities[candidate_index]
                    ),
                }
            )

        results.append(
            {
                "jd_chunk": query_chunks[index],
                "matches": matches,
            }
        )

    return results

def match_cv_chunks_to_jd(
    cv_chunks: list[str],
    jd_chunks: list[str],
) -> list[dict]:
    """
    Với mỗi CV chunk, tìm JD chunk có similarity cao nhất.
    """

    if not cv_chunks or not jd_chunks:
        return []

    cv_embeddings = encode_chunks(cv_chunks)
    jd_embeddings = encode_chunks(jd_chunks)

    results = []

    for index, cv_embedding in enumerate(cv_embeddings):

        similarities = np.dot(
            jd_embeddings,
            cv_embedding,
        )

        best_index = int(
            np.argmax(similarities)
        )

        best_similarity = float(
            similarities[best_index]
        )

        results.append(
            {
                "cv_chunk": cv_chunks[index],
                "jd_chunk": jd_chunks[best_index],
                "similarity": best_similarity,
            }
        )

    return results