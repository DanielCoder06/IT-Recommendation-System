import re
from pathlib import Path
import yaml

from src.config import BASE_DIR, settings
from src.models.entities.raw_job import RawJob

KEYWORDS_FILE = BASE_DIR / "data" / "keywords.yaml"

def _build_keyword_pattern(kw: str) -> re.Pattern:
    escaped = re.escape(kw.strip().lower())
    left_boundary = r"\b" if re.match(r"^\w", kw.strip()) else r"(?<!\S)"
    right_boundary = r"\b" if re.match(r"\w$", kw.strip()) else r"(?!\S)"
    return re.compile(rf"{left_boundary}{escaped}{right_boundary}", re.IGNORECASE)

def _load_keywords():
    if KEYWORDS_FILE.exists():
        with open(KEYWORDS_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    else:
        data = {}

    title_kws = data.get("it_title_keywords", [])
    desc_kws = data.get("it_description_keywords", [])
    non_it_kws = data.get("non_it_title_keywords", [])

    return (
        [_build_keyword_pattern(k) for k in title_kws],
        [_build_keyword_pattern(k) for k in desc_kws],
        [_build_keyword_pattern(k) for k in non_it_kws]
    )

IT_TITLE_PATTERNS, IT_DESC_PATTERNS, NON_IT_TITLE_PATTERNS = _load_keywords()

def calculate_it_score(job: RawJob) -> int:
    title = job.title or ""
    description = job.description or ""
    score = 0

    for pat in IT_TITLE_PATTERNS:
        if pat.search(title): score += 3
    for pat in IT_DESC_PATTERNS:
        if pat.search(description): score += 1
    for pat in NON_IT_TITLE_PATTERNS:
        if pat.search(title): score -= 5

    return score

# Nhận diện senior
SENIOR_TITLE_PATTERN = re.compile(
    r"\b(senior|sr\.?|lead|tech lead|team lead|principal|staff|architect|head of|director|vp|chief|manager|expert)\b",
    re.IGNORECASE,
)

SENIOR_EXP_PATTERN = re.compile(
    r"(?:\b(senior|[5-9]\s*years?|1\d\s*years?)\b|5\+)",
    re.IGNORECASE,
)

def is_senior_job(title: str, experience: str = "") -> bool:
    """Kiểm tra xem công việc có thuộc cấp độ Senior hoặc tương đương hay không."""
    if SENIOR_TITLE_PATTERN.search(title or ""):
        return True
    if experience and SENIOR_EXP_PATTERN.search(experience):
        return True
    return False

def is_it_job(job: RawJob, threshold: int = settings.IT_SCORE_THRESHOLD) -> bool:
    return calculate_it_score(job) >= threshold

def filter_it_jobs(jobs: list[RawJob], exclude_senior: bool = True) -> list[RawJob]:
    """Giữ lại các job IT, có thể loại bỏ các vị trí Senior."""
    filtered = [job for job in jobs if is_it_job(job)]
    
    if exclude_senior:
        filtered = [
            job for job in filtered 
            if not is_senior_job(job.title, getattr(job, "experience", "") or "")
        ]
        
    return filtered