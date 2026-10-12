from database.connection import get_connection


def apply_schema(connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            source TEXT NOT NULL,
            external_id TEXT,

            title TEXT NOT NULL,
            company TEXT,
            location TEXT,

            description TEXT NOT NULL,

            job_url TEXT NOT NULL UNIQUE,

            posted_date TEXT,
            employment_type TEXT,
            experience TEXT,
            remote INTEGER,

            status TEXT NOT NULL DEFAULT 'active',
            last_seen_at TEXT NOT NULL,

            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    _migrate_jobs(connection)
    connection.executescript(
        """
        CREATE INDEX IF NOT EXISTS idx_jobs_source
        ON jobs(source);

        CREATE INDEX IF NOT EXISTS idx_jobs_posted_date
        ON jobs(posted_date);

        CREATE INDEX IF NOT EXISTS idx_jobs_status
        ON jobs(status);
        """
    )


def _column_names(connection, table: str) -> set[str]:
    rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
    return {row[1] for row in rows}


def _migrate_jobs(connection) -> None:
    columns = _column_names(connection, "jobs")

    if "status" not in columns:
        connection.execute(
            """
            ALTER TABLE jobs
            ADD COLUMN status TEXT NOT NULL DEFAULT 'active'
            """
        )

    if "last_seen_at" not in columns:
        connection.execute(
            """
            ALTER TABLE jobs
            ADD COLUMN last_seen_at TEXT
            """
        )
        connection.execute(
            """
            UPDATE jobs
            SET last_seen_at = COALESCE(updated_at, created_at)
            WHERE last_seen_at IS NULL
            """
        )


def create_tables() -> None:
    connection = get_connection()
    connection.commit()
    connection.close()


if __name__ == "__main__":
    create_tables()
    print("Database schema created.")
