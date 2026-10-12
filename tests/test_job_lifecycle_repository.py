from datetime import datetime, timedelta, timezone

import database.connection as connection_mod
from database.job_repository import (
    get_matchable_jobs,
    refresh_job_lifecycle,
    upsert_job,
)
from src.models.raw_job import RawJob


NOW = datetime(2026, 10, 12, tzinfo=timezone.utc)


def _job(url: str, posted_date: datetime) -> RawJob:
    return RawJob(
        source="test",
        external_id=url,
        title="Python Developer",
        company="Acme",
        location="Remote",
        description="Python FastAPI",
        job_url=url,
        posted_date=posted_date,
    )


def test_refresh_closes_jobs_missing_from_crawl(tmp_path, monkeypatch):
    monkeypatch.setattr(connection_mod, "DB_PATH", tmp_path / "jobs.db")

    recent = _job("https://example.com/recent", NOW - timedelta(days=1))
    stale = _job("https://example.com/stale", NOW - timedelta(days=5))

    upsert_job(recent)
    upsert_job(stale)

    connection = connection_mod.get_connection()
    connection.execute(
        """
        UPDATE jobs
        SET last_seen_at = ?
        WHERE job_url = ?
        """,
        ((NOW - timedelta(days=8)).isoformat(), stale.job_url),
    )
    connection.commit()
    connection.close()

    changed = refresh_job_lifecycle({recent.job_url}, now=NOW)

    assert changed["closed"] == 1
    matchable = get_matchable_jobs(now=NOW)
    urls = {job["url"] for job in matchable}
    assert recent.job_url in urls
    assert stale.job_url not in urls


def test_matchable_jobs_exclude_old_active_listings(tmp_path, monkeypatch):
    monkeypatch.setattr(connection_mod, "DB_PATH", tmp_path / "jobs.db")

    fresh = _job("https://example.com/fresh", NOW - timedelta(days=3))
    old = _job("https://example.com/old", NOW - timedelta(days=28))

    upsert_job(fresh)
    upsert_job(old)

    matchable = get_matchable_jobs(now=NOW)
    urls = {job["url"] for job in matchable}

    assert fresh.job_url in urls
    assert old.job_url not in urls
