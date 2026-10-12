import pytest

from src.processing.semantic_chunker import chunk_text


def test_empty_text():
    assert chunk_text("") == []


def test_single_chunk():
    text = (
        "Python is required. "
        "SQL is required. "
        "Git is required."
    )

    chunks = chunk_text(
        text,
        words_per_chunk=9,
        overlap=2,
    )

    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_overlap():
    text = (
        "one two three four five "
        "six seven eight"
    )

    chunks = chunk_text(
        text,
        words_per_chunk=5,
        overlap=2,
    )

    assert chunks == [
        "one two three four five",
        "four five six seven eight",
    ]


def test_invalid_chunk_size():
    with pytest.raises(ValueError):
        chunk_text(
            "Python is required.",
            words_per_chunk=0,
        )


def test_invalid_overlap():
    with pytest.raises(ValueError):
        chunk_text(
            "Python is required.",
            words_per_chunk=3,
            overlap=3,
        )


def test_split_text_into_units_bullets():
    from src.processing.semantic_chunker import split_text_into_units

    text = """
    • Led a team of four engineers to build a resume screening engine.
    • Fine-tuned transformer models for NER on 200k documents.
    • Designed a vector search service with FAISS and FastAPI.
    """
    units = split_text_into_units(text)
    assert len(units) == 3
    assert "Led a team" in units[0]
    assert "Fine-tuned" in units[1]
    assert "Designed a vector" in units[2]


def test_semantic_chunker_basic():
    import numpy as np
    from src.processing.semantic_chunker import SemanticChunker

    # Mock embedding function: vector based on keywords
    def mock_embed(texts):
        vectors = []
        for t in texts:
            if "python" in t.lower() or "backend" in t.lower():
                vectors.append([1.0, 0.0])
            else:
                vectors.append([0.0, 1.0])
        return np.array(vectors)

    chunker = SemanticChunker(
        embed_fn=mock_embed,
        breakpoint_percentile=50.0,
        min_distance=0.1,
        min_chars=10,
        max_chars=120,
    )

    text = """
    • Senior Python backend developer with FastAPI experience.
    • Architected microservices and PostgreSQL databases.
    • Finance and accounting ledger reconciliation specialist.
    • Monthly financial audit reports and tax calculations.
    """
    chunks = chunker.chunk_text(text, header="EXPERIENCE")
    assert len(chunks) >= 2
    assert all("[EXPERIENCE]" in c for c in chunks)