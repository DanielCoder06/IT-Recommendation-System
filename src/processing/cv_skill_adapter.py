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