import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from src.config import settings
from src.controllers import jobs_controller, matching_controller

logger = logging.getLogger(__name__)
PUBLIC_DIR = Path(__file__).resolve().parents[1] / "public"

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Startup server...")
    from src.models.repositories.connection import init_database
    init_database()
    
    try:
        from src.services.embeddings.embedding_model import get_embedding_model
        get_embedding_model()
    except Exception as e:
        logger.warning("Model is not ready: %s", e)
    yield
    logger.info("Server is shutdown.")

app = FastAPI(title="IT Recommend System", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware, allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False, allow_methods=["*"], allow_headers=["*"],
)

# Phục vụ thư mục public tại đường dẫn /static
if PUBLIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(PUBLIC_DIR)), name="static")

@app.get("/")
def root():
    # Trả về file index.html
    return FileResponse(PUBLIC_DIR / "index.html")

app.include_router(jobs_controller.router)
app.include_router(matching_controller.router)