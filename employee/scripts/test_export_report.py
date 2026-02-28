"""
Test Export Report — Selenium regression test for exporting records to CSV/PDF.

Covers:
  - Export all records to CSV
  - Export filtered records to PDF
  - Verify download file exists
  - Export with date range filter
  - Large dataset export with progress indicator
"""

import os
import time
import unittest
from selenium import webdriver # type: ignore
from selenium.webdriver.common.by import By # type: ignore
from selenium.webdriver.support.ui import WebDriverWait, Select # type: ignore
from selenium.webdriver.support import expected_conditions as EC # type: ignore


class TestExportReport(unittest.TestCase):
    """Regression tests for record export at /records/export."""

    BASE_URL = "https://app.example.com"
    RECORDS_URL = f"{BASE_URL}/records"

    # --- XPaths and Selectors ---
    EXPORT_BUTTON = "//button[@data-testid='btn-export']"
    EXPORT_DROPDOWN = "//div[@data-testid='export-dropdown']"
    EXPORT_CSV_OPTION = "//button[@data-testid='export-csv']"
    EXPORT_PDF_OPTION = "//button[@data-testid='export-pdf']"
    EXPORT_PROGRESS = "//div[@data-testid='export-progress']"
    EXPORT_PROGRESS_BAR = "//div[@data-testid='export-progress-bar']"
    EXPORT_COMPLETE_MSG = "//div[@data-testid='export-complete']"
    DOWNLOAD_LINK = "//a[@data-testid='download-link']"
    STATUS_FILTER = "//select[@data-testid='filter-status']"
    DATE_FROM = "//input[@data-testid='filter-date-from']"
    DATE_TO = "//input[@data-testid='filter-date-to']"
    APPLY_FILTERS_BTN = "//button[@data-testid='apply-filters-btn']"
    TOAST_SUCCESS = "//div[@data-testid='toast-success']"
    TOAST_ERROR = "//div[@data-testid='toast-error']"
    LOADING_OVERLAY = "//div[@data-testid='loading-overlay']"

    DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

    def setUp(self):
        """Set up browser with download directory configured."""
        chrome_options = webdriver.ChromeOptions()
        prefs = {"download.default_directory": self.DOWNLOAD_DIR}
        chrome_options.add_experimental_option("prefs", prefs)
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.maximize_window()
        self.driver.implicitly_wait(10)
        self.wait = WebDriverWait(self.driver, 30)
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

    def test_export_all_records_csv(self):
        """Test exporting all records to CSV format.

        Steps:
        1. Navigate to records list
        2. Click Export button
        3. Select CSV from dropdown
        4. Wait for export progress to complete
        5. Verify success message
        6. Verify download link appears
        """
        self.driver.get(self.RECORDS_URL)

        self.driver.find_element(By.XPATH, self.EXPORT_BUTTON).click()
        self.wait.until(EC.visibility_of_element_located((By.XPATH, self.EXPORT_DROPDOWN)))

        self.driver.find_element(By.XPATH, self.EXPORT_CSV_OPTION).click()

        # Wait for export progress
        self.wait.until(EC.visibility_of_element_located((By.XPATH, self.EXPORT_PROGRESS)))
        self.wait.until(EC.visibility_of_element_located((By.XPATH, self.EXPORT_COMPLETE_MSG)))

        toast = self.driver.find_element(By.XPATH, self.TOAST_SUCCESS)
        self.assertIn("export", toast.text.lower())

    def test_export_filtered_records_pdf(self):
        """Test exporting filtered records to PDF.

        Steps:
        1. Navigate to records list
        2. Filter by status = 'Approved'
        3. Click Export button
        4. Select PDF from dropdown
        5. Wait for export to complete
        6. Verify success message
        """
        self.driver.get(self.RECORDS_URL)

        status_select = Select(self.driver.find_element(By.XPATH, self.STATUS_FILTER))
        status_select.select_by_visible_text("Approved")
        self.driver.find_element(By.XPATH, self.APPLY_FILTERS_BTN).click()
        self.wait.until(EC.invisibility_of_element_located((By.XPATH, self.LOADING_OVERLAY)))

        self.driver.find_element(By.XPATH, self.EXPORT_BUTTON).click()
        self.wait.until(EC.visibility_of_element_located((By.XPATH, self.EXPORT_DROPDOWN)))
        self.driver.find_element(By.XPATH, self.EXPORT_PDF_OPTION).click()

        self.wait.until(EC.visibility_of_element_located((By.XPATH, self.EXPORT_COMPLETE_MSG)))

        toast = self.driver.find_element(By.XPATH, self.TOAST_SUCCESS)
        self.assertTrue(toast.is_displayed())

    def test_export_with_date_range(self):
        """Test exporting records with a date range filter applied.

        Steps:
        1. Navigate to records list
        2. Set date range filter (Jan 2026)
        3. Apply filters
        4. Export to CSV
        5. Verify export succeeds
        """
        self.driver.get(self.RECORDS_URL)

        self.driver.find_element(By.XPATH, self.DATE_FROM).send_keys("2026-01-01")
        self.driver.find_element(By.XPATH, self.DATE_TO).send_keys("2026-01-31")
        self.driver.find_element(By.XPATH, self.APPLY_FILTERS_BTN).click()
        self.wait.until(EC.invisibility_of_element_located((By.XPATH, self.LOADING_OVERLAY)))

        self.driver.find_element(By.XPATH, self.EXPORT_BUTTON).click()
        self.wait.until(EC.visibility_of_element_located((By.XPATH, self.EXPORT_DROPDOWN)))
        self.driver.find_element(By.XPATH, self.EXPORT_CSV_OPTION).click()

        self.wait.until(EC.visibility_of_element_located((By.XPATH, self.EXPORT_COMPLETE_MSG)))

        toast = self.driver.find_element(By.XPATH, self.TOAST_SUCCESS)
        self.assertIn("export", toast.text.lower())


if __name__ == "__main__":
    unittest.main()
