from src.models.embedding_model import model


def embed_chunks(chunks: list[str]):
    """
    Encode danh sách chunks thành normalized embeddings.
    """
    if not chunks:
        return []

    return model.encode(
        chunks,
        normalize_embeddings=True,
    )


def retrieve_best_matches(
    jd_chunks: list[str],
    cv_chunks: list[str],
):
    """
    Với mỗi JD chunk, tìm CV chunk có cosine similarity cao nhất.

    Vì embeddings đã normalize nên dot product
    chính là cosine similarity.
    """

    if not jd_chunks or not cv_chunks:
        return []

    jd_embeddings = embed_chunks(jd_chunks)
    cv_embeddings = embed_chunks(cv_chunks)

    results = []

    for jd_index, jd_vector in enumerate(jd_embeddings):
        similarities = cv_embeddings @ jd_vector

        best_cv_index = similarities.argmax()
        best_similarity = similarities[best_cv_index]

        results.append(
            {
                "jd_chunk_index": jd_index,
                "cv_chunk_index": int(best_cv_index),
                "similarity": float(best_similarity),
                "jd_chunk": jd_chunks[jd_index],
                "cv_chunk": cv_chunks[best_cv_index],
            }
        )

    return results