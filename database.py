"""
SQLite state manager for the resume agentic loop.

This module owns all database interaction. The agentic loop and tools never
write raw SQL themselves; they call functions defined here.

7 tables:
  - user_profile
  - experience_entries
  - resume_bullets
  - tool_inventory
  - certifications
  - job_answer_log
  - runs

All seed data uses obviously fictional characters.
"""

from __future__ import annotations

import json
import os
import sqlite3
from typing import Any

DB_PATH = os.environ.get("RESUME_DB_PATH", "experience_kb.db")


def get_connection() -> sqlite3.Connection:
    """Return a sqlite connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create all 7 tables if they do not exist."""
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            email TEXT,
            phone TEXT,
            location TEXT,
            linkedin TEXT,
            portfolio TEXT,
            headline TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS experience_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            title TEXT NOT NULL,
            location TEXT,
            date_range TEXT,
            category TEXT NOT NULL,
            details TEXT NOT NULL,
            source TEXT DEFAULT 'user_input',
            source_confirmed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS resume_bullets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experience_id INTEGER,
            company TEXT NOT NULL,
            title TEXT NOT NULL,
            bullet_text TEXT NOT NULL,
            source TEXT DEFAULT 'generated',
            source_confirmed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (experience_id) REFERENCES experience_entries(id)
        );

        CREATE TABLE IF NOT EXISTS tool_inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool_name TEXT NOT NULL,
            category TEXT,
            proficiency TEXT,
            notes TEXT,
            source_confirmed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS certifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cert_name TEXT NOT NULL,
            issuer TEXT,
            date_obtained TEXT,
            source_confirmed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS job_answer_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_title TEXT,
            company TEXT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_title TEXT,
            company TEXT,
            source_url TEXT,
            raw_job_description TEXT,
            extracted_requirements TEXT,
            matched_experience TEXT,
            generated_resume TEXT,
            status TEXT DEFAULT 'created',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    conn.commit()
    conn.close()


def seed_sample_data() -> str:
    """Insert obviously fictional sample data.

    Returns a short summary string describing what was inserted.
    """
    conn = get_connection()
    cur = conn.cursor()

    # Only seed if DB appears empty
    existing = cur.execute("SELECT COUNT(*) FROM user_profile").fetchone()[0]
    if existing:
        conn.close()
        return "Database already has data. Skipping seed."

    # Fictional user profile
    cur.execute(
        """INSERT INTO user_profile
           (full_name, email, phone, location, linkedin, portfolio, headline)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            "Alex Chen",
            "alex.chen@example.com",
            "555-0100",
            "Remote",
            "https://linkedin.com/in/alex-example",
            "https://github.com/alex-example",
            "Security Automation Engineer",
        ),
    )

    # Fictional experience entries
    experience_seed = [
        (
            "Acme Defense Systems",
            "Senior Security Automation Engineer",
            "Remote",
            "2021-01 to 2024-06",
            "security_automation",
            "Built Python automation to triage vulnerability exports and prioritize high-risk findings across cloud workloads. Reduced manual review time by roughly 40% by standardizing evidence collection.",
            "user_input",
            1,
        ),
        (
            "Northwind Logistics",
            "Cloud Security Engineer",
            "Denver, CO",
            "2018-03 to 2020-12",
            "cloud_security",
            "Hardened GKE and AWS workloads using policy-as-code and configuration drift tooling. Authored runbooks for incident response and vulnerability handling.",
            "user_input",
            1,
        ),
        (
            "Globex Consulting",
            "Security Analyst",
            "Austin, TX",
            "2016-06 to 2018-02",
            "analysis",
            "Investigated phishing and endpoint alerts in a SIEM. Wrote detection content and tuned rules to reduce false positives.",
            "user_input",
            1,
        ),
    ]
    for row in experience_seed:
        cur.execute(
            """INSERT INTO experience_entries
               (company, title, location, date_range, category, details, source, source_confirmed)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            row,
        )

    # Fictional resume bullets
    bullet_seed = [
        (
            1,
            "Acme Defense Systems",
            "Senior Security Automation Engineer",
            "Automated vulnerability export ingestion from InsightVM, reducing time-to-triage from 3 days to under 4 hours.",
            "user_input",
            1,
        ),
        (
            1,
            "Acme Defense Systems",
            "Senior Security Automation Engineer",
            "Designed Python workflows that correlated cloud asset inventory with CVE feeds, producing prioritized remediation queues.",
            "user_input",
            1,
        ),
        (
            2,
            "Northwind Logistics",
            "Cloud Security Engineer",
            "Implemented policy-as-code controls across GKE clusters using OPA and admission controllers.",
            "user_input",
            1,
        ),
        (
            2,
            "Northwind Logistics",
            "Cloud Security Engineer",
            "Tuned SIEM detection rules to cut phishing false positives by 30%.",
            "user_input",
            1,
        ),
        (
            3,
            "Globex Consulting",
            "Security Analyst",
            "Investigated 200+ phishing reports monthly and produced structured case notes for escalations.",
            "user_input",
            1,
        ),
    ]
    for row in bullet_seed:
        cur.execute(
            """INSERT INTO resume_bullets
               (experience_id, company, title, bullet_text, source, source_confirmed)
               VALUES (?, ?, ?, ?, ?, ?)""",
            row,
        )

    # Fictional tool inventory
    tool_seed = [
        ("Python", "programming", "advanced", "Primary automation language", 1),
        ("GKE", "cloud_infrastructure", "intermediate", "Kubernetes security hardening", 1),
        ("AWS", "cloud_infrastructure", "intermediate", "IAM, Config, GuardDuty", 1),
        ("Splunk", "siem", "intermediate", "Detection rule tuning", 1),
        ("InsightVM", "vulnerability_management", "intermediate", "Export automation", 1),
        ("OPA", "policy_as_code", "intermediate", "Admission control policy", 1),
        ("Terraform", "iac", "intermediate", "Security baseline modules", 1),
    ]
    for row in tool_seed:
        cur.execute(
            """INSERT INTO tool_inventory
               (tool_name, category, proficiency, notes, source_confirmed)
               VALUES (?, ?, ?, ?, ?)""",
            row,
        )

    # Fictional certification
    cert_seed = [
        ("CISSP", "Example Cert Board", "2022", 1),
        ("AWS Security Specialty", "Amazon", "2021", 1),
    ]
    for row in cert_seed:
        cur.execute(
            """INSERT INTO certifications
               (cert_name, issuer, date_obtained, source_confirmed)
               VALUES (?, ?, ?, ?)""",
            row,
        )

    conn.commit()
    conn.close()
    return "Seeded fictional sample data: 1 profile, 3 experience entries, 5 bullets, 7 tools, 2 certs."


