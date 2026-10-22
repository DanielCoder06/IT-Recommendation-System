import numpy as np

from src.processing.jd_parser import TextUnit, split_jd_units


def _split_oversized_unit(
    unit: TextUnit,
    max_words: int,
) -> list[TextUnit]:
    """Chia một đơn vị quá dài thành các phần không vượt max_words, giữ nguyên category."""
    words = unit.text.split()
    
    return [
        TextUnit(
            text=" ".join(words[start:start + max_words]),
            is_heading=unit.is_heading,
            category=unit.category
        )
        for start in range(0, len(words), max_words)
    ]


def _semantic_distances(
    units: list[TextUnit],
    model,
) -> np.ndarray:
    """Tính cosine distance giữa hai đơn vị nội dung liên tiếp."""
    if len(units) < 2:
        return np.empty(0, dtype=float)
    # Mảng tính khoản cách
    distances = np.full(
        len(units) - 1,
        np.nan, # Dùng nan thay vì 0 thì là vector 0
        dtype=float,
        
    )

    content_indices = [
        index
        for index, unit in enumerate(units)
        if not unit.is_heading
    ]

    if len(content_indices) < 2:
        return distances

    embeddings = model.encode(
        [units[index].text for index in content_indices],
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    embeddings = np.asarray(embeddings, dtype=float)

    for position in range(len(content_indices) - 1):
        left = content_indices[position]
        right = content_indices[position + 1]

        if right != left + 1:
            continue

        distances[left] = 1.0 - float(
            np.dot(embeddings[position], embeddings[position + 1])
        )

    return distances


def chunk_jd_text(
    text: str,
    max_words: int = 120,
    overlap_units: int = 0,
    breakpoint_percentile: float = 75.0,
    min_distance: float = 0.15,
    model=None,
) -> list[dict]:
    """
    Hybrid chunking cho Job Description trả về dict chứa text và category.
    """
    if max_words <= 0:
        raise ValueError("max_words phải lớn hơn 0.")
    if overlap_units < 0:
        raise ValueError("overlap_units không được âm.")
    if not 0 <= breakpoint_percentile <= 100:
        raise ValueError("breakpoint_percentile phải nằm trong khoảng 0 đến 100.")
    if min_distance < 0:
        raise ValueError("min_distance không được âm.")

    units = split_jd_units(text)

    if not units:
        return []

    expanded_units: list[TextUnit] = []
    for unit in units:
        if unit.is_heading:
            expanded_units.append(unit)
        else:
            expanded_units.extend(_split_oversized_unit(unit, max_words))
    units = expanded_units

    if model is None:
        from src.models.embedding_model import model as embedding_model
        model = embedding_model

    distances = _semantic_distances(units, model)
    valid_distances = distances[np.isfinite(distances)]

    if len(valid_distances):
        threshold = max(
            float(np.percentile(valid_distances, breakpoint_percentile)),
            min_distance,
        )
    else:
        threshold = float("inf")

    chunks: list[dict] = []
    current_units: list[TextUnit] = []
    current_words = 0

    def save_chunk() -> None:
        if current_units:
            chunk_category = current_units[0].category
            chunks.append({
                "text": " ".join(unit.text for unit in current_units),
                "category": chunk_category
            })

    for index, unit in enumerate(units):
        if unit.is_heading and current_units:
            save_chunk()
            current_units = []
            current_words = 0

        word_count = len(unit.text.split())

        semantic_break = (
            index > 0
            and not unit.is_heading
            and not units[index - 1].is_heading
            and index - 1 < len(distances)
            and np.isfinite(distances[index - 1])
            and distances[index - 1] >= threshold
        )

        size_break = (
            bool(current_units)
            and current_words + word_count > max_words
        )

        category_break = (
            bool(current_units) 
            and unit.category != current_units[0].category
            and not unit.is_heading
        )

        if current_units and (semantic_break or size_break or category_break):
            previous_units = current_units.copy()
            save_chunk()

            candidates = [
                previous
                for previous in previous_units
                if not previous.is_heading and previous.category == unit.category
            ]

            current_units = candidates[-overlap_units:] if overlap_units > 0 else []
            current_words = sum(len(previous.text.split()) for previous in current_units)

            while current_units and current_words + word_count > max_words:
                removed = current_units.pop(0)
                current_words -= len(removed.text.split())

        current_units.append(unit)
        current_words += word_count

    save_chunk()
    return chunks