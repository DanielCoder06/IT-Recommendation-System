from collections import Counter

from src.processing.cv_structure import (
    Line,
    Section,
    read_pdf_lines,
    split_sections,
)
from src.processing.cv_chunker import (
    MATCHING_SECTIONS,
    structure_chunk,
)


CV_PATHS = [
    r"data\Java Intern-CV.pdf",
    r"data\MyCV-VoCaoThanhDat.pdf",
]


def test_section_filtering():
    """Chỉ tạo chunk cho section phục vụ matching."""

    sections = [
        Section(
            name="SUMMARY",
            title="SUMMARY",
            lines=[
                Line("Python developer", 10, False, 1),
                Line("Interested in backend development", 10, False, 1),
            ],
        ),
        Section(
            name="SKILLS",
            title="SKILLS",
            lines=[
                Line("Python, SQL, Git", 10, False, 1),
            ],
        ),
        Section(
            name="PROJECTS",
            title="PROJECTS",
            lines=[
                Line("Project A", 10, True, 1),
                Line("Built a web application", 10, False, 1),
                Line("Project B", 10, True, 1),
                Line("Built a REST API", 10, False, 1),
            ],
        ),
        Section(
            name="CONTACT",
            title="CONTACT",
            lines=[
                Line("email@example.com", 10, False, 1),
            ],
        ),
        Section(
            name="REFERENCES",
            title="REFERENCES",
            lines=[
                Line("Available upon request", 10, False, 1),
            ],
        ),
        Section(
            name="SKILLS",
            title="SKILLS",
            lines=[],
        ),
    ]

    chunks = structure_chunk(sections)

    # Chỉ giữ các section được cấu hình để matching.
    expected_sections = [
        section.name
        for section in sections
        if section.name in MATCHING_SECTIONS and section.lines
    ]

    assert [chunk.section for chunk in chunks] == expected_sections

    # CONTACT và REFERENCES không được tạo chunk.
    assert all(
        chunk.section not in {"CONTACT", "REFERENCES"}
        for chunk in chunks
    )

    # Mỗi section được chọn chỉ tạo một chunk.
    assert len(chunks) == 3

    summary_chunk, skills_chunk, projects_chunk = chunks

    assert summary_chunk.text == (
        "Python developer\n"
        "Interested in backend development"
    )
    assert skills_chunk.text == "Python, SQL, Git"

    # PROJECTS là một chunk duy nhất, không tách từng project.
    assert "Project A" in projects_chunk.text
    assert "Project B" in projects_chunk.text
    assert "Built a REST API" in projects_chunk.text

    # Header sử dụng tiêu đề section.
    assert summary_chunk.header == "SUMMARY"
    assert projects_chunk.header == "PROJECTS"

    # Index liên tục và page lấy từ dòng đầu tiên.
    assert [chunk.index for chunk in chunks] == [0, 1, 2]
    assert all(chunk.page == 1 for chunk in chunks)

    # Không làm mất hoặc thay đổi các dòng trong section được chọn.
    expected_lines = [
        line.text
        for section in sections
        if section.name in MATCHING_SECTIONS
        for line in section.lines
    ]
    actual_lines = [
        line
        for chunk in chunks
        for line in chunk.text.splitlines()
    ]

    assert Counter(actual_lines) == Counter(expected_lines)

    print("PASS: test_section_filtering")


def test_real_cv(pdf_path: str):
    """Kiểm tra lọc section trên một CV PDF thực tế."""

    lines = read_pdf_lines(pdf_path)
    sections = split_sections(lines)
    chunks = structure_chunk(sections)

    # Không có section ngoài danh sách matching.
    assert all(
        chunk.section in MATCHING_SECTIONS
        for chunk in chunks
    )

    # Không tạo chunk rỗng.
    assert all(chunk.text.strip() for chunk in chunks)

    # Cho phép nhiều section có cùng tên.
    # Mỗi chunk vẫn phải có nội dung và thuộc nhóm section matching.
    assert all(chunk.section in MATCHING_SECTIONS for chunk in chunks)
    assert all(chunk.text.strip() for chunk in chunks)

    # Index phải liên tục và không bị trùng.
    assert [chunk.index for chunk in chunks] == list(range(len(chunks)))
    # Các dòng thuộc section được chọn phải được bảo toàn.
    expected_lines = [
        line.text
        for section in sections
        if section.name.strip().upper() in MATCHING_SECTIONS
        for line in section.lines
    ]
    actual_lines = [
        line
        for chunk in chunks
        for line in chunk.text.splitlines()
    ]

    assert Counter(actual_lines) == Counter(expected_lines)

    print(f"\nCV: {pdf_path}")
    print(f"Số dòng PDF: {len(lines)}")
    print(f"Số section: {len(sections)}")
    print(f"Số chunk matching: {len(chunks)}")

    for chunk in chunks:
        print(f"\n[{chunk.index}] {chunk.section} - {chunk.header}")
        print(chunk.text)

    return chunks


def main():
    test_section_filtering()

    for pdf_path in CV_PATHS:
        test_real_cv(pdf_path)

    print("\nPASS: Tất cả kiểm thử CV chunking đã hoàn thành.")


if __name__ == "__main__":
    main()
