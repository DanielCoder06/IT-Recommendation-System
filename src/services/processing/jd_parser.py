import re
from dataclasses import dataclass

from src.utils.text_cleaner import clean_job_description
from src.services.processing.jd_classifier import JDCategory, classify_heading, EXACT_KEYWORDS

@dataclass
class TextUnit:
    text: str
    is_heading: bool = False
    category: str = JDCategory.GENERAL.value
    
# Các heading tiếng Anh phổ biến cần tách dòng khi đi kèm dấu hai chấm ':'
_INLINE_HEADINGS = (
    "Requirements", "Key Requirements", "Job Requirements", "Minimum Requirements",
    "Basic Qualifications", "Preferred Qualifications", "Qualifications",
    "What you bring", "What you need", "Skills and Experience", "Required Skills",
    "Desired Skills", "A little about you", "Who you are", "Profile",
    "Responsibilities", "Key Responsibilities", "Your Responsibilities",
    "What you will do", "What you'll do", "Your Mission", "The Role",
    "About the Role", "Role Overview", "Position Summary", "Day to Day",
    "Your Tasks", "Tasks", "What we offer", "Why join us", "Benefits",
    "Perks", "Total Rewards", "Compensation", "About us", "About the company",
    "About our company", "Who we are", "How we work", "Our Tech Stack",
    "Tech Stack", "DE&I Statement", "Diversity and Inclusion",
)

_INLINE_HEADING_PATTERN = re.compile(
    r"(?i)(?<!\S)(" + "|".join(re.escape(h) for h in _INLINE_HEADINGS) + r")\s*:"
)

_BULLET_PATTERN = re.compile(
    r"^\s*(?:[-*•▪◦‣]|\d+[.)])\s+"
)

def _is_heading(line: str) -> bool:
    line = line.strip()
    words = line.split()

    if not line or len(words) > 12:
        return False
    if line.startswith("#"):
        return True

    letters = [char for char in line if char.isalpha()]
    if letters and all(char.isupper() for char in letters):
        return True

    if line.endswith((":", "?")) and len(words) <= 8:
        return True

    if len(words) <= 6 and not line.endswith((".", ",", ";")):
        if classify_heading(line) != JDCategory.GENERAL:
            return True
        if line.istitle():
            return True

    return False

def _split_inline_headings(text: str) -> str:
    return _INLINE_HEADING_PATTERN.sub(lambda match: "\n" + match.group(1) + ":\n", text)

_ALL_UPPER_HEADINGS = tuple(
    sorted({k.upper() for keywords in EXACT_KEYWORDS.values() for k in keywords}, key=len, reverse=True)
)
_UPPER_HEADING_ALT = "|".join(re.escape(h) for h in _ALL_UPPER_HEADINGS)

_UPPER_HEADING_AFTER_PUNCT = re.compile(r'([.!?]\s+)(' + _UPPER_HEADING_ALT + r')(\s+)')
_UPPER_HEADING_LINE_START = re.compile(r'(?m)^(' + _UPPER_HEADING_ALT + r')(\s+)(?=[a-zA-Z0-9])')

def _split_known_uppercase_headings(text: str) -> str:
    text = _UPPER_HEADING_AFTER_PUNCT.sub(r'\1\n\n\2\n\n', text)
    text = _UPPER_HEADING_LINE_START.sub(r'\1\n\n', text)
    return text

def _split_sentences(text: str) -> list[str]:
    return [
        sentence.strip()
        for sentence in re.split(r'(?<=[.!?])\s+(?=[A-Z0-9“"\'])', text.strip())
        if sentence.strip()
    ]

def split_jd_units(text: str) -> list[TextUnit]:
    text = clean_job_description(text)

    if not text:
        return []

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r'\b([A-Z]{2,20})\s*\n\s*(?=[A-Z]{2,20}\b)', r'\1 ', text)
    text = _split_inline_headings(text)
    text = _split_known_uppercase_headings(text)
    text = re.sub(r"(?<=[a-z.!?])\s+(?=[A-Z][A-Z0-9 ]{4,35}(?:\?|:)?(?:\n|$))", "\n\n", text)

    units: list[TextUnit] = []
    current_category = JDCategory.GENERAL.value

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if _is_heading(line):
            current_category = classify_heading(line).value
            units.append(TextUnit(line, is_heading=True, category=current_category))
            continue

        bullet = bool(_BULLET_PATTERN.match(line))
        line = _BULLET_PATTERN.sub("", line).strip()

        if not line:
            continue

        if units and units[-1].is_heading:
            previous_heading = units[-1].text.rstrip(":?").strip()
            duplicate_pattern = re.compile(r"^" + re.escape(previous_heading) + r"\s*:\s*", flags=re.IGNORECASE)
            line = duplicate_pattern.sub("", line, count=1).strip()

        if not line:
            continue

        parts = [line] if bullet else _split_sentences(line)

        for part in parts:
            units.append(TextUnit(part, category=current_category))

    return units