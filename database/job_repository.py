from datetime import datetime, timezone

from database.connection import get_connection
from src.models.raw_job import RawJob
from src.processing.job_lifecycle import (
    MATCH_RECENCY_DAYS,
    is_matchable,
    next_status,
    parse_datetime,
    utc_now,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def upsert_job(job: RawJob) -> int:
    connection = get_connection()

    now = _now()

    existing = connection.execute(
        """
        SELECT id
        FROM jobs
        WHERE job_url = ?
        """,
        (job.job_url,),
    ).fetchone()

    posted_date = (
        job.posted_date.isoformat()
        if job.posted_date
        else None
    )

    if existing is None:
        cursor = connection.execute(
            """
            INSERT INTO jobs (
                source,
                external_id,
                title,
                company,
                location,
                description,
                job_url,
                posted_date,
                employment_type,
                experience,
                remote,
                status,
                last_seen_at,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job.source,
                job.external_id,
                job.title,
                job.company,
                job.location,
                job.description,
                job.job_url,
                posted_date,
                job.employment_type,
                job.experience,
                int(job.remote)
                if job.remote is not None
                else None,
                "active",
                now,
                now,
                now,
            ),
        )

        job_id = cursor.lastrowid

    else:
        job_id = existing["id"]

        connection.execute(
            """
            UPDATE jobs
            SET
                source = ?,
                external_id = ?,
                title = ?,
                company = ?,
                location = ?,
                description = ?,
                posted_date = ?,
                employment_type = ?,
                experience = ?,
                remote = ?,
                status = ?,
                last_seen_at = ?,
                updated_at = ?
            WHERE job_url = ?
            """,
            (
                job.source,
                job.external_id,
                job.title,
                job.company,
                job.location,
                job.description,
                posted_date,
                job.employment_type,
                job.experience,
                int(job.remote)
                if job.remote is not None
                else None,
                "active",
                now,
                now,
                job.job_url,
            ),
        )

    connection.commit()
    connection.close()

    return int(job_id)


def get_job_by_url(
    job_url: str,
) -> RawJob | None:

    connection = get_connection()

    row = connection.execute(
        """
        SELECT *
        FROM jobs
        WHERE job_url = ?
        """,
        (job_url,),
    ).fetchone()

    connection.close()

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
        remote=bool(row["remote"])
        if row["remote"] is not None
        else None,
    )


def get_all_jobs() -> list[dict]:
    """
    Lấy toàn bộ danh sách jobs dưới dạng dict để phục vụ pipeline matching
    """
    connection = get_connection()
    rows = connection.execute(
        """
        SELECT
            id,
            title,
            company,
            location,
            description,
            job_url as url,
            experience,
            remote,
            posted_date,
            created_at,
            last_seen_at,
            status
        FROM jobs
        ORDER BY id DESC
        """
    ).fetchall()
    connection.close()

    return [dict(row) for row in rows]


def get_matchable_jobs(
    recency_days: int = MATCH_RECENCY_DAYS,
    now: datetime | None = None,
) -> list[dict]:
    now = now or utc_now()
    jobs = get_all_jobs()

    matchable = []
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
) -> dict[str, int]:
    now = now or utc_now()
    now_iso = now.isoformat()

    connection = get_connection()
    rows = connection.execute(
        """
        SELECT id, job_url, status, last_seen_at, posted_date, created_at
        FROM jobs
        """
    ).fetchall()

    counts = {
        "closed": 0,
        "expired": 0,
        "active": 0,
        "unchanged": 0,
    }

    for row in rows:
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

        connection.execute(
            """
            UPDATE jobs
            SET status = ?, updated_at = ?
            WHERE id = ?
            """,
            (new_status, now_iso, row["id"]),
        )

        counts[new_status] = counts.get(new_status, 0) + 1

    connection.commit()
    connection.close()

    return counts


def count_jobs_by_status() -> dict[str, int]:
    connection = get_connection()
    rows = connection.execute(
        """
        SELECT status, COUNT(*) AS n
        FROM jobs
        GROUP BY status
        """
    ).fetchall()
    connection.close()
    return {row["status"]: int(row["n"]) for row in rows}
