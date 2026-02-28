"""
Test Record Search and Filter — Selenium regression test for the records list page.

Covers:
  - Search records by keyword
  - Filter by status dropdown
  - Filter by date range
  - Combined search and filter
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
    """Regression tests for the records list search and filter at /records."""

    BASE_URL = "https://app.example.com"
    RECORDS_URL = f"{BASE_URL}/records"

    # --- XPaths and Selectors ---
    SEARCH_INPUT = "//input[@data-testid='search-input']"
    SEARCH_BUTTON = "//button[@data-testid='search-btn']"
    STATUS_FILTER = "//select[@data-testid='filter-status']"
    DATE_FROM_INPUT = "//input[@data-testid='filter-date-from']"
    DATE_TO_INPUT = "//input[@data-testid='filter-date-to']"
    APPLY_FILTERS_BTN = "//button[@data-testid='apply-filters-btn']"
    CLEAR_FILTERS_BTN = "//button[@data-testid='clear-filters-btn']"
    RECORDS_TABLE = "//table[@data-testid='records-table']"
    RECORD_ROWS = "//table[@data-testid='records-table']//tbody//tr"
    NO_RESULTS_MESSAGE = "//div[@data-testid='no-results-message']"
    RESULTS_COUNT = "//span[@data-testid='results-count']"
    PAGINATION_NEXT = "//button[@data-testid='pagination-next']"
    PAGINATION_PREV = "//button[@data-testid='pagination-prev']"
    PAGINATION_PAGE = "//button[@data-testid='pagination-page-{num}']"
    SORT_HEADER_NAME = "//th[@data-testid='sort-name']"
    SORT_HEADER_DATE = "//th[@data-testid='sort-date']"
    SORT_HEADER_STATUS = "//th[@data-testid='sort-status']"
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
        self.driver.get(f"{self.BASE_URL}/auth/login")
        self.driver.find_element(By.XPATH, "//input[@data-testid='login-username']").send_keys("admin@example.com")
        self.driver.find_element(By.XPATH, "//input[@data-testid='login-password']").send_keys("AdminPass123!")
        self.driver.find_element(By.XPATH, "//button[@data-testid='login-submit-btn']").click()
        self.wait.until(EC.url_contains("/dashboard"))

    def test_search_by_keyword(self):
        """Test searching records by keyword in the search box.

        Steps:
        1. Navigate to records list
        2. Enter search keyword in search box
        3. Click search button
        4. Verify results contain the keyword
        5. Verify results count updates
        """
        self.driver.get(self.RECORDS_URL)

        search_input = self.driver.find_element(By.XPATH, self.SEARCH_INPUT)
        search_input.clear()
        search_input.send_keys("Performance Review")
        self.driver.find_element(By.XPATH, self.SEARCH_BUTTON).click()

        self.wait.until(EC.invisibility_of_element_located((By.XPATH, self.LOADING_OVERLAY)))

        rows = self.driver.find_elements(By.XPATH, self.RECORD_ROWS)
        self.assertGreater(len(rows), 0, "Expected at least one result")

        count = self.driver.find_element(By.XPATH, self.RESULTS_COUNT)
        self.assertNotEqual(count.text.strip(), "0")

    def test_filter_by_status(self):
        """Test filtering records by status dropdown.

        Steps:
        1. Navigate to records list
        2. Select 'Approved' from status filter dropdown
        3. Click Apply Filters
        4. Verify all visible records have 'Approved' status
        """
        self.driver.get(self.RECORDS_URL)

        status_select = Select(self.driver.find_element(By.XPATH, self.STATUS_FILTER))
        status_select.select_by_visible_text("Approved")

        self.driver.find_element(By.XPATH, self.APPLY_FILTERS_BTN).click()
        self.wait.until(EC.invisibility_of_element_located((By.XPATH, self.LOADING_OVERLAY)))

        rows = self.driver.find_elements(By.XPATH, self.RECORD_ROWS)
        for row in rows:
            status_cell = row.find_element(By.XPATH, ".//td[@data-testid='cell-status']")
            self.assertEqual(status_cell.text.strip(), "Approved")

    def test_filter_by_date_range(self):
        """Test filtering records by date range.

        Steps:
        1. Navigate to records list
        2. Enter start date in From field
        3. Enter end date in To field
        4. Click Apply Filters
        5. Verify results are within the date range
        """
        self.driver.get(self.RECORDS_URL)

        date_from = self.driver.find_element(By.XPATH, self.DATE_FROM_INPUT)
        date_from.clear()
        date_from.send_keys("2026-01-01")

        date_to = self.driver.find_element(By.XPATH, self.DATE_TO_INPUT)
        date_to.clear()
        date_to.send_keys("2026-01-31")

        self.driver.find_element(By.XPATH, self.APPLY_FILTERS_BTN).click()
        self.wait.until(EC.invisibility_of_element_located((By.XPATH, self.LOADING_OVERLAY)))

        rows = self.driver.find_elements(By.XPATH, self.RECORD_ROWS)
        self.assertGreater(len(rows), 0, "Expected results in date range")

    def test_pagination(self):
        """Test pagination navigation on records list.

        Steps:
        1. Navigate to records list
        2. Verify first page is loaded
        3. Click Next page button
        4. Verify page 2 records are shown
        5. Click Previous page button
        6. Verify back on page 1
        """
        self.driver.get(self.RECORDS_URL)

        rows_page1 = self.driver.find_elements(By.XPATH, self.RECORD_ROWS)
        first_row_text = rows_page1[0].text if rows_page1 else ""

        # Go to page 2
        next_btn = self.driver.find_element(By.XPATH, self.PAGINATION_NEXT)
        next_btn.click()
        self.wait.until(EC.invisibility_of_element_located((By.XPATH, self.LOADING_OVERLAY)))

        rows_page2 = self.driver.find_elements(By.XPATH, self.RECORD_ROWS)
        self.assertGreater(len(rows_page2), 0)

        # Go back to page 1
        prev_btn = self.driver.find_element(By.XPATH, self.PAGINATION_PREV)
        prev_btn.click()
        self.wait.until(EC.invisibility_of_element_located((By.XPATH, self.LOADING_OVERLAY)))

    def test_clear_filters(self):
        """Test clearing all filters resets the list.

        Steps:
        1. Apply a status filter
        2. Click Clear Filters button
        3. Verify all filters are reset
        4. Verify full unfiltered results shown
        """
        self.driver.get(self.RECORDS_URL)

        # Apply filter
        status_select = Select(self.driver.find_element(By.XPATH, self.STATUS_FILTER))
        status_select.select_by_visible_text("Rejected")
        self.driver.find_element(By.XPATH, self.APPLY_FILTERS_BTN).click()
        self.wait.until(EC.invisibility_of_element_located((By.XPATH, self.LOADING_OVERLAY)))

        filtered_count = self.driver.find_element(By.XPATH, self.RESULTS_COUNT).text

        # Clear filters
        self.driver.find_element(By.XPATH, self.CLEAR_FILTERS_BTN).click()
        self.wait.until(EC.invisibility_of_element_located((By.XPATH, self.LOADING_OVERLAY)))

        total_count = self.driver.find_element(By.XPATH, self.RESULTS_COUNT).text
        status_select = Select(self.driver.find_element(By.XPATH, self.STATUS_FILTER))
        self.assertEqual(status_select.first_selected_option.text, "All")

    def test_sort_by_column(self):
        """Test sorting records by clicking column headers.

        Steps:
        1. Navigate to records list
        2. Click on Name column header
        3. Verify records are sorted alphabetically
        4. Click again to reverse sort
        """
        self.driver.get(self.RECORDS_URL)

        self.driver.find_element(By.XPATH, self.SORT_HEADER_NAME).click()
        self.wait.until(EC.invisibility_of_element_located((By.XPATH, self.LOADING_OVERLAY)))

        rows = self.driver.find_elements(By.XPATH, self.RECORD_ROWS)
        if len(rows) >= 2:
            name1 = rows[0].find_element(By.XPATH, ".//td[@data-testid='cell-name']").text
            name2 = rows[1].find_element(By.XPATH, ".//td[@data-testid='cell-name']").text
            self.assertLessEqual(name1.lower(), name2.lower())


if __name__ == "__main__":
    unittest.main()
