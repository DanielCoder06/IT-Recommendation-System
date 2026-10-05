import json
from pathlib import Path

from src.processing.cv_skill_adapter import extract_annotated_skills
from src.processing.cv_skill_normalizer import normalize_cv_skills


BASE_DIR = Path(__file__).resolve().parents[2]

CV_DIR = (
    BASE_DIR
    / "data"
    / "external"
    / "resumes"
    / "ResumesJsonAnnotated"
)

OUTPUT_PATH = (
    BASE_DIR
    / "data"
    / "cv_normalized_skills.json"
)


def main():
    total_cvs = 0
    total_raw = 0
    total_canonical = 0
    total_unknown = 0

    normalized_dataset = []

    for path in CV_DIR.glob("*.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                cv_data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        raw_skills = extract_annotated_skills(cv_data)
        result = normalize_cv_skills(raw_skills)

        total_cvs += 1
        total_raw += len(raw_skills)
        total_canonical += len(result["canonical_skills"])
        total_unknown += len(result["unknown_skills"])

        normalized_dataset.append(
            {
                "file": path.name,
                "canonical_skills": result["canonical_skills"],
                "unknown_skills": result["unknown_skills"],
            }
        )

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(
            normalized_dataset,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print("=== CV NORMALIZATION SUMMARY ===")
    print(f"CVs: {total_cvs}")
    print(f"Raw skills: {total_raw}")
    print(f"Canonical skills: {total_canonical}")
    print(f"Unknown skills: {total_unknown}")

    if total_raw:
        print(
            f"Canonical rate: "
            f"{total_canonical / total_raw:.2%}"
        )

    print(f"Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()