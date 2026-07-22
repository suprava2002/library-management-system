"""
Tests for Student CRUD ( /students/, /students/add/, /students/delete/<pk>/ ).
Each test uses a unique roll_number so tests can be re-run without clashing.
"""
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def unique_roll():
    return f"ROLL-{int(time.time() * 1000)}"


def add_student(driver, base_url, name, roll_number, email="", phone=""):
    driver.get(base_url + "/students/add/")
    # Explicit wait: same fix applied to add_book/issue_book_to_student —
    # the add-student page can render a beat slower on CI than locally.
    wait = WebDriverWait(driver, 15)
    wait.until(EC.presence_of_element_located((By.ID, "name"))).send_keys(name)
    driver.find_element(By.ID, "roll_number").send_keys(roll_number)
    if email:
        driver.find_element(By.ID, "email").send_keys(email)
    if phone:
        driver.find_element(By.ID, "phone").send_keys(phone)
    driver.find_element(By.CSS_SELECTOR, "button.btn-primary").click()


def test_student_list_page_loads(driver, base_url):
    driver.get(base_url + "/students/")
    assert "Students" in driver.title
    assert driver.find_element(By.CLASS_NAME, "data-table")


def test_add_student_success(driver, base_url):
    roll = unique_roll()
    add_student(driver, base_url, "Suprava Biswal", roll, "suprava@example.com", "9876543210")
    assert "/students/" in driver.current_url
    success_msg = driver.find_element(By.CLASS_NAME, "alert-success")
    assert "added successfully" in success_msg.text
    assert roll in driver.page_source


def test_student_search_by_roll_number(driver, base_url):
    roll = unique_roll()
    add_student(driver, base_url, "Search Test Student", roll)
    driver.get(base_url + f"/students/?q={roll}")
    rows = driver.find_elements(By.CSS_SELECTOR, ".data-table tbody tr")
    assert any(roll in row.text for row in rows)


def test_add_student_optional_fields_blank(driver, base_url):
    # email/phone are optional (blank=True) — should still succeed
    roll = unique_roll()
    add_student(driver, base_url, "No Contact Student", roll)
    assert "/students/" in driver.current_url
    assert driver.find_element(By.CLASS_NAME, "alert-success")


def test_add_student_required_field_validation(driver, base_url):
    driver.get(base_url + "/students/add/")
    driver.find_element(By.CSS_SELECTOR, "button.btn-primary").click()
    assert "/students/add/" in driver.current_url


def test_delete_student(driver, base_url):
    roll = unique_roll()
    add_student(driver, base_url, "Delete Me Student", roll)
    driver.get(base_url + "/students/")
    row = next(
        r for r in driver.find_elements(By.CSS_SELECTOR, ".data-table tbody tr")
        if roll in r.text
    )
    row.find_element(By.CSS_SELECTOR, "button.btn-danger").click()
    driver.switch_to.alert.accept()
    success_msg = driver.find_element(By.CLASS_NAME, "alert-success")
    assert "deleted" in success_msg.text.lower()
    assert roll not in driver.page_source
