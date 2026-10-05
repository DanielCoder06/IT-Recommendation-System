from src.processing.cv_skill_adapter import normalize_skill, normalize_skills


def test_normalize_skill():
    assert normalize_skill("python") == "Python"
    assert normalize_skill("python3") == "Python"
    assert normalize_skill("py") == "Python"

    assert normalize_skill("postgres") == "PostgreSQL"
    assert normalize_skill("postgresql") == "PostgreSQL"

    assert normalize_skill("reactjs") == "React"
    assert normalize_skill("k8s") == "Kubernetes"

    assert normalize_skill("unknown skill") is None
    
def test_normalize_skills():
    raw_skills = [
        "python",
        "python3",
        "py",
        "postgres",
        "reactjs",
        "Building",
    ]

    result = normalize_skills(raw_skills)

    assert result == [
        "Python",
        "PostgreSQL",
        "React",
    ]