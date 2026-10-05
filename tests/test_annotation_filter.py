from src.processing.annotation_filter import (
    is_valid_skill_candidate,
)


def test_valid_skill_candidates():
    assert is_valid_skill_candidate("Python")
    assert is_valid_skill_candidate("PySpark")
    assert is_valid_skill_candidate("Computer Vision")
    assert is_valid_skill_candidate("Natural Language Processing")
    assert is_valid_skill_candidate("OCR")


def test_noise_skill_candidates():
    assert not is_valid_skill_candidate("Building")
    assert not is_valid_skill_candidate("Knowledge")
    assert not is_valid_skill_candidate("Technology")
    assert not is_valid_skill_candidate("Engineer")
    assert not is_valid_skill_candidate("Science")
    assert not is_valid_skill_candidate("M")
    assert not is_valid_skill_candidate("PROJECTS")