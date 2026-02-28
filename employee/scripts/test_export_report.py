"""
Test Export Report — Selenium regression test for exporting reports to CSV/PDF.

Covers:
  - Open reports page and select a report
  - Run report with date range
  - Export report to CSV
  - Export report to PDF
  - Verify export success toast
"""

import os
import time
import unittest
from selenium import webdriver # type: ignore
from selenium.webdriver.common.by import By # type: ignore
from selenium.webdriver.support.ui import WebDriverWait, Select # type: ignore
from selenium.webdriver.support import expected_conditions as EC # type: ignore


class TestExportReport(unittest.TestCase):
    """Regression tests for report export at reports page."""

    BASE_URL = "http://localhost:8080"
    REPORTS_URL = f"{BASE_URL}/reports.html"

    # --- XPaths and Selectors (v1.0 — last updated Nov 2025) ---
    REPORTS_LIST = "//div[@data-testid='reports-list']"
    REPORT_CARD = "//div[@data-testid='reports-list']//div[contains(@class,'report-card')]"
    REPORT_DATE_FROM = "//input[@data-testid='report-date-from']"
    REPORT_DATE_TO = "//input[@data-testid='report-date-to']"
    RUN_REPORT_BTN = "//button[@data-testid='btn-run-report']"
    REPORT_LOADING = "//div[@data-testid='report-loading']"
    REPORT_RESULTS = "//div[@data-testid='report-results']"
    EXPORT_BUTTON = "//button[@data-testid='btn-export']"
    EXPORT_DROPDOWN = "//div[@data-testid='export-dropdown']"
    EXPORT_CSV_OPTION = "//div[@data-testid='export-csv']"
    EXPORT_PDF_OPTION = "//div[@data-testid='export-pdf']"
    EXPORT_PROGRESS = "//div[@data-testid='export-progress']"
    EXPORT_COMPLETE_MSG = "//div[@data-testid='export-complete']"
    TOAST_SUCCESS = "//div[@data-testid='toast-success']"
    TOAST_ERROR = "//div[@data-testid='toast-error']"
    EMPTY_STATE = "//div[@data-testid='empty-state-reports']"

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
        self.driver.get(f"{self.BASE_URL}/login.html")
        self.driver.find_element(By.XPATH, "//input[@data-testid='input-username']").send_keys("admin")
        self.driver.find_element(By.XPATH, "//input[@data-testid='input-password']").send_keys("admin123")
        self.driver.find_element(By.XPATH, "//button[@data-testid='btn-login']").click()
        self.wait.until(EC.url_contains("dashboard"))

    def test_open_reports_page(self):
        """Test that reports page loads and displays report cards.

        Steps:
        1. Navigate to reports page
        2. Verify reports list container is visible
        3. Verify at least one report card exists
        """
        self.driver.get(self.REPORTS_URL)

        reports_list = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, self.REPORTS_LIST))
        )
        self.assertTrue(reports_list.is_displayed())

        cards = self.driver.find_elements(By.XPATH, self.REPORT_CARD)
        self.assertGreaterEqual(len(cards), 1, "Expected at least one report card")

    def test_run_report_with_date_range(self):
        """Test running a report with date range shows results.

        Steps:
        1. Navigate to reports page
        2. Click first report card to open detail
        3. Set date range (Feb 2026)
        4. Click Run Report
        5. Wait for loading spinner to disappear
        6. Verify results section is visible
        """
        self.driver.get(self.REPORTS_URL)

        # Click first report card
        first_card = self.driver.find_elements(By.XPATH, self.REPORT_CARD)[0]
        first_card.click()

        # Set date range
        date_from = self.driver.find_element(By.XPATH, self.REPORT_DATE_FROM)
        date_from.clear()
        date_from.send_keys("2026-02-01")

        date_to = self.driver.find_element(By.XPATH, self.REPORT_DATE_TO)
        date_to.clear()
        date_to.send_keys("2026-02-28")

        # Run report
        self.driver.find_element(By.XPATH, self.RUN_REPORT_BTN).click()

        # Wait for loading
        self.wait.until(EC.invisibility_of_element_located((By.XPATH, self.REPORT_LOADING)))

        # Verify results
        results = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, self.REPORT_RESULTS))
        )
        self.assertTrue(results.is_displayed())

    def test_export_report_csv(self):
        """Test exporting a report to CSV format.

        Steps:
        1. Navigate to reports and run a report
        2. Click Export button
        3. Select CSV from dropdown
        4. Verify success toast appears
        """
        self.driver.get(self.REPORTS_URL)

        # Open and run report
        first_card = self.driver.find_elements(By.XPATH, self.REPORT_CARD)[0]
        first_card.click()
        self.driver.find_element(By.XPATH, self.RUN_REPORT_BTN).click()
        self.wait.until(EC.invisibility_of_element_located((By.XPATH, self.REPORT_LOADING)))

        # Export
        self.driver.find_element(By.XPATH, self.EXPORT_BUTTON).click()

        # NOTE: old selector — dropdown may have changed in latest version
        self.wait.until(EC.visibility_of_element_located((By.XPATH, self.EXPORT_DROPDOWN)))
        self.driver.find_element(By.XPATH, self.EXPORT_CSV_OPTION).click()

        toast = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, self.TOAST_SUCCESS))
        )
        self.assertIn("CSV", toast.text)

    def test_export_report_pdf(self):
        """Test exporting a report to PDF format.

        Steps:
        1. Navigate to reports and run a report
        2. Click Export button
        3. Select PDF from dropdown
        4. Verify success toast appears
        """
        self.driver.get(self.REPORTS_URL)

        first_card = self.driver.find_elements(By.XPATH, self.REPORT_CARD)[0]
        first_card.click()
        self.driver.find_element(By.XPATH, self.RUN_REPORT_BTN).click()
        self.wait.until(EC.invisibility_of_element_located((By.XPATH, self.REPORT_LOADING)))

        self.driver.find_element(By.XPATH, self.EXPORT_BUTTON).click()
        self.wait.until(EC.visibility_of_element_located((By.XPATH, self.EXPORT_DROPDOWN)))
        self.driver.find_element(By.XPATH, self.EXPORT_PDF_OPTION).click()

        toast = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, self.TOAST_SUCCESS))
        )
        self.assertTrue(toast.is_displayed())


if __name__ == "__main__":
    unittest.main()
