"""
Database testing for the Library Management System — talks directly to
db.sqlite3, bypassing the UI entirely.

Django's default table names are <app_label>_<model_name>, so:
    Book        -> library_book
    Student     -> library_student
    IssueRecord -> library_issuerecord

Covers: schema checks, CRUD via raw SQL, unique constraints,
foreign key relationships, and data integrity.
"""
import time
import sqlite3
import pytest


def unique_isbn():
    return f"DB-ISBN-{int(time.time() * 1000)}"


def unique_roll():
    return f"DB-ROLL-{int(time.time() * 1000)}"


# ---------------------------------------------------------------------
# 1. Schema testing — confirm expected tables and columns exist
# ---------------------------------------------------------------------

def test_book_table_exists_with_expected_columns(db_connection):
    cursor = db_connection.cursor()
    cursor.execute("PRAGMA table_info(library_book)")
    columns = {row[1] for row in cursor.fetchall()}

    expected = {"id", "title", "author", "isbn", "category",
                "total_copies", "available_copies", "added_on"}
    assert expected.issubset(columns)


def test_student_table_exists_with_expected_columns(db_connection):
    cursor = db_connection.cursor()
    cursor.execute("PRAGMA table_info(library_student)")
    columns = {row[1] for row in cursor.fetchall()}

    expected = {"id", "name", "roll_number", "email", "phone", "joined_on"}
    assert expected.issubset(columns)


def test_issuerecord_table_exists_with_expected_columns(db_connection):
    cursor = db_connection.cursor()
    cursor.execute("PRAGMA table_info(library_issuerecord)")
    columns = {row[1] for row in cursor.fetchall()}

    expected = {"id", "issue_date", "due_date", "return_date",
                "status", "book_id", "student_id"}
    assert expected.issubset(columns)


# ---------------------------------------------------------------------
# 2. CRUD testing — insert, read, update, delete directly via SQL
# ---------------------------------------------------------------------

def test_insert_and_read_book(db_connection):
    isbn = unique_isbn()
    cursor = db_connection.cursor()
    cursor.execute(
        "INSERT INTO library_book (title, author, isbn, category, "
        "total_copies, available_copies, added_on) VALUES (?, ?, ?, ?, ?, ?, date('now'))",
        ("DB Test Book", "Test Author", isbn, "Fiction", 3, 3)
    )
    db_connection.commit()

    cursor.execute("SELECT title, available_copies FROM library_book WHERE isbn = ?", (isbn,))
    row = cursor.fetchone()

    assert row is not None
    assert row[0] == "DB Test Book"
    assert row[1] == 3

    # cleanup
    cursor.execute("DELETE FROM library_book WHERE isbn = ?", (isbn,))
    db_connection.commit()


def test_update_available_copies(db_connection):
    isbn = unique_isbn()
    cursor = db_connection.cursor()
    cursor.execute(
        "INSERT INTO library_book (title, author, isbn, category, "
        "total_copies, available_copies, added_on) VALUES (?, ?, ?, ?, ?, ?, date('now'))",
        ("Update Test Book", "Author", isbn, "Fiction", 2, 2)
    )
    db_connection.commit()

    # simulate a book being issued — available_copies drops by 1
    cursor.execute(
        "UPDATE library_book SET available_copies = available_copies - 1 WHERE isbn = ?",
        (isbn,)
    )
    db_connection.commit()

    cursor.execute("SELECT available_copies FROM library_book WHERE isbn = ?", (isbn,))
    assert cursor.fetchone()[0] == 1

    cursor.execute("DELETE FROM library_book WHERE isbn = ?", (isbn,))
    db_connection.commit()


def test_delete_book(db_connection):
    isbn = unique_isbn()
    cursor = db_connection.cursor()
    cursor.execute(
        "INSERT INTO library_book (title, author, isbn, category, "
        "total_copies, available_copies, added_on) VALUES (?, ?, ?, ?, ?, ?, date('now'))",
        ("Delete Test Book", "Author", isbn, "Fiction", 1, 1)
    )
    db_connection.commit()

    cursor.execute("DELETE FROM library_book WHERE isbn = ?", (isbn,))
    db_connection.commit()

    cursor.execute("SELECT * FROM library_book WHERE isbn = ?", (isbn,))
    assert cursor.fetchone() is None


# ---------------------------------------------------------------------
# 3. Data integrity — unique constraints
# ---------------------------------------------------------------------

def test_isbn_uniqueness_constraint(db_connection):
    isbn = unique_isbn()
    cursor = db_connection.cursor()
    cursor.execute(
        "INSERT INTO library_book (title, author, isbn, category, "
        "total_copies, available_copies, added_on) VALUES (?, ?, ?, ?, ?, ?, date('now'))",
        ("First Copy", "Author A", isbn, "Fiction", 1, 1)
    )
    db_connection.commit()

    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            "INSERT INTO library_book (title, author, isbn, category, "
            "total_copies, available_copies, added_on) VALUES (?, ?, ?, ?, ?, ?, date('now'))",
            ("Duplicate ISBN Book", "Author B", isbn, "Non-fiction", 1, 1)
        )
        db_connection.commit()

    db_connection.rollback()
    cursor.execute("DELETE FROM library_book WHERE isbn = ?", (isbn,))
    db_connection.commit()


