# Library Management System — Selenium + pytest test suite

Tests for the Django Library Management System project (dashboard, books,
students, issue/return flow).

## Setup

1. Copy this whole `library_tests` folder next to your Django project
   (or anywhere on disk — it only needs the server URL, not the source).
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the Django server in another terminal:
   ```bash
   python manage.py runserver
   ```
   By default tests expect `http://127.0.0.1:8000`. Change `BASE_URL` in
   `conftest.py` if your server runs elsewhere.

## Run the tests

```bash
pytest -v
```

Run a single file:
```bash
pytest test_books.py -v
```

Run a single test:
```bash
pytest test_books.py::test_add_book_success -v
```

Generate an HTML report:
```bash
pip install pytest-html
pytest --html=report.html
```

## Files

| File | Covers |
|---|---|
| `conftest.py` | Shared `driver` and `base_url` fixtures |
| `test_dashboard.py` | Dashboard stats, nav links, quick actions |
| `test_books.py` | Book list, search, add, validation, delete |
| `test_students.py` | Student list, search, add, validation, delete |
| `test_issues.py` | Issue a book, return a book, copy counts, status filters |

## Notes

- Each test creates its own book/student with a timestamp-based unique
  ISBN / roll number, so the suite can be re-run repeatedly without
  clashing with existing data or needing a database reset.
- `test_issues.py` imports helper functions (`add_book`, `add_student`)
  from `test_books.py` / `test_students.py` to set up data — keep all
  four test files in the same folder.
- Delete actions trigger a native JS `confirm()` dialog
  (`onsubmit="return confirm(...)"`) — tests handle this with
  `driver.switch_to.alert.accept()`.
