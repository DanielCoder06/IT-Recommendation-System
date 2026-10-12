from dataclasses import dataclass
import re
from pathlib import Path

import pymupdf

from src.processing.cv_text_extractor import (
    _extract_blocks,
    _find_column_boundary,
    _order_blocks,
)

@dataclass
class Line:
    """Một dòng văn bản trích xuất từ CV."""
    text: str
    size: float
    bold: bool
    page: int


@dataclass
class Section:
    """Một mục trong CV."""
    name: str
    title: str
    lines: list[Line]



SECTION_PATTERNS = {
    "SUMMARY": [
        r"SUMMARY",
        r"PROFESSIONAL SUMMARY",
        r"EXECUTIVE SUMMARY",
        r"PROFILE",
        r"PROFESSIONAL PROFILE",
        r"PERSONAL PROFILE",
        r"CAREER OBJECTIVE",
        r"CAREER GOAL",
        r"CAREER GOALS",
        r"OBJECTIVE",
        r"ABOUT ME",
        r"ABOUT MYSELF",
    ],
    "CONTACT": [
        r"CONTACT",
        r"CONTACT INFORMATION",
        r"CONTACT DETAILS",
        r"PERSONAL DETAILS",
        r"PERSONAL INFORMATION",
    ],
    "EXPERIENCE": [
        r"EXPERIENCE",
        r"WORK EXPERIENCE",
        r"PROFESSIONAL EXPERIENCE",
        r"EMPLOYMENT HISTORY",
        r"WORK HISTORY",
        r"CAREER HISTORY",
        r"INTERNSHIP EXPERIENCE",
        r"WORK AND EXPERIENCE",
    ],
    "EDUCATION": [
        r"EDUCATION",
        r"EDUCATIONAL BACKGROUND",
        r"ACADEMIC BACKGROUND",
        r"ACADEMIC QUALIFICATIONS",
    ],
    "SKILLS": [
        r"SKILLS",
        r"TECHNICAL SKILLS",
        r"CORE SKILLS",
        r"KEY SKILLS",
        r"TECHNICAL EXPERTISE",
        r"TECHNOLOGIES",
        r"TECHNOLOGY STACK",
        r"TECH STACK",
        r"PROGRAMMING SKILLS",
        r"IT SKILLS",
    ],
    "PROJECTS": [
        r"PROJECT",
        r"PROJECTS",
        r"PERSONAL PROJECT",
        r"PERSONAL PROJECTS",
        r"ACADEMIC PROJECT",
        r"ACADEMIC PROJECTS",
        r"SELECTED PROJECTS",
        r"KEY PROJECTS",
        r"PROJECT EXPERIENCE",
    ],
    "CERTIFICATIONS": [
        r"CERTIFICATION",
        r"CERTIFICATIONS",
        r"CERTIFICATE",
        r"CERTIFICATES",
        r"LICENSES AND CERTIFICATIONS",
    ],
    "AWARDS": [
        r"AWARD",
        r"AWARDS",
        r"ACHIEVEMENT",
        r"ACHIEVEMENTS",
        r"HONORS AND AWARDS",
    ],
    "PUBLICATIONS": [
        r"PUBLICATION",
        r"PUBLICATIONS",
        r"RESEARCH PUBLICATIONS",
    ],
    "LANGUAGES": [
        r"LANGUAGE",
        r"LANGUAGES",
        r"LANGUAGE SKILLS",
    ],
    "INTERESTS": [
        r"INTEREST",
        r"INTERESTS",
        r"HOBBIES",
        r"PERSONAL INTERESTS",
    ],
    "REFERENCES": [
        r"REFERENCE",
        r"REFERENCES",
        r"PROFESSIONAL REFERENCES",
    ],
}


