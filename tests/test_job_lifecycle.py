from datetime import datetime, timedelta, timezone

from src.processing.job_lifecycle import (
    STATUS_ACTIVE,
    STATUS_CLOSED,
    STATUS_EXPIRED,
    is_matchable,
    next_status,
    parse_datetime,
    recency_multiplier,
)


NOW = datetime(2026, 10, 12, tzinfo=timezone.utc)


def test_parse_datetime_iso_and_unix():
    parsed_iso = parse_datetime("2026-10-01T08:00:00+00:00")
    parsed_unix = parse_datetime(NOW.timestamp())

    assert parsed_iso == datetime(2026, 10, 1, 8, tzinfo=timezone.utc)
    assert parsed_unix.date() == NOW.date()


def test_seen_job_stays_active():
    status = next_status(
        current_status=STATUS_CLOSED,
        seen_in_crawl=True,
        last_seen_at=NOW,
        posted_date=NOW - timedelta(days=3),
        created_at=NOW - timedelta(days=3),
        now=NOW,
    )

    assert status == STATUS_ACTIVE


def test_seen_but_too_old_is_expired():
    status = next_status(
        current_status=STATUS_ACTIVE,
        seen_in_crawl=True,
        last_seen_at=NOW,
        posted_date=NOW - timedelta(days=40),
        created_at=NOW - timedelta(days=40),
        now=NOW,
    )

    assert status == STATUS_EXPIRED


def test_missing_beyond_grace_is_closed():
    status = next_status(
        current_status=STATUS_ACTIVE,
        seen_in_crawl=False,
        last_seen_at=NOW - timedelta(days=7),
        posted_date=NOW - timedelta(days=10),
        created_at=NOW - timedelta(days=10),
        now=NOW,
    )

    assert status == STATUS_CLOSED


def test_missing_within_grace_stays_active():
    status = next_status(
        current_status=STATUS_ACTIVE,
        seen_in_crawl=False,
        last_seen_at=NOW - timedelta(days=2),
        posted_date=NOW - timedelta(days=5),
        created_at=NOW - timedelta(days=5),
        now=NOW,
    )

    assert status == STATUS_ACTIVE


def test_matchable_only_recent_active_jobs():
    assert is_matchable(
        status=STATUS_ACTIVE,
        posted_date=NOW - timedelta(days=10),
        created_at=NOW - timedelta(days=10),
        last_seen_at=NOW,
        now=NOW,
    )

    assert not is_matchable(
        status=STATUS_ACTIVE,
        posted_date=NOW - timedelta(days=25),
        created_at=NOW - timedelta(days=25),
        last_seen_at=NOW,
        now=NOW,
    )

    assert not is_matchable(
        status=STATUS_CLOSED,
        posted_date=NOW - timedelta(days=2),
        created_at=NOW - timedelta(days=2),
        last_seen_at=NOW,
        now=NOW,
    )


def test_recency_multiplier_decays():
    fresh = recency_multiplier(0)
    old = recency_multiplier(21)

    assert fresh == 1.0
    assert old == 0.7
    assert recency_multiplier(10) > old
