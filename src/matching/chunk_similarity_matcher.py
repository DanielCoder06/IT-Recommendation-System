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