from pathlib import Path
import sys

# Thêm thư mục gốc vào sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.processing.cv_structure import read_pdf_lines, split_sections
from src.processing.cv_chunker import structure_chunk
from src.processing.semantic_chunker import SemanticChunker

PDF_PATH = ROOT_DIR / "data" / "No-Name.pdf"

# Các Section chuyên môn cốt lõi được hệ thống giữ lại để matching
CV_CORE_SECTIONS = {
    "SKILLS",
    "PROJECTS",
    "EXPERIENCE",
    "WORK EXPERIENCE",
    "PROFILE",
    "SUMMARY",
}


def inspect_cv(pdf_path: str | Path = PDF_PATH) -> None:
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        print(f"Không tìm thấy file: {pdf_path}")
        return

    # 1. Trích xuất Sections và Chunks thô
    lines = read_pdf_lines(pdf_path)
    sections = split_sections(lines)
    all_chunks = structure_chunk(sections)

    # 2. Lọc các Section cốt lõi được giữ lại để matching
    kept_chunks = [c for c in all_chunks if c.section in CV_CORE_SECTIONS]
    ignored_chunks = [c for c in all_chunks if c.section not in CV_CORE_SECTIONS]

    print("=" * 70)
    print(f"CV: {pdf_path.name}")
    print(f"Tổng chunks trích xuất: {len(all_chunks)} | Giữ lại: {len(kept_chunks)} | Bỏ qua: {len(ignored_chunks)}")
    print("=" * 70)

    # 3. Hiển thị các chunks được giữ lại (Structure-based)
    print("\n>>> CÁC CHUNK SECTION ĐƯỢC GIỮ LẠI (DÙNG ĐỂ MATCHING):")
    for i, chunk in enumerate(kept_chunks, start=1):
        print(f"\n[{i}] SECTION: {chunk.section} | Header: '{chunk.header}' (Trang {chunk.page})")
        print("-" * 50)
        print(chunk.text.strip())
        print("-" * 50)

    # 4. Hiển thị kết quả sau khi cắt nhỏ qua SemanticChunker (đầu vào thực tế đưa vào Embedding)
    semantic_chunker = SemanticChunker(
        breakpoint_percentile=70.0,
        min_distance=0.15,
        min_chars=120,
        max_chars=500,
        window=1,
    )
    final_semantic_chunks = []
    for sc in kept_chunks:
        sub_chunks = semantic_chunker.chunk_text(sc.text, header=sc.header)
        final_semantic_chunks.extend(sub_chunks)

    print(f"\n>>> TỔNG CỘNG {len(final_semantic_chunks)} SEMANTIC CHUNKS CUỐI CÙNG (ĐƯA VÀO VECTOR EMBEDDING):")
    for idx, text in enumerate(final_semantic_chunks, start=1):
        preview = text.replace("\n", " ").strip()
        print(f"  ({idx:02d}) {preview}")


if __name__ == "__main__":
    target_pdf = sys.argv[1] if len(sys.argv) > 1 else PDF_PATH
    inspect_cv(target_pdf)
