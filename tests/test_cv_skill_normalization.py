from src.processing.cv_skill_normalizer import normalize_skill
def test_normalize_skill():
    assert normalize_skill("python") == "Python"
    assert normalize_skill("python3") == "Python"
    assert normalize_skill("py") == "Python"

    assert normalize_skill("postgres") == "PostgreSQL"
    assert normalize_skill("postgresql") == "PostgreSQL"

    assert normalize_skill("reactjs") == "React"
    assert normalize_skill("k8s") == "Kubernetes"

    assert normalize_skill("unknown skill") is None