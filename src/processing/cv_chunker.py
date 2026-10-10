
from dataclasses import dataclass

from src.processing.cv_structure import Section


@dataclass
class CVChunk:
    """Đại diện cho một chunk được tạo từ cấu trúc CV."""

    section: str
    header: str
    text: str
    page: int
    index: int


# Section quan trong CV được tạo ra.
MATCHING_SECTIONS = {
    "SUMMARY",
    "PROFILE",
    "SKILLS",
    "PROJECTS",
    "EXPERIENCE",
    "WORK EXPERIENCE",
    "EDUCATION",
    "CERTIFICATIONS",
    "LANGUAGES",
}


def structure_chunk(sections: list[Section]) -> list[CVChunk]:
    """
    Tạo một chunk cho mỗi section quan trọng của CV.
    Giữ nguyên nội dung các dòng trong section được chọn.
    """
    chunks: list[CVChunk] = []

    for section in sections:
        section_name = section.name.strip().upper()

        # Bỏ qua section không nằm trong danh sách matching.
        if section_name not in MATCHING_SECTIONS:
            continue

        # Bỏ qua section không có nội dung.
        if not section.lines:
            continue

        chunks.append(
            CVChunk(
                section=section_name,
                header=section.title.strip() or section_name,
                text="\n".join(line.text for line in section.lines),
                page=section.lines[0].page,
                index=len(chunks),
            )
        )

    return chunks