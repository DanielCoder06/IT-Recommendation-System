import sys
import logging
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.models.repositories.connection import get_connection, release_connection, init_database
from src.services.matching.chunk_indexer import index_job_chunks

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def backfill_all():
    """Tìm các job active chưa có vector và tiến hành index bù."""
    init_database()
    
    # Tìm các job bị thiếu vector
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, title, description
                FROM jobs
                WHERE status = 'active'
                  AND id NOT IN (SELECT DISTINCT job_id FROM job_chunks)
                """
            )
            rows = cur.fetchall()
    finally:
        release_connection(conn)

    total = len(rows)
    logger.info("Bắt đầu backfill embeddings cho %d jobs...", total)

    if total == 0:
        logger.info("Không có job nào cần backfill.")
        return

    # Duyệt và xử lý từng job
    indexed = 0
    for idx, r in enumerate(rows, start=1):
        try:
            # Để nó tự kiểm tra MD5 
            if index_job_chunks(r["id"], r["description"]):
                indexed += 1
                
        except Exception as e:
            logger.error("Lỗi khi index job %d (%s): %s", r["id"], r["title"], e)

    logger.info("Đã index %d/%d jobs.", indexed, total)

if __name__ == "__main__":
    backfill_all()