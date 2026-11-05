import logging
from src.models.entities.raw_job import RawJob
from src.services.sources.arbeitnow import ArbeitnowScraper
from src.services.sources.jobicy import JobicyScraper

logger = logging.getLogger(__name__)

SOURCE_REGISTRY = [ArbeitnowScraper, JobicyScraper]

def fetch_all_jobs() -> tuple[list[RawJob], set[str]]:
    all_jobs: list[RawJob] = []
    failed_sources: set[str] = set()

    for scraper_cls in SOURCE_REGISTRY:
        scraper_name = scraper_cls.__name__
        try:
            scraper = scraper_cls()
            jobs = scraper.fetch()
            all_jobs.extend(jobs)
            logger.info("Thu thập thành công %d việc làm từ %s", len(jobs), scraper_name)
        except Exception as exc:
            logger.error("Lỗi khi thu thập từ %s: %s", scraper_name, exc)
            failed_sources.add(scraper_name.lower().replace("scraper", ""))

    return all_jobs, failed_sources