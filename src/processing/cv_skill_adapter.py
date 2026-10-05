import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DICTIONARY_PATH = BASE_DIR / "config" / "skills_dictionary.json"


with open(DICTIONARY_PATH, "r", encoding="utf-8-sig") as f:
    SKILLS_DICTIONARY = json.load(f)
    
    
def extract_annotated_skills(
    cv_data: dict,
) -> list[str]:
    text = cv_data["text"]
    annotations = cv_data["annotations"]

    skills = []
    
    for start, end, label in annotations:
        if not label.startswith("SKILL: "):
            continue
        
        skill_text = text[start:end].strip()
        
        if skill_text:
            skills.append(skill_text)
    
    return skills

def normalize_skill(skill: str) -> str | None:
    skill = skill.strip().lower()
    
    for canonical, aliases in SKILLS_DICTIONARY.items():
        if skill == canonical:
            return canonical
        
        if skill in [alias.lower() for alias in aliases]:
            return canonical
    
    return None

def normalize_skills(skills: list[str],) -> list[str]:
    normalized = []
    seen = set()
    
    for skill in skills:
        canonical = normalize_skill(skill)
        
        if canonical is None:
            continue
        
        if canonical in seen:
            continue
        
        seen.add(canonical)
        normalized.append(canonical)
        
    return normalized