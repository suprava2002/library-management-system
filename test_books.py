"""
Tests for Book CRUD ( /books/, /books/add/, /books/delete/<pk>/ ).
Each test creates its own unique ISBN so tests can be re-run without clashing.
"""
import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def unique_isbn():
    return f"ISBN-{int(time.time() * 1000)}"


def add_book(driver, base_url, title, author, isbn, category="Fiction", total_copies="3"):
    driver.get(base_url + "/books/add/")
    # Explicit wait: on a shared CI runner the add-book page can render a
    # beat slower than locally, so an implicit wait alone occasionally
    # isn't enough (same class of flakiness fixed in issue_book_to_student).
    wait = WebDriverWait(driver, 15)
    wait.until(EC.presence_of_element_located((By.ID, "title"))).send_keys(title)
    driver.find_element(By.ID, "author").send_keys(author)
    driver.find_element(By.ID, "isbn").send_keys(isbn)
    driver.find_element(By.ID, "category").send_keys(category)
    total = driver.find_element(By.ID, "total_copies")
    total.clear()
    total.send_keys(total_copies)
    driver.find_element(By.CSS_SELECTOR, "button.btn-primary").click()


def get_book_row_by_isbn(driver, isbn, timeout=15):
    """Waits for the books table to actually render before searching rows.
    Prevents StopIteration when /books/ hasn't finished loading yet."""
    wait = WebDriverWait(driver, timeout)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "data-table")))
    return next(
        r for r in driver.find_elements(By.CSS_SELECTOR, ".data-table tbody tr")
        if isbn in r.text
    )


def test_book_list_page_loads(driver, base_url):
    driver.get(base_url + "/books/")
    assert "Books" in driver.title
    assert driver.find_element(By.CLASS_NAME, "data-table")


def test_add_book_success(driver, base_url):
    isbn = unique_isbn()
    add_book(driver, base_url, "Automation Testing 101", "S. Biswal", isbn)
    # book_add redirects to book_list on success
    assert "/books/" in driver.current_url
    success_msg = driver.find_element(By.CLASS_NAME, "alert-success")
    assert "added successfully" in success_msg.text
    # New row should be visible in the table
    assert isbn in driver.page_source


def test_book_search_by_title(driver, base_url):
    isbn = unique_isbn()
    add_book(driver, base_url, "Selenium Deep Dive", "R. Kumar", isbn)
    driver.get(base_url + "/books/?q=Selenium Deep Dive")

    # Explicit wait for search results to render before asserting.
    wait = WebDriverWait(driver, 15)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".data-table tbody tr")))

    rows = driver.find_elements(By.CSS_SELECTOR, ".data-table tbody tr")
    assert any("Selenium Deep Dive" in row.text for row in rows)


def test_book_search_no_results_shows_empty_row(driver, base_url):
    driver.get(base_url + "/books/?q=NoSuchBookTitleXYZ123")
    empty_row = driver.find_element(By.CLASS_NAME, "empty-row")
    assert "No books found" in empty_row.text


def test_add_book_required_field_validation(driver, base_url):
    # Leaving required fields blank should not navigate away (HTML5 validation)
    driver.get(base_url + "/books/add/")
    driver.find_element(By.CSS_SELECTOR, "button.btn-primary").click()
    assert "/books/add/" in driver.current_url


def test_delete_book(driver, base_url):
    isbn = unique_isbn()
    add_book(driver, base_url, "Book To Delete", "Temp Author", isbn)
    driver.get(base_url + "/books/")
    row = get_book_row_by_isbn(driver, isbn)
    row.find_element(By.CSS_SELECTOR, "button.btn-danger").click()
    # Confirm JS alert (onsubmit="return confirm(...)")
    driver.switch_to.alert.accept()
    success_msg = driver.find_element(By.CLASS_NAME, "alert-success")
    assert "deleted" in success_msg.text.lower()
    assert isbn not in driver.page_source
