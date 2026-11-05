import requests
from src.config import settings
from src.models.entities.raw_job import RawJob
from src.services.sources.base_source import BaseSource
from src.services.processing.job_lifecycle import parse_datetime
from src.utils.text_cleaner import clean_job_description

class JobicyScraper(BaseSource):
    def fetch(self, url: str | None = None) -> list[RawJob]:
        target_url = url or settings.JOBICY_URL
        response = requests.get(target_url, params={"count": settings.JOBICY_COUNT}, timeout=settings.JOBICY_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        jobs = []
        for job in data.get("jobs", []):
            jobs.append(RawJob(
                source="jobicy",
                external_id=str(job.get("id", "")),
                title=job.get("jobTitle", ""),
                company=job.get("companyName"),
                location=job.get("jobGeo"),
                description=clean_job_description(job.get("jobDescription", "")),
                job_url=job.get("url", ""),
                posted_date=parse_datetime(job.get("jobPubDate") or job.get("pubDate")),
                remote=True,
            ))
        return jobs