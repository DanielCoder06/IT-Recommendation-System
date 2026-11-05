from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class RawJob:
    """Dữ liệu job thô sau khi lấy từ một nguồn tuyển dụng."""

    source: str
    external_id: str | None
    title: str
    company: str | None
    location: str | None
    description: str
    job_url: str
    posted_date: datetime | None = None
    employment_type: str | None = None
    experience: str | None = None
    remote: bool | None = None
    tags: list[str] = field(default_factory=list)
    raw_data: dict[str, Any] = field(default_factory=dict)