def read_pdf_lines(pdf_path: str | Path) -> list[Line]:
    """Đọc từng dòng cùng metadata font và sắp xếp theo cột."""

    lines = []

    with pymupdf.open(pdf_path) as document:
        for page_number, page in enumerate(document, start=1):
            blocks = _extract_blocks(page)
            boundary = _find_column_boundary(blocks, page.rect.width)

            # Khi phát hiện hai cột, dùng thứ tự cột.
            # Nếu không, dùng thứ tự gần theo hàng.
            ordered_blocks = _order_blocks(blocks, page.rect.width)

            for block in ordered_blocks:
                # Lấy thông tin font từ block gốc để giữ size và bold.
                data = page.get_text("dict", sort=False)
                matching_blocks = [
                    item for item in data["blocks"]
                    if item.get("type") == 0
                    and tuple(round(v, 1) for v in item["bbox"])
                    == tuple(round(block[k], 1)
                             for k in ("x0", "y0", "x1", "y1"))
                ]

                if not matching_blocks:
                    continue

                for raw_line in matching_blocks[0].get("lines", []):
                    spans = raw_line.get("spans", [])
                    text = "".join(
                        span.get("text", "") for span in spans
                    )
                    text = re.sub(r"\s+", " ", text).strip()

                    if not text:
                        continue

                    size = max(
                        (span.get("size", 0) for span in spans),
                        default=0,
                    )
                    bold = any(
                        span.get("flags", 0) & 16
                        or "bold" in span.get("font", "").lower()
                        for span in spans
                    )

                    lines.append(
                        Line(
                            text=text,
                            size=float(size),
                            bold=bold,
                            page=page_number,
                        )
                    )

    return lines    

def normalize_lookalike_chars(text: str) -> str:
    """Normalize common Cyrillic characters that resemble Latin letters."""
    lookalikes = str.maketrans({
        "А": "A",
        "В": "B",
        "С": "C",
        "Е": "E",
        "Н": "H",
        "І": "I",
        "К": "K",
        "М": "M",
        "О": "O",
        "Р": "P",
        "Т": "T",
        "Х": "X",
        "а": "a",
        "с": "c",
        "е": "e",
        "о": "o",
        "р": "p",
        "х": "x",
    })
    return text.translate(lookalikes)


def match_section_keyword(text: str) -> str | None:
    """Nhận diện tiêu đề section tiếng Anh."""

    text = normalize_lookalike_chars(text)

    # Chuẩn hóa chữ hoa và khoảng trắng, nhưng giữ dấu ":".
    normalized = re.sub(r"\s+", " ", text.upper()).strip()

    # Heading có dấu ":" ở cuối thường là nhãn con.
    if normalized.endswith(":"):
        return None

    # Chuẩn hóa dấu câu còn lại.
    normalized = re.sub(r"[^A-Z& ]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()

    if not normalized or len(normalized.split()) > 5:
        return None

    for section_name, patterns in SECTION_PATTERNS.items():
        for pattern in patterns:
            if re.fullmatch(pattern, normalized):
                return section_name

    return None


def split_sections(lines: list[Line]) -> list[Section]:
    """Chia CV thành các mục dựa trên tiêu đề tiếng Anh."""
    if not lines:
        return []

    body_size = sorted(line.size for line in lines)[len(lines) // 2]

    sections = []
    current = Section(
        name="HEADER",
        title="HEADER",
        lines=[],
    )
    seen_keyword = False

    for line in lines:
        section_name = match_section_keyword(line.text)

        if section_name:
            if current.lines:
                sections.append(current)

            current = Section(
                name=section_name,
                title=line.text,
                lines=[],
            )
            seen_keyword = True
            continue

        # fallback 
        words = line.text.split()
        looks_like_heading = (
            seen_keyword
            and 1 <= len(words) <= 4
            and not re.search(r"\d", line.text)
            and not line.text.endswith((".", ",", ":"))
            and line.text.isupper()
            and len(line.text) > 3
            and line.bold
            and line.size >= body_size
        )

        if looks_like_heading:
            if current.lines:
                sections.append(current)

            current = Section(
                name="OTHER",
                title=line.text,
                lines=[],
            )
            continue

        current.lines.append(line)

    if current.lines:
        sections.append(current)

    return sections