import re


def chunk_text(
    text: str,
    words_per_chunk: int = 120,
    overlap: int = 30,
) -> list[str]:
    """
    Chia văn bản thành các chunk dựa trên số lượng từ.

    Ví dụ:
        words_per_chunk=5
        overlap=2

        Chunk 1: W1 W2 W3 W4 W5
        Chunk 2: W4 W5 W6 W7 W8
        Chunk 3: W7 W8 W9 W10 W11
    """

    if not text or not text.strip():
        return []

    if words_per_chunk <= 0:
        raise ValueError(
            "words_per_chunk must be greater than 0"
        )

    if overlap < 0:
        raise ValueError(
            "overlap must be greater than or equal to 0"
        )

    if overlap >= words_per_chunk:
        raise ValueError(
            "overlap must be smaller than words_per_chunk"
        )

    # Chuẩn hóa whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Tách thành từ
    words = text.split()

    if not words:
        return []

    # Khoảng cách giữa hai chunk
    step = words_per_chunk - overlap

    chunks = []

    for start in range(0, len(words), step):

        chunk_words = words[
            start:start + words_per_chunk
        ]

        if not chunk_words:
            break

        chunks.append(
            " ".join(chunk_words)
        )

        # Đã lấy đến cuối văn bản
        if start + words_per_chunk >= len(words):
            break

    return chunks