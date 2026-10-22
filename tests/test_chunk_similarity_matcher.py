from src.matching.chunk_similarity_matcher import (
    encode_chunks,
    match_chunks,
)


def test_encode_chunks():
    chunks = [
        "Python backend development",
        "SQL database experience",
    ]

    vectors = encode_chunks(chunks)

    assert len(vectors) == 2
    assert vectors.shape[0] == 2


def test_match_chunks():
    jd_chunks = [
        "Experience with Python backend development",
        "Experience with SQL databases",
    ]

    cv_chunks = [
        "Developed backend applications using Python",
        "Built responsive frontend using React",
        "Worked with SQL and relational databases",
    ]

    results = match_chunks(
        jd_chunks,
        cv_chunks,
    )

    assert len(results) == 2

    for result in results:
        assert "jd_chunk" in result
        assert "cv_chunk" in result
        assert "similarity" in result

    assert results[0]["similarity"] >= 0
    assert results[1]["similarity"] >= 0
