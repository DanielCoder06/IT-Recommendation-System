from dataclasses import dataclass
from src.services.processing.cv_structure import Section

@dataclass
class CVChunk:
    """Đại diện cho một chunk được tạo từ cấu trúc CV."""
    section: str
    header: str
    text: str
    page: int
    index: int

# Section quan trọng trong CV được tạo ra.
MATCHING_SECTIONS = {
    "SUMMARY", "PROFILE", "SKILLS", "PROJECTS", "EXPERIENCE",
    "WORK EXPERIENCE", "EDUCATION", "CERTIFICATIONS", "LANGUAGES",
}

def structure_chunk(sections: list[Section]) -> list[CVChunk]:
    """Tạo một chunk cho mỗi section quan trọng của CV."""
    chunks: list[CVChunk] = []
    for section in sections:
        section_name = section.name.strip().upper()
        if section_name not in MATCHING_SECTIONS:
            continue
        if not section.lines:
            continue

        chunks.append(CVChunk(
            section=section_name,
            header=section.title.strip() or section_name,
            text="\n".join(line.text for line in section.lines),
            page=section.lines[0].page,
            index=len(chunks),
        ))
    return chunks