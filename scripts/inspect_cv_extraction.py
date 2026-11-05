import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

from src.services.processing.cv_structure import read_pdf_lines, split_sections
from src.services.processing.cv_chunker import structure_chunk, MATCHING_SECTIONS
from src.services.processing.semantic_chunker import SemanticChunker
from src.config import settings

def inspect_cv(pdf_path: str):
    path = Path(pdf_path)
    if not path.exists():
        print(f" Không tìm thấy file PDF")
        return
    print("="*100)
    print(f">>> Kiểm tra trích xuất CV: {path.name}")
    print("="*100)

    lines = read_pdf_lines(pdf_path)
    print(f"Số dòng được được từ CV-PDF: {len(lines)}\n")

    sections = split_sections(lines)
    print(f"Nhận diện được {len(sections)} Sections")
    for idx, sec in enumerate(sections):
        print(f"[{idx+1:02d}] {sec.name:<15} | {sec.title[:50]} ({len(sec.lines)} dòng)")
        print("-" * 100)

    all_chunks = structure_chunk(sections)
    kept_chunks = [c for c in all_chunks if c.section in MATCHING_SECTIONS]
    # ignored_chunks = [c for c in all_chunks if c.section not in MATCHING_SECTIONS]

    # print(f"Lọc Section: Giữ lại {len(kept_chunks)} | Bỏ qua {len(ignored_chunks)}")
    # print("   -> Các section được giữ lại để Matching:")
    # for c in kept_chunks:
    #     print(f"      + {c.section}")

    print("\n" + "=" * 100)
    print(">>> SEMANTIC CHUNKING:")
    print("=" * 100)
    
    chunker = SemanticChunker(
        breakpoint_percentile=settings.BREAKPOINT_PERCENTILE,
        min_distance=settings.MIN_DISTANCE,
        min_chars=settings.MIN_CHARS,
        max_chars=settings.MAX_CHARS,
        window=settings.WINDOW,
    )
    
    final_chunks = []
    for sc in kept_chunks:
        sub_chunks = chunker.chunk_text(sc.text, header=sc.header)
        final_chunks.extend(sub_chunks)

    print(f"Tổng cộng tạo ra {len(final_chunks)} chunks matching:\n")
    for idx, text in enumerate(final_chunks, start=1):
        preview = text.replace("\n", " ").strip()
        print(f"[{idx:02d}] {preview}")
        print("-" * 100)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect CV")  
    parser.add_argument("pdf_path", type=str, help="Đường dẫn tới file PDF (VD: data/sample_cv.pdf)")
    args = parser.parse_args()

    inspect_cv(args.pdf_path)

