"""
Shared pytest fixtures for the Library Management System test suite.
Place this file in the same folder as your test_*.py files —
pytest auto-discovers conftest.py, no import needed.
"""
import sqlite3
from pathlib import Path

import pytest
from selenium import webdriver


BASE_URL = "http://127.0.0.1:8000"


@pytest.fixture
def driver():
    """Opens a fresh Chrome browser before each test, closes it after."""
    drv = webdriver.Chrome()
    drv.implicitly_wait(5)
    drv.maximize_window()

    yield drv  # test runs here

    drv.quit()


@pytest.fixture
def base_url():
    """Change this if your Django dev server runs on a different port."""
    return BASE_URL


def find_db_path():
    """
    Looks for db.sqlite3 starting in the current folder and walking upward.
    Works whether pytest is run from the project root or from a
    tests/ subfolder, as long as manage.py + db.sqlite3 live together.
    """
    start = Path.cwd()
    for folder in [start, *start.parents]:
        candidate = folder / "db.sqlite3"
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "db.sqlite3 not found. Run 'python manage.py migrate' first, "
        "and run pytest from the Django project root."
    )


@pytest.fixture
def db_connection():
    """
    Direct SQLite connection to the Django project's database file.
    Read-only style checks are safe to run anytime; tests that INSERT
    clean up after themselves (see test_database.py).
    """
    conn = sqlite3.connect(find_db_path())
    conn.execute("PRAGMA foreign_keys = ON")  # SQLite needs this explicitly
    yield conn
    conn.close()
