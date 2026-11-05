import logging
import threading
from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks, Header, HTTPException
from src.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Jobs"])

_update_lock = threading.Lock()
_update_status = {"is_running": False, "last_run": None, "last_result": None, "last_error": None}

@router.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat(), "version": "1.0.0"}

@router.get("/api/jobs")
def get_jobs(page: int = 1, limit: int = settings.PAGE_SIZE, status: str = "active"):
    from src.models.repositories.job_repository import count_jobs, get_all_jobs
    if page < 1: page = 1
    if limit < 1: limit = settings.PAGE_SIZE

    status_filter = status if status.lower() != "all" else None
    total = count_jobs(status_filter=status_filter)
    offset = (page - 1) * limit
    sliced_jobs = get_all_jobs(status_filter=status_filter, limit=limit, offset=offset)

    formatted_jobs = [
        {
            "id": job.get("id"),
            "title": job.get("title") or "N/A",
            "company": job.get("company") or "N/A",
            "location": job.get("location") or "N/A",
            "url": job.get("url") or "",
            "experience": job.get("experience") or "N/A",
            "status": job.get("status"),
        }
        for job in sliced_jobs
    ]
    return {
        "total": total, "page": page, "limit": limit,
        "total_pages": (total + limit - 1) // limit if total > 0 else 1,
        "count": len(formatted_jobs), "data": formatted_jobs,
    }

def _background_job_update_worker():
    from src.services.sources.job_sources import fetch_all_jobs
    from src.services.processing.job_filter import filter_it_jobs
    from src.models.repositories.job_repository import upsert_job, count_jobs_by_status
    from src.services.matching.chunk_indexer import index_job_chunks

    try:
        raw_jobs, failed_sources = fetch_all_jobs()
        it_jobs = filter_it_jobs(raw_jobs)
        saved = 0
        for job in it_jobs:
            if job.job_url and job.title:
                job_id = upsert_job(job)
                index_job_chunks(job_id, job.description)
                saved += 1
        
        totals = count_jobs_by_status()
        _update_status["last_result"] = {"active_jobs": totals.get("active", 0), "saved_jobs": saved}
        _update_status["last_error"] = None
    except Exception as exc:
        logger.exception("Lỗi cập nhật jobs")
        _update_status["last_error"] = str(exc)
    finally:
        _update_status["is_running"] = False
        _update_status["last_run"] = datetime.now(timezone.utc).isoformat()
        if _update_lock.locked():
            _update_lock.release()

@router.post("/api/jobs/update")
def update_jobs_from_sources(background_tasks: BackgroundTasks, authorization: str | None = Header(None)):
    if settings.UPDATE_TOKEN:
        token = authorization.replace("Bearer ", "") if authorization else ""
        if token != settings.UPDATE_TOKEN:
            raise HTTPException(status_code=401, detail="Token xác thực không hợp lệ.")
    if not _update_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="Tiến trình cập nhật đang chạy.")
    
    _update_status["is_running"] = True
    background_tasks.add_task(_background_job_update_worker)
    return {"message": "Đã bắt đầu cập nhật.", "status": "started"}

@router.get("/api/jobs/update/status")
def get_update_status():
    return _update_status