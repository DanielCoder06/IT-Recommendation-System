"""CRUD job_chunks + pgvector round-trip."""
import hashlib

import numpy as np
from psycopg2.extras import execute_values

from src.config import settings
from src.models.repositories.connection import (
    get_connection,
    get_db_context,
    release_connection,
)


def hash_description(text: str) -> str:
    return hashlib.md5((text or "").encode("utf-8")).hexdigest()


def save_job_chunks(
    job_id: int,
    chunks: list[dict],
    embeddings: np.ndarray,
    description_hash: str,
    model_name: str = settings.MODEL_NAME,
) -> None:
    """Ghi chunks + embeddings. Xoá chunks cũ của job_id trước."""
    if not chunks:
        return

    rows_to_insert = []
    for idx, (chunk_data, emb) in enumerate(zip(chunks, embeddings)):
        rows_to_insert.append((
            job_id,
            idx,
            chunk_data.get("category", "GENERAL"),
            chunk_data.get("text", ""),
            emb.tolist() if isinstance(emb, np.ndarray) else list(emb),
            model_name,
            description_hash,
        ))

    with get_db_context() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM job_chunks WHERE job_id = %s;", (job_id,))
            execute_values(
                cur,
                """
                INSERT INTO job_chunks
                    (job_id, chunk_index, category, text, embedding, model_name, description_hash)
                VALUES %s
                """,
                rows_to_insert,
                template="(%s, %s, %s, %s, %s::vector, %s, %s)",
            )


def get_job_chunks(
    job_id: int,
    categories: tuple[str, ...] = ("REQUIREMENT", "RESPONSIBILITY"),
) -> list[dict]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT chunk_index, category, text, embedding, description_hash
                FROM job_chunks
                WHERE job_id = %s AND category = ANY(%s)
                ORDER BY chunk_index ASC;
                """,
                (job_id, list(categories)),
            )
            result = []
            for r in cur.fetchall():
                emb = r["embedding"].to_numpy()  # ← Vector → np.ndarray
                result.append({
                    "chunk_index": r["chunk_index"],
                    "category": r["category"],
                    "text": r["text"],
                    "embedding": emb,
                    "description_hash": r["description_hash"],
                })
            return result
    finally:
        release_connection(conn)


def get_chunks_for_jobs(
    job_ids: list[int],
    categories: tuple[str, ...] = ("REQUIREMENT", "RESPONSIBILITY"),
) -> dict[int, list[dict]]:
    if not job_ids:
        return {}

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT job_id, chunk_index, category, text, embedding
                FROM job_chunks
                WHERE job_id = ANY(%s) AND category = ANY(%s)
                ORDER BY job_id, chunk_index ASC;
                """,
                (list(job_ids), list(categories)),
            )
            grouped: dict[int, list[dict]] = {jid: [] for jid in job_ids}
            for r in cur.fetchall():
                grouped[r["job_id"]].append({
                    "chunk_index": r["chunk_index"],
                    "category": r["category"],
                    "text": r["text"],
                    "embedding": r["embedding"].to_numpy(),  # ←
                })
            return grouped
    finally:
        release_connection(conn)


def delete_inactive_job_chunks() -> int:
    with get_db_context() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM job_chunks
                WHERE job_id IN (
                    SELECT id FROM jobs WHERE status IN ('closed', 'expired')
                );
                """
            )
            return cur.rowcount


def get_job_description_hash(job_id: int) -> str | None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT description_hash FROM job_chunks WHERE job_id = %s LIMIT 1;",
                (job_id,),
            )
            row = cur.fetchone()
            return row["description_hash"] if row else None
    finally:
        release_connection(conn)