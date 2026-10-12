import re
from dataclasses import dataclass

from src.processing.text_cleaner import clean_job_description
from src.processing.jd_classifier import JDCategory, classify_heading, EXACT_KEYWORDS


@dataclass
class TextUnit:
    text: str
    is_heading: bool = False
    category: str = JDCategory.GENERAL.value


_INLINE_HEADINGS = (
    "How we work at Aircall",
    "Your mission @ Aircall",
    "A little about you",
    "Our Tech Stack",
    "Why join us",
    "DE&I Statement",
)

_INLINE_HEADING_PATTERN = re.compile(
    r"(?i)(?<!\S)("
    + "|".join(re.escape(h) for h in _INLINE_HEADINGS)
    + r")\s*:"
)

_BULLET_PATTERN = re.compile(
    r"^\s*(?:[-*•▪◦‣]|\d+[.)])\s+"
)


def _is_heading(line: str) -> bool:
    """Nhận diện heading dựa trên hình thức trình bày."""
    line = line.strip()

    if not line or len(line.split()) > 12:
        return False

    if line.startswith("#"):
        return True

    letters = [char for char in line if char.isalpha()]
    if letters and all(char.isupper() for char in letters):
        return True

    if line.endswith((":", "?")) and len(line.split()) <= 8:
        return True

    if len(line.split()) <= 6 and not line.endswith((".", ",", ";")):
        if classify_heading(line) != JDCategory.GENERAL:
            return True
        if line.istitle():
            return True

    return False


def _split_inline_headings(text: str) -> str:
    """Tách heading tiếng Anh đã biết khi nó đứng cùng dòng với nội dung."""
    return _INLINE_HEADING_PATTERN.sub(
        lambda match: "\n" + match.group(1) + ":\n",
        text,
    )


def _split_known_uppercase_headings(text: str) -> str:
    """Tách các heading IN HOA có trong từ khóa nếu bị dính vào câu."""
    for keywords in EXACT_KEYWORDS.values():
        for k in keywords:
            h = k.upper()
            # Pattern 1: Dính sau dấu chấm (VD: "English. ABOUT US FELFEL is").
            text = re.sub(
                r'([.!?]\s+)(' + re.escape(h) + r')(\s+)', 
                r'\1\n\n\2\n\n', 
                text
            )
            # Pattern 2: Đứng đầu dòng nhưng bị dính chữ (VD: "\nABOUT US FELFEL is")
            text = re.sub(
                r'(?m)^(' + re.escape(h) + r')(\s+)(?=[a-zA-Z0-9])', 
                r'\1\n\n', 
                text
            )
    return text


def _split_sentences(text: str) -> list[str]:
    """Chia văn xuôi thành câu, giữ lại dấu câu kết thúc."""
    return [
        sentence.strip()
        for sentence in re.split(
            r'(?<=[.!?])\s+(?=[A-Z0-9“"\'])',
            text.strip(),
        )
        if sentence.strip()
    ]


def split_jd_units(text: str) -> list[TextUnit]:
    """Làm sạch JD và tách thành heading, bullet và câu kèm theo nhãn phân loại."""
    text = clean_job_description(text)

    if not text:
        return []

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    
    # Nối các từ in hoa bị rớt dòng
    text = re.sub(r'\b([A-Z]{2,20})\s*\n\s*(?=[A-Z]{2,20}\b)', r'\1 ', text)
    
    text = _split_inline_headings(text)
    
    # [CẬP NHẬT MỚI]: Tách các heading in hoa phổ biến bị dính liền vào câu
    text = _split_known_uppercase_headings(text)

    # Tách heading viết hoa nếu nó bị dính sát vào cuối câu trước đó
    text = re.sub(
        r"(?<=[a-z.!?])\s+(?=[A-Z][A-Z0-9 ]{4,35}(?:\?|:)?(?:\n|$))",
        "\n\n",
        text,
    )

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
            duplicate_pattern = re.compile(
                r"^" + re.escape(previous_heading) + r"\s*:\s*",
                flags=re.IGNORECASE,
            )
            line = duplicate_pattern.sub("", line, count=1).strip()

        if not line:
            continue

        parts = [line] if bullet else _split_sentences(line)

        for part in parts:
            units.append(TextUnit(part, category=current_category))

    return units