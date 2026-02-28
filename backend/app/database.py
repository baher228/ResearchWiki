"""Lean PostgreSQL layer — just psycopg2, no ORM."""

import os
import psycopg2
import psycopg2.extras
import logging
from app.config import get_settings

logger = logging.getLogger(__name__)

# Register UUID adapter
psycopg2.extras.register_uuid()

# Path to AWS RDS root certificate
_CERT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "certs", "global-bundle.pem"))

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS papers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    original_filename TEXT,
    s3_pdf_key TEXT,
    s3_markdown_key TEXT,
    s3_html_key TEXT,
    s3_images_prefix TEXT,
    images_extracted INT DEFAULT 0,
    images_used INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
"""


def get_conn():
    """Get a new database connection. Uses SSL only for RDS."""
    settings = get_settings()
    kwargs = {"connect_timeout": 10}

    # Only use SSL when connecting to RDS
    if "rds.amazonaws.com" in settings.DATABASE_URL:
        kwargs["sslmode"] = "verify-full"
        kwargs["sslrootcert"] = _CERT_PATH

    return psycopg2.connect(settings.DATABASE_URL, **kwargs)


def init_db():
    """Create tables if they don't exist. Non-fatal on failure."""
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(_CREATE_TABLE)
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Database initialized — papers table ready")
    except Exception as e:
        logger.warning("Database init failed (server will still start): %s", e)


def insert_paper(title, original_filename, s3_pdf_key, s3_markdown_key,
                 s3_html_key, s3_images_prefix, images_extracted, images_used):
    """Insert a paper record and return its UUID."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO papers (title, original_filename, s3_pdf_key, s3_markdown_key,
                            s3_html_key, s3_images_prefix, images_extracted, images_used)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, created_at
    """, (title, original_filename, s3_pdf_key, s3_markdown_key,
          s3_html_key, s3_images_prefix, images_extracted, images_used))
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return str(row[0]), row[1].isoformat()


def get_all_papers():
    """Return all papers, newest first."""
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM papers ORDER BY created_at DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    # Convert UUIDs to strings
    for r in rows:
        r["id"] = str(r["id"])
        r["created_at"] = r["created_at"].isoformat()
    return rows


def get_paper_by_id(paper_id: str):
    """Return a single paper by UUID."""
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM papers WHERE id = %s", (paper_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        row["id"] = str(row["id"])
        row["created_at"] = row["created_at"].isoformat()
    return row
