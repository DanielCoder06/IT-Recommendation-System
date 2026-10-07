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