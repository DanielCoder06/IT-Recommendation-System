import json
from pathlib import Path

from src.processing.cv_skill_adapter import (
    extract_annotated_skills,
    normalize_skills,
)


BASE_DIR = Path(__file__).resolve().parents[1]

CV_PATH = (
    BASE_DIR
    / "data"
    / "external"
    / "resumes"
    / "ResumesJsonAnnotated"
    / "cv (1)_annotated.json"
)


def test_real_cv_adapter():
    with open(CV_PATH, "r", encoding="utf-8-sig") as f:
        cv_data = json.load(f)

    raw_skills = extract_annotated_skills(cv_data)
    canonical_skills = normalize_skills(raw_skills)

    print("\nRAW SKILLS:")
    print(raw_skills)

    print("\nCANONICAL SKILLS:")
    print(canonical_skills)

    assert len(raw_skills) > 0
    assert "Python" in canonical_skills
    assert "Java" in canonical_skills