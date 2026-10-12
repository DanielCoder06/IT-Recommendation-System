import requests

from src.models.raw_job import RawJob
from src.sources.base_source import BaseSource
from src.processing.job_lifecycle import parse_datetime
from src.processing.text_cleaner import clean_job_description


JOBICY_API_URL = "https://jobicy.com/api/v2/remote-jobs"


class JobicyScraper(BaseSource):

    def fetch(
        self,
        url: str = JOBICY_API_URL,
    ) -> list[RawJob]:

        response = requests.get(
            url,
            params={"count": 50},
            timeout=20,
        )
        response.raise_for_status()

        data = response.json()

        jobs = []

        for job in data.get("jobs", []):
            raw_job = RawJob(
                source="jobicy",
                external_id=str(job.get("id", "")),
                title=job.get("jobTitle", ""),
                company=job.get("companyName"),
                location=job.get("jobGeo"),
                description=clean_job_description(
                    job.get("jobDescription", "")
                ),
                job_url=job.get("url", ""),
                posted_date=parse_datetime(
                    job.get("jobPubDate") or job.get("pubDate")
                ),
                employment_type=", ".join(
                    job.get("jobType", [])
                ),
                experience=job.get("jobLevel"),
                remote=True,
                tags=job.get("jobIndustry", []),
                raw_data=job,
            )

            jobs.append(raw_job)

        return jobs
