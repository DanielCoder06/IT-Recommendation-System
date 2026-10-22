from pathlib import Path
import sys

# Thêm thư mục gốc vào sys.path để import các module trong src & database
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from database.connection import get_connection
from src.processing.jd_parser import split_jd_units
from src.processing.jd_chunker import chunk_jd_text

DEFAULT_JOB_ID = 381

CORE_JD_CATEGORIES = {"REQUIREMENT", "RESPONSIBILITY"}


def get_job_by_id(job_id: int) -> dict | None:
    """Truy vấn thông tin Job từ database theo ID."""
    connection = get_connection()
    row = connection.execute(
        """
        SELECT id, title, company, location, experience, status, description, job_url
        FROM jobs
        WHERE id = ?
        """,
        (job_id,),
    ).fetchone()
    connection.close()

    return dict(row) if row else None


def list_sample_jobs(limit: int = 5) -> None:
    """Liệt kê một vài job mẫu để người dùng dễ chọn ID."""
    connection = get_connection()
    rows = connection.execute(
        f"SELECT id, title, company, status FROM jobs ORDER BY id LIMIT {limit}"
    ).fetchall()
    connection.close()

    print("\n[Gợi ý một số Job ID có sẵn trong Database]:")
    for r in rows:
        print(f"  - ID {r['id']:<4} | {r['title'][:40]:<40} | Công ty: {r['company']} ({r['status']})")
    print()


def extract_jd_sections(units) -> list[dict]:
    """Gom nhóm các text units thành các section dựa trên các heading đã nhận diện."""
    sections = []
    current_section = {
        "title": "INTRODUCTION / GENERAL",
        "category": "GENERAL",
        "lines": [],
    }

    for unit in units:
        if unit.is_heading:
            if current_section["lines"]:
                sections.append(current_section)
            current_section = {
                "title": unit.text,
                "category": unit.category,
                "lines": [],
            }
        else:
            current_section["lines"].append(unit.text)

    if current_section["lines"]:
        sections.append(current_section)

    return sections


def inspect_jd(job_id: int = DEFAULT_JOB_ID) -> None:
    job = get_job_by_id(job_id)
    if not job:
        print(f"[ERROR] Không tìm thấy Job có ID = {job_id} trong database.")
        list_sample_jobs()
        return

    jd_text = job.get("description", "")
    if not jd_text or not jd_text.strip():
        print(f"[WARN] Job ID {job_id} ({job.get('title')}) không có nội dung description.")
        return

    # 1. Phân tích cú pháp và tách thành các Text Units
    units = split_jd_units(jd_text)
    sections = extract_jd_sections(units)

    # 2. Trích xuất toàn bộ chunks bằng jd_chunker (Hybrid semantic & heading chunking)
    all_chunks = chunk_jd_text(
        text=jd_text,
        max_words=120,
        overlap_units=0,
    )

    # 3. Lọc các chunks quan trọng (REQUIREMENT & RESPONSIBILITY) dùng để so khớp năng lực
    kept_chunks = [c for c in all_chunks if c.get("category") in CORE_JD_CATEGORIES]
    other_chunks = [c for c in all_chunks if c.get("category") not in CORE_JD_CATEGORIES]

    print("=" * 70)
    print(f"JOB ID: {job['id']} | {job['title']} @ {job['company']}")
    print(f"Địa điểm: {job.get('location')} | Trạng thái: {job.get('status')}")
    print(f"Tổng sections nhận diện: {len(sections)}")
    print(f"Tổng chunks trích xuất: {len(all_chunks)} | Giữ lại (Matching): {len(kept_chunks)} | Khác: {len(other_chunks)}")
    print("=" * 70)

    # -------------------------------------------------------------
    # PHẦN 1: HIỂN THỊ CÁC SECTION ĐÃ ĐƯỢC CHIA TỪ JD
    # -------------------------------------------------------------
    print("\n>>> DANH SÁCH CÁC SECTION TRONG JD:")
    for idx, sec in enumerate(sections, start=1):
        line_count = len(sec["lines"])
        preview = "\n".join(f"    • {line}" for line in sec["lines"][:4])
        print(f"\n--- Section #{idx}: [{sec['category']}] Title: '{sec['title']}' ({line_count} dòng) ---")
        print(preview)
        if line_count > 4:
            print(f"    ... (còn {line_count - 4} dòng nữa)")

    # -------------------------------------------------------------
    # PHẦN 2: CÁC CHUNK QUAN TRỌNG ĐƯỢC GIỮ LẠI (DÙNG ĐỂ MATCHING)
    # -------------------------------------------------------------
    print("\n\n" + "=" * 70)
    print(">>> CÁC CHUNKS QUAN TRỌNG ĐƯỢC GIỮ LẠI (DÙNG ĐỂ MATCHING VỚI CV):")
    print("=" * 70)
    if not kept_chunks:
        print("  (Không tìm thấy chunk thuộc nhóm REQUIREMENT hoặc RESPONSIBILITY)")
    for i, chunk in enumerate(kept_chunks, start=1):
        print(f"\n[{i}] PHÂN LOẠI: [{chunk['category']}]")
        print("-" * 50)
        print(chunk["text"].strip())
        print("-" * 50)

    # -------------------------------------------------------------
    # PHẦN 3: TỔNG HỢP DANH SÁCH CHUNKS MATCHING RÚT GỌN
    # -------------------------------------------------------------
    print(f"\n>>> TỔNG HỢP {len(kept_chunks)} CHUNKS SẼ SO KHỚP VỚI CV EMBEDDING:")
    for idx, chunk in enumerate(kept_chunks, start=1):
        preview = chunk["text"].replace("\n", " ").strip()
        print(f"  ({idx:02d}) [{chunk['category']}] {preview[:120]}...")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            target_id = int(sys.argv[1])
        except ValueError:
            print("[ERROR] ID phải là số nguyên.")
            sys.exit(1)
    else:
        target_id = DEFAULT_JOB_ID

    inspect_jd(target_id)
