from datetime import datetime, timezone
from typing import Any


STATUS_ACTIVE = "active"
STATUS_CLOSED = "closed"
STATUS_EXPIRED = "expired"

MISSING_GRACE_DAYS = 7
EXPIRE_AFTER_DAYS = 30
MATCH_RECENCY_DAYS = 21
RECENCY_SCORE_FLOOR = 0.7


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_datetime(value: Any) -> datetime | None:
    if value is None or value == "":
        return None

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    if isinstance(value, (int, float)):
        timestamp = float(value)
        if timestamp > 1e12:
            timestamp /= 1000
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)

    text = str(value).strip()
    if not text:
        return None

    if text.isdigit():
        return parse_datetime(int(text))

    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def job_age_days(
    posted_date: datetime | None,
    created_at: datetime | None,
    now: datetime,
) -> float | None:
    origin = posted_date or created_at
    if origin is None:
        return None
    return (now - origin).total_seconds() / 86400


def next_status(
    *,
    current_status: str | None,
    seen_in_crawl: bool,
    last_seen_at: datetime | None,
    posted_date: datetime | None,
    created_at: datetime | None,
    now: datetime,
    missing_grace_days: int = MISSING_GRACE_DAYS,
    expire_after_days: int = EXPIRE_AFTER_DAYS,
) -> str:
    age_days = job_age_days(posted_date, created_at, now)
    too_old = age_days is not None and age_days > expire_after_days

    if seen_in_crawl:
        if too_old:
            return STATUS_EXPIRED
        return STATUS_ACTIVE

    if last_seen_at is not None:
        missing_days = (now - last_seen_at).total_seconds() / 86400
        if missing_days >= missing_grace_days:
            return STATUS_CLOSED

    if too_old:
        return STATUS_EXPIRED

    return current_status or STATUS_ACTIVE


def is_matchable(
    *,
    status: str | None,
    posted_date: datetime | None,
    created_at: datetime | None,
    last_seen_at: datetime | None,
    now: datetime,
    recency_days: int = MATCH_RECENCY_DAYS,
) -> bool:
    if status != STATUS_ACTIVE:
        return False

    origin = posted_date or created_at or last_seen_at
    if origin is None:
        return False

    age_days = (now - origin).total_seconds() / 86400
    return 0 <= age_days <= recency_days


def recency_multiplier(
    age_days: float | None,
    recency_days: int = MATCH_RECENCY_DAYS,
    floor: float = RECENCY_SCORE_FLOOR,
) -> float:
    if age_days is None or recency_days <= 0:
        return 1.0

    bounded = min(max(age_days, 0.0) / recency_days, 1.0)
    return 1.0 - bounded * (1.0 - floor)
