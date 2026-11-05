import logging
import os
import tempfile
import pymupdf
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from src.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Matching"])

@router.post("/api/recommend-cv")
def match_cv(file: UploadFile = File(...), exclude_senior: bool = Form(True), top_k: int = Form(settings.TOP_K)):
    from src.services.matching.matching_service import recommend_jobs_for_cv, CVContentError
    
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    content = file.file.read(max_bytes + 1)
    
    if len(content) > max_bytes:
        raise HTTPException(413, f"File vượt quá giới hạn {settings.MAX_UPLOAD_MB} MB.")
    if not content.startswith(b"%PDF-"):
        raise HTTPException(400, "File không phải PDF hợp lệ.")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            with pymupdf.open(tmp_path) as doc:
                page_count = len(doc)
        except Exception:
            raise HTTPException(400, "Không thể đọc file PDF.")

        if page_count > settings.MAX_PAGES:
            raise HTTPException(400, f"CV có {page_count} trang, vượt quá {settings.MAX_PAGES} trang.")

        recommended = recommend_jobs_for_cv(pdf_path=tmp_path, exclude_senior=exclude_senior, top_k=top_k)

        for job in recommended:
            job.pop("_score", None)

        return {"filename": file.filename, "total_matches": len(recommended), "data": recommended}

    except HTTPException:
        raise
    except CVContentError as exc:
        raise HTTPException(422, str(exc))
    except Exception as e:
        logger.exception("Lỗi xử lý CV")
        raise HTTPException(500, "Lỗi nội bộ khi xử lý CV.")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)