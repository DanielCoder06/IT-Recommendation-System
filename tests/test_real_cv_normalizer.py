import json
from pathlib import Path

from src.processing.cv_skill_adapter import extract_annotated_skills
from src.processing.cv_skill_normalizer import normalize_cv_skills


def test_real_cv_normalizer():
    path = Path(
        "data/external/resumes/ResumesJsonAnnotated/cv (1)_annotated.json"
    )

    with open(path, "r", encoding="utf-8") as f:
        cv_data = json.load(f)

    raw_skills = extract_annotated_skills(cv_data)

    result = normalize_cv_skills(raw_skills)

    print("\n=== REAL CV NORMALIZATION ===")
    print(f"Raw skills: {len(raw_skills)}")

    print("\nCanonical:")
    print(result["canonical_skills"])

    print("\nUnknown:")
    print(result["unknown_skills"])

    assert len(result["canonical_skills"]) > 0