def query_experience(query: str, category: str | None = None) -> list[dict[str, Any]]:
    """Search experience entries by keyword and optional category."""
    conn = get_connection()
    cur = conn.cursor()
    like = f"%{query.lower()}%"
    if category:
        rows = cur.execute(
            """SELECT * FROM experience_entries
               WHERE (LOWER(company) LIKE ? OR LOWER(title) LIKE ?
                      OR LOWER(details) LIKE ?)
               AND category = ?
               ORDER BY id DESC""",
            (like, like, like, category),
        ).fetchall()
    else:
        rows = cur.execute(
            """SELECT * FROM experience_entries
               WHERE LOWER(company) LIKE ? OR LOWER(title) LIKE ?
                      OR LOWER(details) LIKE ?
               ORDER BY id DESC""",
            (like, like, like),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def query_bullets(company: str | None = None, keyword: str | None = None) -> list[dict[str, Any]]:
    """Search resume bullets by optional company and keyword."""
    conn = get_connection()
    cur = conn.cursor()
    conditions = []
    params: list[Any] = []
    if company:
        conditions.append("LOWER(company) LIKE ?")
        params.append(f"%{company.lower()}%")
    if keyword:
        conditions.append("LOWER(bullet_text) LIKE ?")
        params.append(f"%{keyword.lower()}%")
    where = " AND ".join(conditions) if conditions else "1=1"
    rows = cur.execute(
        f"SELECT * FROM resume_bullets WHERE {where} ORDER BY id DESC",  # noqa: S608
        params,
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def query_tools(tool_name: str) -> list[dict[str, Any]]:
    """Search tool inventory by name."""
    conn = get_connection()
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT * FROM tool_inventory WHERE LOWER(tool_name) LIKE ? ORDER BY id DESC",
        (f"%{tool_name.lower()}%",),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def store_experience(
    company: str,
    title: str,
    date_range: str,
    category: str,
    details: str,
) -> int:
    """Insert a new experience entry. Returns the new row ID."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO experience_entries
           (company, title, date_range, category, details)
           VALUES (?, ?, ?, ?, ?)""",
        (company, title, date_range, category, details),
    )
    conn.commit()
    row_id = cur.lastrowid
    conn.close()
    return int(row_id)


def store_bullet(
    experience_id: int | None,
    company: str,
    title: str,
    bullet_text: str,
) -> int:
    """Insert a new resume bullet. Returns the new row ID."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO resume_bullets
           (experience_id, company, title, bullet_text)
           VALUES (?, ?, ?, ?)""",
        (experience_id, company, title, bullet_text),
    )
    conn.commit()
    row_id = cur.lastrowid
    conn.close()
    return int(row_id)


