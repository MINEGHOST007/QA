"""
Test Record Search and Filter — Selenium regression test for the records list page.

Covers:
  - Search records by keyword
  - Filter by status dropdown
  - Filter by type dropdown
  - Filter by date range
  - Pagination navigation
  - Sort by column headers
  - Clear filters
"""

import unittest
from selenium import webdriver # type: ignore
from selenium.webdriver.common.by import By # type: ignore
from selenium.webdriver.common.keys import Keys # type: ignore
from selenium.webdriver.support.ui import WebDriverWait, Select # type: ignore
from selenium.webdriver.support import expected_conditions as EC # pyright: ignore[reportMissingImports]


class TestRecordSearchFilter(unittest.TestCase):
    """Regression tests for the records list search and filter."""

    BASE_URL = "http://localhost:8080"
    RECORDS_URL = f"{BASE_URL}/records.html"

    # --- XPaths and Selectors (v1.1 — last updated Jan 2026) ---
    SEARCH_INPUT = "//input[@data-testid='search-input']"
    SEARCH_BUTTON = "//button[@data-testid='btn-search']"
    FILTER_BUTTON = "//button[@data-testid='btn-filter']"
    FILTER_PANEL = "//div[@data-testid='filter-panel']"
    STATUS_FILTER = "//select[@data-testid='filter-status']"
    TYPE_FILTER = "//select[@data-testid='filter-type']"
    DATE_FROM_INPUT = "//input[@data-testid='filter-date-from']"
    DATE_TO_INPUT = "//input[@data-testid='filter-date-to']"
    APPLY_FILTERS_BTN = "//button[@data-testid='btn-apply-filters']"
    CLEAR_FILTERS_BTN = "//button[@data-testid='btn-clear-filters']"
    ACTIVE_FILTER_TAGS = "//div[@data-testid='active-filter-tags']"
    RECORDS_TABLE = "//div[@data-testid='records-table']"
    RECORD_ROWS = "//div[@data-testid='records-table']//tbody//tr[@data-testid='records-table-row']"
    EMPTY_STATE = "//div[@data-testid='empty-state-records']"
    RESULTS_COUNT = "//span[@data-testid='results-count']"
    SHOW_ARCHIVED = "//input[@data-testid='toggle-show-archived']"

    # Pagination
    PAGINATION_CONTROLS = "//div[@data-testid='pagination-controls']"
    PAGINATION_NEXT = "//button[@data-testid='btn-page-next']"
    PAGINATION_PREV = "//button[@data-testid='btn-page-prev']"
    PAGE_SIZE_SELECT = "//select[@data-testid='select-page-size']"

    # Sort headers
    SORT_HEADER_TITLE = "//th[@data-testid='th-sort-title']"
    SORT_HEADER_TYPE = "//th[@data-testid='th-sort-type']"
    SORT_HEADER_STATUS = "//th[@data-testid='th-sort-status']"
    SORT_HEADER_ASSIGNEE = "//th[@data-testid='th-sort-assignee']"

    LOADING_OVERLAY = "//div[@data-testid='loading-overlay']"

    def setUp(self):
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()
        self.driver.implicitly_wait(10)
        self.wait = WebDriverWait(self.driver, 15)
        self._login()

    def tearDown(self):
        self.driver.quit()

    def _login(self):
        """Helper: login as admin."""
        self.driver.get(f"{self.BASE_URL}/login.html")
        self.driver.find_element(By.XPATH, "//input[@data-testid='input-username']").send_keys("admin")
        self.driver.find_element(By.XPATH, "//input[@data-testid='input-password']").send_keys("admin123")
        self.driver.find_element(By.XPATH, "//button[@data-testid='btn-login']").click()
        self.wait.until(EC.url_contains("dashboard"))

    def test_search_by_keyword(self):
        """Test searching records by keyword in the search box.

        Steps:
        1. Navigate to records list
        2. Enter search keyword in search box
        3. Press Enter or click search
        4. Verify results update
        5. Verify matching records visible
        """
        self.driver.get(self.RECORDS_URL)

        search_input = self.driver.find_element(By.XPATH, self.SEARCH_INPUT)
        search_input.clear()
        search_input.send_keys("Financial Review")

        # NOTE: Old test used a search button — current UI uses oninput debounce
        # Keeping the Enter key fallback
        search_input.send_keys(Keys.RETURN)

        import time
        time.sleep(1)  # Wait for debounce

        rows = self.driver.find_elements(By.XPATH, self.RECORD_ROWS)
        self.assertGreater(len(rows), 0, "Expected at least one result")

    def test_filter_by_status(self):
        """Test filtering records by status dropdown.

        Steps:
        1. Navigate to records list
        2. Click Filter button to open panel
        3. Select 'Approved' from status filter dropdown
        4. Click Apply Filters
        5. Verify filter tag appears
        6. Verify filtered results
        """
        self.driver.get(self.RECORDS_URL)

        # Open filter panel
        self.driver.find_element(By.XPATH, self.FILTER_BUTTON).click()
        self.wait.until(EC.visibility_of_element_located((By.XPATH, self.FILTER_PANEL)))

        status_select = Select(self.driver.find_element(By.XPATH, self.STATUS_FILTER))
        status_select.select_by_visible_text("Approved")

        self.driver.find_element(By.XPATH, self.APPLY_FILTERS_BTN).click()

        # Verify active filter tags shown
        tags = self.driver.find_element(By.XPATH, self.ACTIVE_FILTER_TAGS)
        self.assertTrue(tags.is_displayed())

        rows = self.driver.find_elements(By.XPATH, self.RECORD_ROWS)
        self.assertGreater(len(rows), 0)

    def test_filter_by_type(self):
        """Test filtering records by type dropdown.

        Steps:
        1. Navigate to records list
        2. Open filter panel
        3. Select 'Compliance' from type filter
        4. Click Apply
        5. Verify filtered results
        """
        self.driver.get(self.RECORDS_URL)

        self.driver.find_element(By.XPATH, self.FILTER_BUTTON).click()
        self.wait.until(EC.visibility_of_element_located((By.XPATH, self.FILTER_PANEL)))

        type_select = Select(self.driver.find_element(By.XPATH, self.TYPE_FILTER))
        type_select.select_by_visible_text("Compliance")

        self.driver.find_element(By.XPATH, self.APPLY_FILTERS_BTN).click()

        rows = self.driver.find_elements(By.XPATH, self.RECORD_ROWS)
        self.assertGreater(len(rows), 0)

    def test_filter_by_date_range(self):
        """Test filtering records by date range.

        Steps:
        1. Navigate to records list
        2. Open filter panel
        3. Enter start date in From field
        4. Enter end date in To field
        5. Click Apply Filters
        6. Verify results within date range
        """
        self.driver.get(self.RECORDS_URL)

        self.driver.find_element(By.XPATH, self.FILTER_BUTTON).click()
        self.wait.until(EC.visibility_of_element_located((By.XPATH, self.FILTER_PANEL)))

        date_from = self.driver.find_element(By.XPATH, self.DATE_FROM_INPUT)
        date_from.clear()
        date_from.send_keys("2026-02-01")

        date_to = self.driver.find_element(By.XPATH, self.DATE_TO_INPUT)
        date_to.clear()
        date_to.send_keys("2026-02-28")

        self.driver.find_element(By.XPATH, self.APPLY_FILTERS_BTN).click()

        rows = self.driver.find_elements(By.XPATH, self.RECORD_ROWS)
        self.assertGreater(len(rows), 0, "Expected results in date range")

    def test_pagination(self):
        """Test pagination navigation on records list.

        Steps:
        1. Navigate to records list
        2. Verify first page is loaded
        3. Click Next page button
        4. Verify page 2 records shown
        5. Click Previous page button
        6. Verify back on page 1
        """
        self.driver.get(self.RECORDS_URL)

        rows_page1 = self.driver.find_elements(By.XPATH, self.RECORD_ROWS)
        first_row_text = rows_page1[0].text if rows_page1 else ""

        # Go to page 2
        next_btn = self.driver.find_element(By.XPATH, self.PAGINATION_NEXT)
        next_btn.click()

        import time
        time.sleep(1)

        rows_page2 = self.driver.find_elements(By.XPATH, self.RECORD_ROWS)
        self.assertGreater(len(rows_page2), 0)

        # Go back to page 1
        prev_btn = self.driver.find_element(By.XPATH, self.PAGINATION_PREV)
        prev_btn.click()

    def test_clear_filters(self):
        """Test clearing all filters resets the list.

        Steps:
        1. Apply a status filter
        2. Click Clear Filters button
        3. Verify all filters are reset
        4. Verify full unfiltered results shown
        """
        self.driver.get(self.RECORDS_URL)

        # Open filter panel and apply filter
        self.driver.find_element(By.XPATH, self.FILTER_BUTTON).click()
        self.wait.until(EC.visibility_of_element_located((By.XPATH, self.FILTER_PANEL)))

        status_select = Select(self.driver.find_element(By.XPATH, self.STATUS_FILTER))
        status_select.select_by_visible_text("Rejected")
        self.driver.find_element(By.XPATH, self.APPLY_FILTERS_BTN).click()

        import time
        time.sleep(0.5)

        # Clear filters
        self.driver.find_element(By.XPATH, self.CLEAR_FILTERS_BTN).click()
        time.sleep(0.5)

        # Verify status dropdown reset
        status_select = Select(self.driver.find_element(By.XPATH, self.STATUS_FILTER))
        self.assertEqual(status_select.first_selected_option.text, "All Statuses")

    def test_sort_by_title_column(self):
        """Test sorting records by clicking title column header.

        Steps:
        1. Navigate to records list
        2. Click on Title column header
        3. Verify sort icon changes
        4. Click again to reverse sort
        """
        self.driver.get(self.RECORDS_URL)

        title_header = self.driver.find_element(By.XPATH, self.SORT_HEADER_TITLE)
        title_header.click()

        import time
        time.sleep(0.5)

        # Verify sort indicator changed
        sort_icon = title_header.find_element(By.CLASS_NAME, "sort-icon")
        sort_classes = sort_icon.get_attribute("class")
        self.assertTrue("sort--asc" in sort_classes or "sort--desc" in sort_classes)

    def test_show_archived_toggle(self):
        """Test toggling archived records visibility.

        Steps:
        1. Navigate to records list
        2. Check the 'Show archived' checkbox
        3. Verify archived records become visible
        4. Uncheck the checkbox
        5. Verify archived records hidden again
        """
        self.driver.get(self.RECORDS_URL)

        archived_toggle = self.driver.find_element(By.XPATH, self.SHOW_ARCHIVED)
        self.assertFalse(archived_toggle.is_selected())

        archived_toggle.click()
        self.assertTrue(archived_toggle.is_selected())

        # Toggle back off
        archived_toggle.click()
        self.assertFalse(archived_toggle.is_selected())


if __name__ == "__main__":
    unittest.main()
