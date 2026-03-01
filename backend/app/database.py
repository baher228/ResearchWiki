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

_ALTER_PAPERS_TABLE = """
ALTER TABLE papers ADD COLUMN IF NOT EXISTS content_hash TEXT;
ALTER TABLE papers ADD COLUMN IF NOT EXISTS markdown TEXT;
"""

_CREATE_PAPERS_INDEXES = """
CREATE UNIQUE INDEX IF NOT EXISTS idx_papers_content_hash_unique
ON papers (content_hash)
WHERE content_hash IS NOT NULL AND content_hash <> '';
"""

_CREATE_LINKS_TABLE = """
CREATE TABLE IF NOT EXISTS paper_links (
    source_paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    target_paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    relation_type TEXT NOT NULL DEFAULT 'related_topic',
    score DOUBLE PRECISION NOT NULL DEFAULT 0,
    evidence TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (source_paper_id, target_paper_id, relation_type),
    CHECK (source_paper_id <> target_paper_id)
);
"""

_CREATE_LINKS_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_paper_links_source_score ON paper_links (source_paper_id, score DESC);
CREATE INDEX IF NOT EXISTS idx_paper_links_target ON paper_links (target_paper_id);
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
        cur.execute(_ALTER_PAPERS_TABLE)
        cur.execute(_CREATE_PAPERS_INDEXES)
        cur.execute(_CREATE_LINKS_TABLE)
        cur.execute(_CREATE_LINKS_INDEXES)
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Database initialized — papers and paper_links tables ready")
    except Exception as e:
        logger.warning("Database init failed (server will still start): %s", e)


def insert_paper(title, original_filename, s3_pdf_key, s3_markdown_key,
                 s3_html_key, s3_images_prefix, images_extracted, images_used,
                 content_hash: str = "", markdown: str = ""):
    """Insert a paper record and return its UUID."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO papers (title, original_filename, s3_pdf_key, s3_markdown_key,
                                                        s3_html_key, s3_images_prefix, images_extracted, images_used, content_hash, markdown)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
        RETURNING id, created_at
    """, (title, original_filename, s3_pdf_key, s3_markdown_key,
                    s3_html_key, s3_images_prefix, images_extracted, images_used, content_hash, markdown))
    row = cur.fetchone()
    if not row and content_hash:
        cur.execute("SELECT id, created_at FROM papers WHERE content_hash = %s", (content_hash,))
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


def get_all_filenames():
    """Return all (id, original_filename) pairs for deduplication checks."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, original_filename FROM papers")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [(str(r[0]), r[1]) for r in rows]


def get_paper_id_by_content_hash(content_hash: str) -> str | None:
    """Return paper ID for an exact content hash match."""
    if not content_hash:
        return None
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM papers WHERE content_hash = %s", (content_hash,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return str(row[0]) if row else None


def upsert_paper_link(source_paper_id: str, target_paper_id: str, relation_type: str,
                      score: float, evidence: str = ""):
    """Insert or update one directional link between two papers."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO paper_links (source_paper_id, target_paper_id, relation_type, score, evidence)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (source_paper_id, target_paper_id, relation_type)
        DO UPDATE SET
            score = EXCLUDED.score,
            evidence = EXCLUDED.evidence,
            created_at = NOW()
    """, (source_paper_id, target_paper_id, relation_type, score, evidence))
    conn.commit()
    cur.close()
    conn.close()


def insert_paper_links(source_paper_id: str, links: list[dict]):
    """Batch upsert links from one source paper to many targets."""
    if not links:
        return

    rows = []
    for link in links:
        target_id = link.get("id")
        relation_type = link.get("relation_type") or "related_topic"
        score = float(link.get("score") or 0)
        evidence = link.get("evidence") or ""
        if not target_id or target_id == source_paper_id:
            continue
        rows.append((source_paper_id, target_id, relation_type, score, evidence))

    if not rows:
        return

    conn = get_conn()
    cur = conn.cursor()
    cur.executemany("""
        INSERT INTO paper_links (source_paper_id, target_paper_id, relation_type, score, evidence)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (source_paper_id, target_paper_id, relation_type)
        DO UPDATE SET
            score = EXCLUDED.score,
            evidence = EXCLUDED.evidence,
            created_at = NOW()
    """, rows)
    conn.commit()
    cur.close()
    conn.close()


def get_related_papers(paper_id: str, limit: int = 5):
    """Return top related papers with score and relation metadata."""
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT
            p.id,
            p.title,
            p.original_filename,
            p.s3_html_key,
            p.s3_markdown_key,
            l.relation_type,
            l.score,
            l.evidence
        FROM paper_links l
        JOIN papers p ON p.id = l.target_paper_id
        WHERE l.source_paper_id = %s
        ORDER BY l.score DESC, p.created_at DESC
        LIMIT %s
    """, (paper_id, limit))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    for row in rows:
        row["id"] = str(row["id"])

    return rows


def delete_paper_by_id(paper_id: str) -> bool:
    """Delete one paper by UUID. Returns True if a row was removed."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM papers WHERE id = %s RETURNING id", (paper_id,))
    deleted = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return bool(deleted)


def delete_all_papers() -> int:
    """Delete all papers from the database. Returns the number of rows deleted."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM papers")
    deleted = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return deleted


def update_paper_title(paper_id: str, title: str) -> bool:
    """Update a paper title. Returns True if a row was updated."""
    if not title:
        return False
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE papers SET title = %s WHERE id = %s", (title, paper_id))
    updated = cur.rowcount > 0
    conn.commit()
    cur.close()
    conn.close()
    return updated


def update_paper_markdown(paper_id: str, markdown: str) -> bool:
    """Update cached markdown for a paper. Returns True if a row was updated."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE papers SET markdown = %s WHERE id = %s", (markdown, paper_id))
    updated = cur.rowcount > 0
    conn.commit()
    cur.close()
    conn.close()
    return updated
