from src.processing.annotation_filter import is_valid_skill_candidate
from src.processing.cv_skill_adapter import normalize_skill


def normalize_cv_skills(
    raw_skills: list[str],
) -> dict[str, list[str]]:
    canonical_skills = []
    unknown_skills = []

    seen_canonical = set()
    seen_unknown = set()

    for skill in raw_skills:
        if not is_valid_skill_candidate(skill):
            continue

        canonical = normalize_skill(skill)

        if canonical is not None:
            if canonical not in seen_canonical:
                seen_canonical.add(canonical)
                canonical_skills.append(canonical)
        else:
            normalized_unknown = skill.strip()

            if normalized_unknown not in seen_unknown:
                seen_unknown.add(normalized_unknown)
                unknown_skills.append(normalized_unknown)

    return {
        "canonical_skills": canonical_skills,
        "unknown_skills": unknown_skills,
    }