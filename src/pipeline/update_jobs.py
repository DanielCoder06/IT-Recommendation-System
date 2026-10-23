from src.sources.arbeitnow import ArbeitnowScraper
from src.sources.jobicy import JobicyScraper

from src.processing.job_adapter import raw_jobs_to_job_records
from src.processing.job_filter import filter_it_jobs

from database.job_repository import (
    count_jobs_by_status,
    refresh_job_lifecycle,
    upsert_job,
)

def run_job_update() -> dict:
    # Crawl data from sources
    raw_jobs = (
        ArbeitnowScraper().fetch()
        + JobicyScraper().fetch()
    )
    
    # Convert raw jobs to job record 
    job_records = raw_jobs_to_job_records(raw_jobs)
    
    # Filter IT jobs
    it_jobs = filter_it_jobs(job_records)
    
    # Get urls of IT jobs (!set() ->delete duplicates url)
    it_job_urls = {
        job.url 
        for job in it_jobs
    }
    
    # Get raw job by url
    it_raw_jobs = [
        job
        for job in raw_jobs
        if job.job_url in it_job_urls 
    ]
    
    # Save / Update db
    saved_jobs = 0
    for job in it_raw_jobs:
        upsert_job(job)
        saved_jobs += 1

    changed = refresh_job_lifecycle(it_job_urls)
    totals = count_jobs_by_status()

    return {
        "raw_jobs_count": len(raw_jobs),
        "it_jobs_count": len(it_jobs),
        "saved_jobs": saved_jobs,
        "closed_jobs": changed.get("closed", 0),
        "expired_jobs": changed.get("expired", 0),
        "active_jobs": totals.get("active", 0),
    }

def main():
    res = run_job_update()
    print(f"Jobs saved: {res['saved_jobs']}")
    print(f"Active jobs: {res['active_jobs']}")
    print(f"Closed: {res['closed_jobs']}, Expired: {res['expired_jobs']}")
    
if __name__ == "__main__":
    main()