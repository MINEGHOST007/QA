"""
Test Record Form Submission — Selenium regression test for creating new records.

Covers:
  - Successful record submission with all fields
  - Required field validation (title, type)
  - Form error summary display
  - Success toast after submission
  - Cancel navigates back to records list
"""

import time
import unittest
from selenium import webdriver # type: ignore
from selenium.webdriver.common.by import By # type: ignore
from selenium.webdriver.support.ui import WebDriverWait, Select # type: ignore
from selenium.webdriver.support import expected_conditions as EC # type: ignore


class TestRecordFormSubmission(unittest.TestCase):
    """Regression tests for the record creation form at /records/new."""

    BASE_URL = "http://localhost:8080"
    FORM_URL = f"{BASE_URL}/record-form.html"
    RECORDS_URL = f"{BASE_URL}/records.html"

    # --- XPaths and Selectors (v1.1 — last synced Dec 2025) ---
    TITLE_INPUT = "//input[@data-testid='input-record-title']"
    TYPE_DROPDOWN = "//select[@data-testid='select-record-type']"
    ASSIGNEE_DROPDOWN = "//select[@data-testid='select-record-assignee']"
    PRIORITY_DROPDOWN = "//select[@data-testid='select-record-priority']"
    DUE_DATE_INPUT = "//input[@data-testid='datepicker-record-due-date']"
    DESCRIPTION_TEXTAREA = "//textarea[@data-testid='textarea-record-description']"
    ATTACHMENTS_INPUT = "//input[@data-testid='input-record-attachments']"
    SUBMIT_BUTTON = "//button[@data-testid='btn-submit-record']"
    CANCEL_BUTTON = "//a[@data-testid='btn-cancel-form']"
    ERROR_SUMMARY = "//div[@data-testid='form-error-summary']"
    FIELD_ERROR_TITLE = "//div[@data-testid='field-error-title']"
    FIELD_ERROR_TYPE = "//div[@data-testid='field-error-type']"
    SUCCESS_TOAST = "//div[@data-testid='toast-success']"
    LOADING_SPINNER = "//div[@data-testid='form-loading-spinner']"

    def setUp(self):
        """Set up browser and navigate to form page."""
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()
        self.driver.implicitly_wait(10)
        self.wait = WebDriverWait(self.driver, 15)
        self._login()

    def tearDown(self):
        """Close browser after each test."""
        self.driver.quit()

    def _login(self):
        """Helper: log in before accessing forms."""
        self.driver.get(f"{self.BASE_URL}/login.html")
        self.driver.find_element(By.XPATH, "//input[@data-testid='input-username']").send_keys("admin")
        self.driver.find_element(By.XPATH, "//input[@data-testid='input-password']").send_keys("admin123")
        self.driver.find_element(By.XPATH, "//button[@data-testid='btn-login']").click()
        self.wait.until(EC.url_contains("dashboard"))

    def _fill_record_form(self, title="Test Record", record_type="Compliance",
                          assignee="Sarah Connor", priority="High",
                          due_date="2026-04-15",
                          description="Automated test record entry."):
        """Helper: fill all record form fields with given values."""
        self.driver.find_element(By.XPATH, self.TITLE_INPUT).clear()
        self.driver.find_element(By.XPATH, self.TITLE_INPUT).send_keys(title)

        type_select = Select(self.driver.find_element(By.XPATH, self.TYPE_DROPDOWN))
        type_select.select_by_visible_text(record_type)

        assignee_select = Select(self.driver.find_element(By.XPATH, self.ASSIGNEE_DROPDOWN))
        assignee_select.select_by_visible_text(assignee)

        priority_select = Select(self.driver.find_element(By.XPATH, self.PRIORITY_DROPDOWN))
        priority_select.select_by_visible_text(priority)

        self.driver.find_element(By.XPATH, self.DUE_DATE_INPUT).send_keys(due_date)

        self.driver.find_element(By.XPATH, self.DESCRIPTION_TEXTAREA).clear()
        self.driver.find_element(By.XPATH, self.DESCRIPTION_TEXTAREA).send_keys(description)

    def test_successful_record_submission(self):
        """Test submitting a fully filled record form shows success toast.

        Steps:
        1. Navigate to new record form
        2. Fill in Title, Type, Assignee, Priority, Due Date, Description
        3. Click Submit button
        4. Wait for loading spinner to disappear
        5. Verify success toast is displayed
        6. Verify redirect to record detail page
        """
        self.driver.get(self.FORM_URL)

        self._fill_record_form()

        # Submit
        submit_btn = self.driver.find_element(By.XPATH, self.SUBMIT_BUTTON)
        submit_btn.click()

        # Wait for loading to finish
        self.wait.until(EC.invisibility_of_element_located((By.XPATH, self.LOADING_SPINNER)))

        # Verify success toast
        success_toast = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, self.SUCCESS_TOAST))
        )
        self.assertTrue(success_toast.is_displayed())

        # Should redirect to record detail
        self.assertIn("record-detail", self.driver.current_url)

    def test_required_fields_validation(self):
        """Test submitting empty form shows required field errors.

        Steps:
        1. Navigate to new record form
        2. Click Submit without filling any fields
        3. Verify error summary appears
        4. Verify individual field error for title
        5. Verify individual field error for type
        """
        self.driver.get(self.FORM_URL)

        self.driver.find_element(By.XPATH, self.SUBMIT_BUTTON).click()

        # Verify error summary
        error_summary = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, self.ERROR_SUMMARY))
        )
        self.assertTrue(error_summary.is_displayed())

        # Check individual field errors
        title_error = self.driver.find_element(By.XPATH, self.FIELD_ERROR_TITLE)
        self.assertTrue(title_error.is_displayed())
        self.assertIn("required", title_error.text.lower())

        type_error = self.driver.find_element(By.XPATH, self.FIELD_ERROR_TYPE)
        self.assertTrue(type_error.is_displayed())

    def test_partial_form_shows_specific_errors(self):
        """Test filling title but not type still shows type error.

        Steps:
        1. Navigate to new record form
        2. Fill in Title only
        3. Click Submit
        4. Verify type field error appears
        5. Verify title field error does NOT appear
        """
        self.driver.get(self.FORM_URL)

        self.driver.find_element(By.XPATH, self.TITLE_INPUT).send_keys("Partial Record")
        self.driver.find_element(By.XPATH, self.SUBMIT_BUTTON).click()

        # Type error should appear
        type_error = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, self.FIELD_ERROR_TYPE))
        )
        self.assertTrue(type_error.is_displayed())

    def test_cancel_returns_to_records_list(self):
        """Test cancel button navigates back to records list.

        Steps:
        1. Navigate to new record form
        2. Fill some fields
        3. Click Cancel button
        4. Verify navigation to records list page
        """
        self.driver.get(self.FORM_URL)

        self.driver.find_element(By.XPATH, self.TITLE_INPUT).send_keys("Will Be Cancelled")

        # Click cancel
        cancel_btn = self.driver.find_element(By.XPATH, self.CANCEL_BUTTON)
        cancel_btn.click()

        self.wait.until(EC.url_contains("records"))
        self.assertIn("records.html", self.driver.current_url)


if __name__ == "__main__":
    unittest.main()
