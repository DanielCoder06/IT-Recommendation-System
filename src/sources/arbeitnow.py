import requests

from src.models.raw_job import RawJob
from src.sources.base_source import BaseSource
from src.processing.job_lifecycle import parse_datetime
from src.processing.text_cleaner import clean_job_description


ARBEITNOW_API_URL = "https://www.arbeitnow.com/api/job-board-api"


class ArbeitnowScraper(BaseSource):

    def fetch(
        self,
        url: str = ARBEITNOW_API_URL,
    ) -> list[RawJob]:

        response = requests.get(
            url,
            timeout=20,
        )
        response.raise_for_status()

        data = response.json()

        jobs = []

        for job in data["data"]:
            job_record = RawJob(
                source="arbeitnow",
                external_id=str(job.get("slug", "")),
                title=job["title"],
                company=job.get("company_name"),
                location=job.get("location"),
                description=clean_job_description(
                    job.get("description", "")
                ),
                job_url=job["url"],
                posted_date=parse_datetime(job.get("created_at")),
                experience=None,
                raw_data=job,
            )

            jobs.append(job_record)

        return jobs
