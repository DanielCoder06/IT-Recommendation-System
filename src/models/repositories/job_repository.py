"""CRUD jobs + lifecycle refresh."""
from datetime import datetime, timezone

from psycopg2.extras import execute_batch

from src.models.entities.raw_job import RawJob
from src.models.repositories.connection import (
    get_connection,
    get_db_context,
    release_connection,
)
from src.services.processing.job_lifecycle import (
    MATCH_RECENCY_DAYS,
    is_matchable,
    next_status,
    parse_datetime,
    utc_now,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def upsert_job(job: RawJob) -> int:
    now = _now()
    posted_date = job.posted_date.isoformat() if job.posted_date else None

    with get_db_context() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO jobs (
                    source, external_id, title, company, location,
                    description, job_url, posted_date, employment_type,
                    experience, remote, status, last_seen_at, created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (job_url) DO UPDATE
                SET source = EXCLUDED.source,
                    external_id = EXCLUDED.external_id,
                    title = EXCLUDED.title,
                    company = EXCLUDED.company,
                    location = EXCLUDED.location,
                    description = EXCLUDED.description,
                    posted_date = EXCLUDED.posted_date,
                    employment_type = EXCLUDED.employment_type,
                    experience = EXCLUDED.experience,
                    remote = EXCLUDED.remote,
                    status = 'active',
                    last_seen_at = EXCLUDED.last_seen_at,
                    updated_at = EXCLUDED.updated_at
                RETURNING id;
                """,
                (
                    job.source, job.external_id, job.title, job.company,
                    job.location, job.description, job.job_url, posted_date,
                    job.employment_type, job.experience, job.remote,
                    "active", now, now, now,
                ),
            )
            row = cur.fetchone()
            return int(row["id"])


def delete_jobs_by_status(statuses: tuple[str, ...] = ("closed",)) -> int:
    if not statuses:
        return 0
    with get_db_context() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM jobs WHERE status = ANY(%s);", (list(statuses),))
            return cur.rowcount


def get_job_by_url(job_url: str) -> RawJob | None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM jobs WHERE job_url = %s;", (job_url,))
            row = cur.fetchone()
            if row is None:
                return None
            return RawJob(
                source=row["source"],
                external_id=row["external_id"],
                title=row["title"],
                company=row["company"],
                location=row["location"],
                description=row["description"],
                job_url=row["job_url"],
                posted_date=parse_datetime(row["posted_date"]),
                employment_type=row["employment_type"],
                experience=row["experience"],
                remote=bool(row["remote"]) if row["remote"] is not None else None,
            )
    finally:
        release_connection(conn)


def count_jobs(status_filter: str | None = None) -> int:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if status_filter:
                cur.execute("SELECT COUNT(*) AS c FROM jobs WHERE status = %s;", (status_filter,))
            else:
                cur.execute("SELECT COUNT(*) AS c FROM jobs;")
            row = cur.fetchone()
            return int(row["c"]) if row else 0
    finally:
        release_connection(conn)


def get_all_jobs(
    status_filter: str | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> list[dict]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            query = """
                SELECT id, title, company, location, description,
                       job_url AS url, experience, remote, posted_date,
                       created_at, last_seen_at, status
                FROM jobs
            """
            params: list = []
            if status_filter:
                query += " WHERE status = %s"
                params.append(status_filter)
            query += " ORDER BY updated_at DESC, id DESC"
            if limit is not None:
                query += " LIMIT %s OFFSET %s"
                params.extend([limit, offset])
            cur.execute(query, tuple(params))
            return [dict(row) for row in cur.fetchall()]
    finally:
        release_connection(conn)


def get_matchable_jobs(
    recency_days: int = MATCH_RECENCY_DAYS,
    now: datetime | None = None,
) -> list[dict]:
    now = now or utc_now()
    jobs = get_all_jobs()
    matchable: list[dict] = []
    for job in jobs:
        if is_matchable(
            status=job.get("status"),
            posted_date=parse_datetime(job.get("posted_date")),
            created_at=parse_datetime(job.get("created_at")),
            last_seen_at=parse_datetime(job.get("last_seen_at")),
            now=now,
            recency_days=recency_days,
        ):
            matchable.append(job)
    return matchable


def refresh_job_lifecycle(
    seen_job_urls: set[str],
    now: datetime | None = None,
    failed_sources: set[str] | None = None,
) -> dict[str, int]:
    now = now or utc_now()
    now_iso = now.isoformat()
    failed_sources = {s.lower() for s in (failed_sources or set())}

    counts = {"closed": 0, "expired": 0, "active": 0, "unchanged": 0}

    with get_db_context() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, source, job_url, status, last_seen_at, posted_date, created_at FROM jobs;"
            )
            rows = cur.fetchall()

            updates: list[tuple] = []
            for row in rows:
                job_source = (row["source"] or "").lower()
                if job_source in failed_sources:
                    counts["unchanged"] += 1
                    continue

                new_status = next_status(
                    current_status=row["status"],
                    seen_in_crawl=row["job_url"] in seen_job_urls,
                    last_seen_at=parse_datetime(row["last_seen_at"]),
                    posted_date=parse_datetime(row["posted_date"]),
                    created_at=parse_datetime(row["created_at"]),
                    now=now,
                )

                if new_status == row["status"]:
                    counts["unchanged"] += 1
                    continue

                updates.append((new_status, now_iso, row["id"]))
                counts[new_status] = counts.get(new_status, 0) + 1

            if updates:
                execute_batch(
                    cur,
                    "UPDATE jobs SET status = %s, updated_at = %s WHERE id = %s;",
                    updates,
                )

    return counts


def count_jobs_by_status() -> dict[str, int]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT status, COUNT(*) AS n FROM jobs GROUP BY status;")
            return {row["status"]: int(row["n"]) for row in cur.fetchall()}
    finally:
        release_connection(conn)