"""
Tests for Issue / Return flow ( /issues/, /issues/issue/, /issues/return/<pk>/ ).
Reuses the add_book / add_student helpers so each test starts with
a fresh book + student pair (avoids clashing with existing data).

IMPORTANT:
- Book titles and student names are suffixed with a unique timestamp tag
  (not just ISBN/roll number) so repeated suite runs never collide on
  title+name text matching in the issues table.
- issue_book_to_student uses an explicit WebDriverWait before interacting
  with the form. On a shared CI runner the Django dev server can respond
  a little slower than locally, and implicit waits alone were occasionally
  not enough, causing a flaky NoSuchElementException on the "book" select.
- get_book_row_by_isbn applies the same explicit-wait pattern before
  looking up a row on /books/, to avoid a StopIteration when the redirect
  hasn't finished rendering the table yet.
"""
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from test_books import add_book, unique_isbn, get_book_row_by_isbn
from test_students import add_student, unique_roll


def unique_tag():
    return str(int(time.time() * 1000))


def issue_book_to_student(driver, base_url, book_title, student_name):
    driver.get(base_url + "/issues/issue/")
    wait = WebDriverWait(driver, 15)
    book_select_el = wait.until(EC.presence_of_element_located((By.ID, "book")))
    student_select_el = wait.until(EC.presence_of_element_located((By.ID, "student")))
    book_select = Select(book_select_el)
    student_select = Select(student_select_el)

    # Options are rendered as "<title> (<n> available)" / "<name> (<roll>)"
    for option in book_select.options:
        if option.text.startswith(book_title):
            book_select.select_by_visible_text(option.text)
            break
    for option in student_select.options:
        if option.text.startswith(student_name):
            student_select.select_by_visible_text(option.text)
            break

    driver.find_element(By.CSS_SELECTOR, "button.btn-primary").click()


def get_latest_row(driver, title, student_name):
    """Rows are ordered by -issue_date (date-only), so same-day ties aren't
    guaranteed newest-first. Titles/names here are already unique per test
    run, but we still take the LAST DOM match as a safety net."""
    wait = WebDriverWait(driver, 15)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "data-table")))
    rows = [
        r for r in driver.find_elements(By.CSS_SELECTOR, ".data-table tbody tr")
        if title in r.text and student_name in r.text
    ]
    return rows[-1]


def test_issue_list_page_loads(driver, base_url):
    driver.get(base_url + "/issues/")
    assert "Issue" in driver.title
    assert driver.find_element(By.CLASS_NAME, "data-table")


def test_issue_book_success(driver, base_url):
    tag = unique_tag()
    isbn = unique_isbn()
    roll = unique_roll()
    title = f"Clean Code {tag}"
    student_name = f"Issue Test Student {tag}"

    add_book(driver, base_url, title, "Robert Martin", isbn, total_copies="2")
    add_student(driver, base_url, student_name, roll)
    issue_book_to_student(driver, base_url, title, student_name)

    assert "/issues/" in driver.current_url
    success_msg = driver.find_element(By.CLASS_NAME, "alert-success")
    assert "issued to" in success_msg.text

    row = get_latest_row(driver, title, student_name)
    assert "ISSUED" in row.text


def test_issued_book_available_copies_decrease(driver, base_url):
    tag = unique_tag()
    isbn = unique_isbn()
    roll = unique_roll()
    title = f"Only One Copy {tag}"
    student_name = f"Copy Check Student {tag}"

    add_book(driver, base_url, title, "Some Author", isbn, total_copies="1")
    add_student(driver, base_url, student_name, roll)
    issue_book_to_student(driver, base_url, title, student_name)

    driver.get(base_url + "/books/")
    row = get_book_row_by_isbn(driver, isbn)
    assert "0 / 1" in row.text


def test_return_book_updates_status(driver, base_url):
    tag = unique_tag()
    isbn = unique_isbn()
    roll = unique_roll()
    title = f"Return Flow Book {tag}"
    student_name = f"Return Test Student {tag}"

    add_book(driver, base_url, title, "Some Author", isbn, total_copies="1")
    add_student(driver, base_url, student_name, roll)
    issue_book_to_student(driver, base_url, title, student_name)

    driver.get(base_url + "/issues/")
    row = get_latest_row(driver, title, student_name)
    row.find_element(By.CSS_SELECTOR, "button.btn-secondary").click()

    success_msg = driver.find_element(By.CLASS_NAME, "alert-success")
    assert "returned by" in success_msg.text

    driver.get(base_url + "/issues/")
    row = get_latest_row(driver, title, student_name)
    assert "RETURNED" in row.text


def test_returned_book_copies_restored(driver, base_url):
    tag = unique_tag()
    isbn = unique_isbn()
    roll = unique_roll()
    title = f"Restore Copies Book {tag}"
    student_name = f"Restore Test Student {tag}"

    add_book(driver, base_url, title, "Some Author", isbn, total_copies="1")
    add_student(driver, base_url, student_name, roll)
    issue_book_to_student(driver, base_url, title, student_name)

    driver.get(base_url + "/issues/")
    row = get_latest_row(driver, title, student_name)
    row.find_element(By.CSS_SELECTOR, "button.btn-secondary").click()

    driver.get(base_url + "/books/")
    row = get_book_row_by_isbn(driver, isbn)
    assert "1 / 1" in row.text


def test_issue_list_filter_tabs(driver, base_url):
    driver.get(base_url + "/issues/?status=ISSUED")
    active_tab = driver.find_element(By.CSS_SELECTOR, ".filter-tabs a.active")
    assert active_tab.text == "Issued"

    driver.get(base_url + "/issues/?status=RETURNED")
    active_tab = driver.find_element(By.CSS_SELECTOR, ".filter-tabs a.active")
    assert active_tab.text == "Returned"
