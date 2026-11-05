import logging
from src.app import app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s – %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn
    from src.config import settings
    uvicorn.run("src.app:app", host=settings.HOST, port=settings.PORT, reload=True)