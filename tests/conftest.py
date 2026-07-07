"""Pytest fixtures for the resume-agentic-loop-mock test suite.

Sets up a temporary SQLite database before any test module imports database.py,
so tests that exercise database-backed tools work without a pre-existing DB.
"""

import os
import tempfile

# Set DB path before any test module imports database.py — it reads the env var
# at module load time to set database.DB_PATH.
_db_path = tempfile.mktemp(suffix=".db")
os.environ["RESUME_DB_PATH"] = _db_path


import pytest

import database


@pytest.fixture(autouse=True)
def _fresh_db():
    """Before each test, init a clean database and yield. Clean up after."""
    database.init_db()
    yield
    # Clean all tables between tests
    conn = database.get_connection()
    cur = conn.cursor()
    for table in [
        "user_profile",
        "experience_entries",
        "resume_bullets",
        "tool_inventory",
        "certifications",
        "job_answer_log",
        "runs",
    ]:
        cur.execute(f"DELETE FROM {table}")
    conn.commit()
    conn.close()


def pytest_unconfigure(config):
    """Clean up the temp database file after the test session ends."""
    if os.path.exists(_db_path):
        os.unlink(_db_path)
