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

from src.matching.chunk_similarity_matcher import (
    match_top_k_chunks,
)


def test_match_top_k_chunks():
    query_chunks = [
        "Python backend development",
    ]

    candidate_chunks = [
        "Python backend development with FastAPI",
        "Java Spring Boot backend development",
        "HTML CSS frontend development",
        "Data analysis with SQL",
    ]

    results = match_top_k_chunks(
        query_chunks,
        candidate_chunks,
        top_k=3,
    )

    assert len(results) == 1

    matches = results[0]["matches"]

    assert len(matches) == 3

    assert (
        matches[0]["similarity"]
        >= matches[1]["similarity"]
    )

    assert (
        matches[1]["similarity"]
        >= matches[2]["similarity"]
    )
    
def test_match_top_k_larger_than_candidates():
    query_chunks = [
        "Python backend development",
    ]

    candidate_chunks = [
        "Python backend development",
        "Java backend development",
    ]

    results = match_top_k_chunks(
        query_chunks,
        candidate_chunks,
        top_k=10,
    )

    assert len(results[0]["matches"]) == 2