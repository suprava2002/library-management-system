"""
Shared pytest fixtures for the Library Management System test suite.
Place this file in the same folder as your test_*.py files —
pytest auto-discovers conftest.py, no import needed.
"""
import os
import sqlite3
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


BASE_URL = os.environ.get("TEST_BASE_URL", "http://127.0.0.1:8000")
IS_CI = bool(os.environ.get("CI")) or os.environ.get("HEADLESS", "").lower() == "true"


@pytest.fixture
def driver():
    """
    Opens Chrome before each test, closes it after.
    Runs headless automatically on CI (GitHub Actions sets CI=true),
    or if you set HEADLESS=true yourself locally.
    """
    options = Options()

    # If the workflow captured an exact Chrome binary path, use it directly —
    # this avoids "session not created: Chrome instance exited abnormally"
    # caused by Selenium Manager picking the wrong / a missing binary.
    chrome_binary = os.environ.get("CHROME_BINARY")
    if chrome_binary:
        options.binary_location = chrome_binary

    if IS_CI:
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--window-size=1920,1080")

    drv = webdriver.Chrome(options=options)
    drv.implicitly_wait(5)
    if not IS_CI:
        drv.maximize_window()

    yield drv  # test runs here

    drv.quit()


@pytest.fixture
def base_url():
    """Change TEST_BASE_URL env var if your Django dev server runs elsewhere."""
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