def test_roll_number_uniqueness_constraint(db_connection):
    roll = unique_roll()
    cursor = db_connection.cursor()
    cursor.execute(
        "INSERT INTO library_student (name, roll_number, email, phone, joined_on) "
        "VALUES (?, ?, ?, ?, date('now'))",
        ("First Student", roll, "first@test.com", "9999999999")
    )
    db_connection.commit()

    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            "INSERT INTO library_student (name, roll_number, email, phone, joined_on) "
            "VALUES (?, ?, ?, ?, date('now'))",
            ("Duplicate Roll Student", roll, "second@test.com", "8888888888")
        )
        db_connection.commit()

    db_connection.rollback()
    cursor.execute("DELETE FROM library_student WHERE roll_number = ?", (roll,))
    db_connection.commit()


# ---------------------------------------------------------------------
# 4. Foreign key relationships
# ---------------------------------------------------------------------

def test_issuerecord_foreign_keys_point_to_valid_rows(db_connection):
    """Every issue record must reference a book and student that actually exist."""
    cursor = db_connection.cursor()
    cursor.execute("""
        SELECT ir.id FROM library_issuerecord ir
        LEFT JOIN library_book b ON ir.book_id = b.id
        WHERE b.id IS NULL
    """)
    orphaned_book_refs = cursor.fetchall()
    assert len(orphaned_book_refs) == 0, "Found issue records pointing to a deleted book"

    cursor.execute("""
        SELECT ir.id FROM library_issuerecord ir
        LEFT JOIN library_student s ON ir.student_id = s.id
        WHERE s.id IS NULL
    """)
    orphaned_student_refs = cursor.fetchall()
    assert len(orphaned_student_refs) == 0, "Found issue records pointing to a deleted student"


def test_raw_sql_delete_is_blocked_when_issue_records_exist(db_connection):
    """
    models.py defines on_delete=CASCADE for book -> issue_records, but that
    cascade is implemented by Django's ORM in Python (it deletes the child
    rows itself before deleting the parent) — it is NOT written into the
    SQLite schema as an 'ON DELETE CASCADE' clause. So a raw SQL DELETE
    that bypasses Django correctly gets blocked by SQLite's own foreign
    key enforcement. This test confirms that protection is in place at
    the database level, independent of the application code.
    """
    isbn = unique_isbn()
    roll = unique_roll()
    cursor = db_connection.cursor()

    cursor.execute(
        "INSERT INTO library_book (title, author, isbn, category, "
        "total_copies, available_copies, added_on) VALUES (?, ?, ?, ?, ?, ?, date('now'))",
        ("Cascade Test Book", "Author", isbn, "Fiction", 1, 1)
    )
    cursor.execute(
        "INSERT INTO library_student (name, roll_number, email, phone, joined_on) "
        "VALUES (?, ?, ?, ?, date('now'))",
        ("Cascade Test Student", roll, "cascade@test.com", "7777777777")
    )
    db_connection.commit()

    book_id = cursor.execute("SELECT id FROM library_book WHERE isbn = ?", (isbn,)).fetchone()[0]
    student_id = cursor.execute("SELECT id FROM library_student WHERE roll_number = ?", (roll,)).fetchone()[0]

    cursor.execute(
        "INSERT INTO library_issuerecord (issue_date, due_date, return_date, status, book_id, student_id) "
        "VALUES (date('now'), date('now', '+14 days'), NULL, 'ISSUED', ?, ?)",
        (book_id, student_id)
    )
    db_connection.commit()

    # a direct SQL delete (no Django ORM in between) must be rejected —
    # the DB-level foreign key constraint protects against orphan records
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("DELETE FROM library_book WHERE id = ?", (book_id,))
        db_connection.commit()
    db_connection.rollback()

    # book should still be there, untouched
    cursor.execute("SELECT * FROM library_book WHERE id = ?", (book_id,))
    assert cursor.fetchone() is not None

    # cleanup — delete child row first, then the parents
    cursor.execute("DELETE FROM library_issuerecord WHERE book_id = ?", (book_id,))
    cursor.execute("DELETE FROM library_book WHERE id = ?", (book_id,))
    cursor.execute("DELETE FROM library_student WHERE id = ?", (student_id,))
    db_connection.commit()


# ---------------------------------------------------------------------
# 5. Business-rule level integrity checks
# ---------------------------------------------------------------------

def test_available_copies_never_exceeds_total_copies(db_connection):
    cursor = db_connection.cursor()
    cursor.execute(
        "SELECT title, available_copies, total_copies FROM library_book "
        "WHERE available_copies > total_copies"
    )
    violations = cursor.fetchall()
    assert violations == [], f"Books with available > total copies: {violations}"


def test_available_copies_never_negative(db_connection):
    cursor = db_connection.cursor()
    cursor.execute("SELECT title, available_copies FROM library_book WHERE available_copies < 0")
    violations = cursor.fetchall()
    assert violations == [], f"Books with negative available copies: {violations}"


def test_returned_records_have_a_return_date(db_connection):
    cursor = db_connection.cursor()
    cursor.execute(
        "SELECT id FROM library_issuerecord WHERE status = 'RETURNED' AND return_date IS NULL"
    )
    violations = cursor.fetchall()
    assert violations == [], "Found RETURNED records with no return_date set"