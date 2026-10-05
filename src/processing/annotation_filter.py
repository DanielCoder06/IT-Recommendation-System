NOISE_TERMS = {
    "building",
    "knowledge",
    "technology",
    "engineer",
    "science",
    "skills",
    "projects",
}


def is_valid_skill_candidate(skill: str) -> bool:
    skill = skill.strip()

    if not skill:
        return False

    if len(skill) <= 1:
        return False

    if skill.lower() in NOISE_TERMS:
        return False

    return True