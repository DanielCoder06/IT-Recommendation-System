from src.processing.cv_structure import (
    read_pdf_lines,
    split_sections,
)

pdf_path = r"data\hTN-CV.pdf"

lines = read_pdf_lines(pdf_path)
sections = split_sections(lines)

from collections import Counter

input_lines = Counter(line.text for line in lines)

section_lines = Counter(
    line.text
    for section in sections
    for line in section.lines
)

section_titles = Counter(
    section.title
    for section in sections
    if section.title != "HEADER"
)

represented_lines = section_lines + section_titles

missing_lines = input_lines - represented_lines
unexpected_lines = represented_lines - input_lines

print("\n--- DATA INTEGRITY CHECK ---")
print("Input lines:", sum(input_lines.values()))
print("Represented lines:", sum(represented_lines.values()))
print("Missing lines:", sum(missing_lines.values()))
print("Unexpected lines:", sum(unexpected_lines.values()))

if missing_lines:
    print("\nMissing:")
    for text, count in missing_lines.items():
        print(f"  [{count}x] {text}")
        
print("Total lines:", len(lines))

for section in sections:
    print(f"\n[{section.name}] {section.title}")

    for line in section.lines:
        print(" -", line.text)

for line in lines:
    if "ONTA" in line.text.upper():
        print("Text:", repr(line.text))
        print("Characters:", [
            (char, f"U+{ord(char):04X}")
            for char in line.text
        ])
        
for section in sections:
    print(
        f"{section.name:15} "
        f"lines={len(section.lines):3} "
        f"title={section.title}"
    )


from src.processing.cv_structure import match_section_keyword

assert match_section_keyword("TECHNICAL SKILLS") == "SKILLS"
assert match_section_keyword("Languages:") is None
assert match_section_keyword("LANGUAGES") == "LANGUAGES"
assert match_section_keyword("PROJECTS") == "PROJECTS"
