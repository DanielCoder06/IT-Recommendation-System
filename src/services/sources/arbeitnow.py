import requests
from src.config import settings
from src.models.entities.raw_job import RawJob
from src.services.sources.base_source import BaseSource
from src.services.processing.job_lifecycle import parse_datetime
from src.utils.text_cleaner import clean_job_description

class ArbeitnowScraper(BaseSource):
    def fetch(self, url: str | None = None) -> list[RawJob]:
        target_url = url or settings.ARBEITNOW_URL
        response = requests.get(target_url, timeout=settings.ARBEITNOW_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        jobs = []
        for job in data.get("data", []):
            jobs.append(RawJob(
                source="arbeitnow",
                external_id=str(job.get("slug", "")),
                title=job.get("title", ""),
                company=job.get("company_name"),
                location=job.get("location"),
                description=clean_job_description(job.get("description", "")),
                job_url=job.get("url", ""),
                posted_date=parse_datetime(job.get("created_at")),
            ))
        return jobs