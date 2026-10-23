from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from database.job_repository import get_all_jobs

# Khởi tạo ứng dụng FastAPI
app = FastAPI(
    title="IT Recommend System",
    description="Hệ thống tìm kiếm việc làm IT",
    version="1.0.0"
)

# Cấu hình CORS 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Phục vụ file tĩnh (CSS, JS)
WEB_DIR = Path(__file__).resolve().parent / "web"
app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")

@app.get("/")
def root():
    """Trả về giao diện trang chủ home.html khi truy cập http://127.0.0.1:8000/"""
    return FileResponse(WEB_DIR / "home.html")

@app.get("/api/jobs")
def get_jobs(page: int = 1, limit: int = 9, status: str = "active"):
    """
    API lấy danh sách các công việc IT hiện có trong database hỗ trợ phân trang
    - page: số thứ tự trang 
    - limit: số lượng công việc mỗi trang 
    - status: trạng thái công việc
    """
    status_filter = status if status.lower() != "all" else None
    all_jobs = get_all_jobs(status_filter=status_filter)
    total = len(all_jobs)
    
    # Tính toán vị trí cắt danh sách 
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    sliced_jobs = all_jobs[start_idx:end_idx]
    
    # Format dữ liệu trả về cho front-end
    formatted_jobs = []
    for job in sliced_jobs:
        formatted_jobs.append({
            "id": job.get("id"),
            "title": job.get("title") or "N/A",
            "company": job.get("company") or "Chưa rõ",
            "location": job.get("location") or "Toàn quốc",
            "url": job.get("url") or "#",
            "experience": job.get("experience") or "Không yêu cầu",
            "status": job.get("status")
        })
        
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit,
        "count": len(formatted_jobs),
        "data": formatted_jobs
    }


@app.post("/api/recommend-cv")
async def match_cv(
    file: UploadFile = File(...),
    exclude_senior: bool = Form(True),
    top_k: int = Form(6),
):
    """
    Nhận file CV (PDF), phân tích cấu trúc, ngữ nghĩa và so khớp điểm phù hợp với các Job trong database
    """
    import tempfile
    from src.pipeline.matching_service import recommend_jobs_for_cv

    # Lưu file PDF tạm 
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        recommended = recommend_jobs_for_cv(
            pdf_path=tmp_path,
            exclude_senior=exclude_senior,
            top_k=top_k,
        )
        return {
            "success": True,
            "filename": file.filename,
            "exclude_senior": exclude_senior,
            "total_matches": len(recommended),
            "data": recommended,
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "data": [],
        }
    finally:
        import os
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.post("/api/jobs/update")
async def update_jobs_from_sources():
    """
    Crawl dữ liệu việc làm IT mới nhất từ các nguồn (Jobicy, Arbeitnow) và cập nhật cơ sở dữ liệu
    """
    try:
        from src.pipeline.update_jobs import run_job_update
        result = run_job_update()
        return {
            "success": True,
            "message": "Cập nhật dữ liệu việc làm thành công",
            "data": result,
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
        }