def store_answer(job_title: str, company: str, question: str, answer: str) -> int:
    """Store a user's answer to a gap question. Returns the new row ID."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO job_answer_log
           (job_title, company, question, answer)
           VALUES (?, ?, ?, ?)""",
        (job_title, company, question, answer),
    )
    conn.commit()
    row_id = cur.lastrowid
    conn.close()
    return int(row_id)


def get_user_profile() -> dict[str, Any] | None:
    """Return the first (single) user profile row, or None."""
    conn = get_connection()
    cur = conn.cursor()
    row = cur.execute("SELECT * FROM user_profile ORDER BY id LIMIT 1").fetchone()
    conn.close()
    return dict(row) if row else None


def set_user_profile(profile: dict[str, Any]) -> None:
    """Upsert the single user profile row."""
    conn = get_connection()
    cur = conn.cursor()
    existing = cur.execute("SELECT id FROM user_profile ORDER BY id LIMIT 1").fetchone()
    if existing:
        cur.execute(
            """UPDATE user_profile SET
               full_name=?, email=?, phone=?, location=?,
               linkedin=?, portfolio=?, headline=?, updated_at=CURRENT_TIMESTAMP
               WHERE id=?""",
            (
                profile.get("full_name", ""),
                profile.get("email", ""),
                profile.get("phone", ""),
                profile.get("location", ""),
                profile.get("linkedin", ""),
                profile.get("portfolio", ""),
                profile.get("headline", ""),
                existing["id"],
            ),
        )
    else:
        cur.execute(
            """INSERT INTO user_profile
               (full_name, email, phone, location, linkedin, portfolio, headline)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                profile.get("full_name", ""),
                profile.get("email", ""),
                profile.get("phone", ""),
                profile.get("location", ""),
                profile.get("linkedin", ""),
                profile.get("portfolio", ""),
                profile.get("headline", ""),
            ),
        )
    conn.commit()
    conn.close()


def get_certifications() -> list[dict[str, Any]]:
    """Return all certifications."""
    conn = get_connection()
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM certifications ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_tools() -> list[dict[str, Any]]:
    """Return all tool inventory rows."""
    conn = get_connection()
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM tool_inventory ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_run(job_title: str, company: str, source_url: str, raw_job_description: str) -> int:
    """Create a new run record. Returns the run ID."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO runs
           (job_title, company, source_url, raw_job_description, status)
           VALUES (?, ?, ?, ?, 'running')""",
        (job_title, company, source_url, raw_job_description),
    )
    conn.commit()
    row_id = cur.lastrowid
    conn.close()
    return int(row_id)


def update_run(
    run_id: int,
    extracted_requirements: str | None = None,
    matched_experience: str | None = None,
    generated_resume: str | None = None,
    status: str | None = None,
) -> None:
    """Update a run record with results."""
    conn = get_connection()
    cur = conn.cursor()
    updates = []
    params: list[Any] = []
    if extracted_requirements is not None:
        updates.append("extracted_requirements = ?")
        params.append(extracted_requirements)
    if matched_experience is not None:
        updates.append("matched_experience = ?")
        params.append(matched_experience)
    if generated_resume is not None:
        updates.append("generated_resume = ?")
        params.append(generated_resume)
    if status is not None:
        updates.append("status = ?")
        params.append(status)
    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(run_id)
    cur.execute(
        f"UPDATE runs SET {', '.join(updates)} WHERE id = ?",  # noqa: S608
        params,
    )
    conn.commit()
    conn.close()


def get_latest_run() -> dict[str, Any] | None:
    """Return the most recent run record."""
    conn = get_connection()
    cur = conn.cursor()
    row = cur.execute("SELECT * FROM runs ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    return dict(row) if row else None


def get_db_summary() -> dict[str, int]:
    """Return row counts for each table."""
    conn = get_connection()
    cur = conn.cursor()
    tables = [
        "user_profile",
        "experience_entries",
        "resume_bullets",
        "tool_inventory",
        "certifications",
        "job_answer_log",
        "runs",
    ]
    summary: dict[str, int] = {}
    for table in tables:
        count = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]  # noqa: S608
        summary[table] = int(count)
    conn.close()
    return summary
