from src.processing.cv_skill_adapter import extract_annotated_skills


def test_extract_annotated_skills():
    cv_data = {
        "text": "Python Java Machine Learning",
        "annotations": [
            [0, 6, "SKILL: Python"],
            [7, 11, "SKILL: Java"],
            [12, 28, "SKILL: Machine Learning"],
            [0, 6, "OTHER: Something"],
        ],
    }

    result = extract_annotated_skills(cv_data)

    assert result == [
        "Python",
        "Java",
        "Machine Learning",
    ]