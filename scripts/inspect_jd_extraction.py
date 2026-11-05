import argparse

from src.models.repositories.connection import get_connection, release_connection
from src.services.processing.jd_parser import split_jd_units
from src.services.processing.jd_chunker import chunk_jd_text

CORE_JD_CATEGORIES = {"REQUIREMENT", "RESPONSIBILITY"}

def inspect_jd(job_id: int):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, title, company, location, status, description FROM jobs WHERE id = %s",
                (job_id,),
            )
            row = cur.fetchone()
    finally:
        release_connection(conn)

    if not row:
        print(f"Không tìm thấy Job có ID = {job_id} trong db.")
        return

    job = dict(row)
    jd_text = (job.get("description") or "").strip()

    if not jd_text:
        print(f"Job ID {job_id} ({job.get('title')}) không có nội dung description.")
        return 

    units = split_jd_units(jd_text)
    all_chunks = chunk_jd_text(text=jd_text, max_words=120)
    matching_chunks = [c for c in all_chunks if c.get("category") in CORE_JD_CATEGORIES]

    print(f"Job ID: {job['id']}")
    print(">>> Heading + Content")
    for i, u in enumerate(units):
        prefix = "[HEADING]" if u.is_heading else "[CONTENT]"
        print(f"[{i+1:03d}] {prefix} | [{u.category}] {u.text[:100]}")
    print("=" * 100)

    print(">>> [Units] sau khi chia chunk")
    for i, chunk in enumerate(all_chunks):
        print(f"Chunk {i+1} | Category: [{chunk['category']}]")
        print(f"Text: {chunk['text']}")
        print("-" * 100)
    print("=" * 100)

    print(f">>> Danh sách {len(matching_chunks)} chunks cốt lỗi")
    if not matching_chunks:
        print("Hệ thống sẽ bỏ qua job này khi Matching CV!")
    else:
        for i, chunk in enumerate(matching_chunks):
            print(f"[{i+1:03d}] [{chunk['category']}] {chunk['text']}")
            print("-" * 100)
    print("=" * 100)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect JD")
    parser.add_argument("job_id", type=int, help="ID của Job cần kiểm tra trong database")
    args = parser.parse_args()

    inspect_jd(args.job_id)