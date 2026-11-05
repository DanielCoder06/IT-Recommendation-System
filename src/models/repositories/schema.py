"""DDL idempotent cho PostgreSQL + pgvector."""
from src.config import settings


def apply_schema(connection) -> None:
    with connection.cursor() as cur:
        # Extension pgvector
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        # Bảng jobs
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id SERIAL PRIMARY KEY,
                source TEXT NOT NULL,
                external_id TEXT,
                title TEXT NOT NULL,
                company TEXT,
                location TEXT,
                description TEXT NOT NULL,
                job_url TEXT NOT NULL UNIQUE,
                posted_date TEXT,
                employment_type TEXT,
                experience TEXT,
                remote BOOLEAN,
                status TEXT NOT NULL DEFAULT 'active',
                last_seen_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )

        # Bảng job_chunks với vector(384)
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS job_chunks (
                job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                chunk_index INTEGER NOT NULL,
                category TEXT NOT NULL,
                text TEXT NOT NULL,
                embedding vector({settings.VECTOR_DIM}) NOT NULL,
                model_name TEXT NOT NULL,
                description_hash TEXT NOT NULL,
                PRIMARY KEY (job_id, chunk_index)
            );
            """
        )

        # Index thường
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_jobs_source         ON jobs(source);
            CREATE INDEX IF NOT EXISTS idx_jobs_posted_date    ON jobs(posted_date);
            CREATE INDEX IF NOT EXISTS idx_jobs_status         ON jobs(status);
            CREATE INDEX IF NOT EXISTS idx_job_chunks_job_id   ON job_chunks(job_id);
            CREATE INDEX IF NOT EXISTS idx_job_chunks_category ON job_chunks(category);
            """
        )

        # HNSW cosine index cho vector search
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_job_chunks_embedding
                ON job_chunks USING hnsw (embedding vector_cosine_ops);
            """
        )