from datetime import datetime, timezone

from database.connection import get_connection
from src.models.raw_job import RawJob


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
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job.source,
                job.external_id,
                job.title,
                job.company,
                job.location,
                job.description,
                job.job_url,
                job.posted_date.isoformat()
                if job.posted_date
                else None,
                job.employment_type,
                job.experience,
                int(job.remote)
                if job.remote is not None
                else None,
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
                job.posted_date.isoformat()
                if job.posted_date
                else None,
                job.employment_type,
                job.experience,
                int(job.remote)
                if job.remote is not None
                else None,
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
        posted_date=row["posted_date"],
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
        SELECT id, title, company, location, description, job_url as url, experience, remote, posted_date
        FROM jobs
        ORDER BY id DESC
        """
    ).fetchall()
    connection.close()

    return [dict(row) for row in rows]