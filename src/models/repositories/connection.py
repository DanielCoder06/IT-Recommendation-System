"""Connection pool PostgreSQL + pgvector."""
import logging
from contextlib import contextmanager
from typing import Generator

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from pgvector.psycopg2 import register_vector

from src.config import settings
from src.models.repositories.schema import apply_schema

logger = logging.getLogger(__name__)

_pool: pool.SimpleConnectionPool | None = None
_schema_initialized = False


def _get_connection_params() -> dict:
    """Chỉ trả về các key psycopg2 hiểu được."""
    dsn = (settings.DATABASE_URL or "").strip()
    if dsn:
        return {"dsn": dsn}
    return {
        "host": settings.POSTGRES_HOST,
        "port": settings.POSTGRES_PORT,
        "dbname": settings.POSTGRES_DB,
        "user": settings.POSTGRES_USER,
        "password": settings.POSTGRES_PASSWORD,
    }


def get_pool() -> pool.SimpleConnectionPool:
    global _pool
    if _pool is None:
        params = _get_connection_params()
        _pool = pool.SimpleConnectionPool(
            minconn=1,
            maxconn=20,
            **params,
            cursor_factory=RealDictCursor,
        )
        logger.info("Đã tạo connection pool PostgreSQL (%s)", settings.POSTGRES_DB)
    return _pool


def get_connection():
    """Lấy connection từ pool, đảm bảo schema tồn tại, rồi đăng ký type vector."""
    global _schema_initialized
    p = get_pool()
    conn = p.getconn()
    conn.autocommit = False

    if not _schema_initialized:
        try:
            apply_schema(conn)
            conn.commit()
            _schema_initialized = True
            logger.info("Schema đã sẵn sàng.")
        except Exception:
            conn.rollback()
            raise

    try:
        register_vector(conn)
    except psycopg2.ProgrammingError:

        apply_schema(conn)
        conn.commit()
        register_vector(conn)

    return conn


def release_connection(conn) -> None:
    """Trả connection về pool."""
    if _pool and conn:
        try:
            _pool.putconn(conn)
        except Exception:
            pass


@contextmanager
def get_db_context() -> Generator:
    """Tự commit khi thành công, rollback khi lỗi, luôn trả conn về pool."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        release_connection(conn)


def init_database() -> None:
    """Gọi lúc app startup: đảm bảo schema tồn tại."""
    with get_db_context() as conn:
        apply_schema(conn)
    logger.info("init_database(): schema sẵn sàng cho %s", settings.POSTGRES_DB)