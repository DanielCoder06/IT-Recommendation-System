from src.processing.cv_skill_normalizer import normalize_cv_skills


def test_normalize_cv_skills():
    raw_skills = [
        "python",
        "python3",
        "py",
        "postgres",
        "reactjs",
        "PySpark",
        "Kubeflow",
        "Building",
        "Knowledge",
        "M",
    ]

    result = normalize_cv_skills(raw_skills)

    assert result["canonical_skills"] == [
        "Python",
        "PostgreSQL",
        "React",
        "PySpark",
        "Kubeflow",
    ]

    assert result["unknown_skills"] == []