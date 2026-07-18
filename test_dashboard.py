"""
Tests for the Dashboard page ( '/' -> views.dashboard ).
"""
from selenium.webdriver.common.by import By


def test_dashboard_loads(driver, base_url):
    driver.get(base_url + "/")
    assert "Dashboard" in driver.title


def test_dashboard_has_stat_cards(driver, base_url):
    driver.get(base_url + "/")
    stat_cards = driver.find_elements(By.CLASS_NAME, "stat-card")
    # Total Books, Total Students, Books Issued, Overdue
    assert len(stat_cards) == 4


def test_dashboard_navigation_links(driver, base_url):
    driver.get(base_url + "/")
    nav_links = driver.find_element(By.CLASS_NAME, "nav-links")
    assert nav_links.find_element(By.LINK_TEXT, "Books")
    assert nav_links.find_element(By.LINK_TEXT, "Students")
    assert nav_links.find_element(By.LINK_TEXT, "Issue / Return")


def test_dashboard_quick_action_links_navigate(driver, base_url):
    driver.get(base_url + "/")
    driver.find_element(By.LINK_TEXT, "+ Add Book").click()
    assert "/books/add/" in driver.current_url
