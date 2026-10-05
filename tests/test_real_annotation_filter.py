import json
from pathlib import Path

from src.processing.cv_skill_adapter import extract_annotated_skills
from src.processing.annotation_filter import is_valid_skill_candidate


def test_real_annotation_filter():
    path = Path(
        "data/external/resumes/ResumesJsonAnnotated/cv (1)_annotated.json"
    )

    with open(path, "r", encoding="utf-8") as f:
        cv_data = json.load(f)

    raw_skills = extract_annotated_skills(cv_data)

    kept = []
    rejected = []

    for skill in raw_skills:
        if is_valid_skill_candidate(skill):
            kept.append(skill)
        else:
            rejected.append(skill)

    print("\n=== REAL CV ANNOTATION FILTER ===")
    print(f"Raw skills: {len(raw_skills)}")
    print(f"Kept: {len(kept)}")
    print(f"Rejected: {len(rejected)}")

    print("\n--- KEPT ---")
    print(kept)

    print("\n--- REJECTED ---")
    print(rejected)

    assert len(raw_skills) > 0
    assert len(kept) > 0