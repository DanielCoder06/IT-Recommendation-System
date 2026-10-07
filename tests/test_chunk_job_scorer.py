import pytest
from src.matching.chunk_job_scorer import calculate_job_score


def test_calculate_job_score():
    matches = [
        {
            "cv_chunk": "Python backend",
            "jd_chunk": "Python developer",
            "similarity": 0.8,
        },
        {
            "cv_chunk": "SQL database",
            "jd_chunk": "Database engineer",
            "similarity": 0.6,
        },
        {
            "cv_chunk": "Docker deployment",
            "jd_chunk": "Cloud infrastructure",
            "similarity": 0.4,
        },
    ]

    result = calculate_job_score(matches)

    assert "job_score" in result
    assert "quality" in result
    assert "coverage" in result
    assert "chunk_scores" in result

    assert len(result["chunk_scores"]) == 3
    assert result["quality"] == (0.8 + 0.6 + 0.4) / 3
    assert 0.0 <= result["coverage"] <= 1.0
    assert result["job_score"] > 0


def test_empty_matches():
    result = calculate_job_score([])

    assert result["job_score"] == 0.0
    assert result["quality"] == 0.0
    assert result["coverage"] == 0.0
    assert result["chunk_scores"] == []


def test_all_equal_similarities():
    matches = [
        {
            "cv_chunk": "A",
            "jd_chunk": "A",
            "similarity": 0.5,
        },
        {
            "cv_chunk": "B",
            "jd_chunk": "B",
            "similarity": 0.5,
        },
        {
            "cv_chunk": "C",
            "jd_chunk": "C",
            "similarity": 0.5,
        },
    ]

    result = calculate_job_score(matches)

    assert result["quality"] == 0.5
    assert result["coverage"] == 1.0
    assert result["job_score"] == pytest.approx(0.65)