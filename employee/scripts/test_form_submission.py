"""
Test Form Submission — Selenium regression test for the contact/feedback form.

Covers:
  - Successful form submission with all fields
  - Required field validation
  - Email format validation
  - Success message verification
  - Form reset after submission
"""

import time
import unittest
from selenium import webdriver # type: ignore
from selenium.webdriver.common.by import By # type: ignore
from selenium.webdriver.support.ui import WebDriverWait, Select # type: ignore
from selenium.webdriver.support import expected_conditions as EC # type: ignore


class TestFormSubmission(unittest.TestCase):
    """Regression tests for the contact form at /forms/contact."""

    BASE_URL = "https://app.example.com"
    FORM_URL = f"{BASE_URL}/forms/contact"

    # --- XPaths and Selectors ---
    FIRST_NAME_INPUT = "//input[@data-testid='form-first-name']"
    LAST_NAME_INPUT = "//input[@data-testid='form-last-name']"
    EMAIL_INPUT = "//input[@data-testid='form-email']"
    PHONE_INPUT = "//input[@data-testid='form-phone']"
    SUBJECT_DROPDOWN = "//select[@data-testid='form-subject']"
    MESSAGE_TEXTAREA = "//textarea[@data-testid='form-message']"
    SUBMIT_BUTTON = "//button[@data-testid='form-submit-btn']"
    RESET_BUTTON = "//button[@data-testid='form-reset-btn']"
    SUCCESS_MESSAGE = "//div[@data-testid='form-success-message']"
    ERROR_SUMMARY = "//div[@data-testid='form-error-summary']"
    FIELD_ERROR = "//span[@class='field-error' and @data-testid='field-error-{field}']"
    LOADING_SPINNER = "//div[@data-testid='form-loading-spinner']"

    def setUp(self):
        """Set up browser and navigate to form page."""
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()
        self.driver.implicitly_wait(10)
        self.wait = WebDriverWait(self.driver, 15)

    def tearDown(self):
        """Close browser after each test."""
        self.driver.quit()

    def _fill_form(self, first_name="John", last_name="Doe",
                   email="john@example.com", phone="555-0100",
                   subject="General Inquiry", message="Test message"):
        """Helper: fill all form fields with given values."""
        self.driver.find_element(By.XPATH, self.FIRST_NAME_INPUT).clear()
        self.driver.find_element(By.XPATH, self.FIRST_NAME_INPUT).send_keys(first_name)

        self.driver.find_element(By.XPATH, self.LAST_NAME_INPUT).clear()
        self.driver.find_element(By.XPATH, self.LAST_NAME_INPUT).send_keys(last_name)

        self.driver.find_element(By.XPATH, self.EMAIL_INPUT).clear()
        self.driver.find_element(By.XPATH, self.EMAIL_INPUT).send_keys(email)

        self.driver.find_element(By.XPATH, self.PHONE_INPUT).clear()
        self.driver.find_element(By.XPATH, self.PHONE_INPUT).send_keys(phone)

        subject_select = Select(self.driver.find_element(By.XPATH, self.SUBJECT_DROPDOWN))
        subject_select.select_by_visible_text(subject)

        self.driver.find_element(By.XPATH, self.MESSAGE_TEXTAREA).clear()
        self.driver.find_element(By.XPATH, self.MESSAGE_TEXTAREA).send_keys(message)

    def test_successful_form_submission(self):
        """Test submitting a fully filled form shows success message.

        Steps:
        1. Navigate to form page
        2. Fill in First Name, Last Name, Email, Phone
        3. Select a Subject from the dropdown
        4. Enter a message in the textarea
        5. Click Submit button
        6. Wait for loading spinner to disappear
        7. Verify success message is displayed
        8. Verify success message text contains 'Thank you'
        """
        self.driver.get(self.FORM_URL)

        self._fill_form()

        # Submit
        submit_btn = self.driver.find_element(By.XPATH, self.SUBMIT_BUTTON)
        submit_btn.click()

        # Wait for loading to finish
        self.wait.until(EC.invisibility_of_element_located((By.XPATH, self.LOADING_SPINNER)))

        # Verify success
        success_msg = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, self.SUCCESS_MESSAGE))
        )
        self.assertTrue(success_msg.is_displayed())
        self.assertIn("Thank you", success_msg.text)

    def test_required_fields_validation(self):
        """Test submitting empty form shows required field errors.

        Steps:
        1. Navigate to form page
        2. Click Submit without filling any fields
        3. Verify error summary appears
        4. Verify individual field error messages
        """
        self.driver.get(self.FORM_URL)

        self.driver.find_element(By.XPATH, self.SUBMIT_BUTTON).click()

        # Verify error summary
        error_summary = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, self.ERROR_SUMMARY))
        )
        self.assertTrue(error_summary.is_displayed())

        # Check individual field errors
        for field in ["first-name", "last-name", "email"]:
            xpath = self.FIELD_ERROR.format(field=field)
            field_err = self.driver.find_element(By.XPATH, xpath)
            self.assertTrue(field_err.is_displayed(), f"Error missing for {field}")

    def test_invalid_email_validation(self):
        """Test submitting form with invalid email shows email error.

        Steps:
        1. Navigate to form page
        2. Fill all required fields with valid data
        3. Enter invalid email format
        4. Click Submit
        5. Verify email validation error appears
        """
        self.driver.get(self.FORM_URL)

        self._fill_form(email="not-an-email")

        self.driver.find_element(By.XPATH, self.SUBMIT_BUTTON).click()

        email_error_xpath = self.FIELD_ERROR.format(field="email")
        email_err = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, email_error_xpath))
        )
        self.assertIn("valid email", email_err.text.lower())

    def test_form_reset_clears_fields(self):
        """Test reset button clears all form fields.

        Steps:
        1. Navigate to form page
        2. Fill all fields
        3. Click Reset button
        4. Verify all fields are empty
        """
        self.driver.get(self.FORM_URL)

        self._fill_form()

        # Click reset
        self.driver.find_element(By.XPATH, self.RESET_BUTTON).click()

        # Verify fields are cleared
        first_name = self.driver.find_element(By.XPATH, self.FIRST_NAME_INPUT)
        self.assertEqual(first_name.get_attribute("value"), "")

        email = self.driver.find_element(By.XPATH, self.EMAIL_INPUT)
        self.assertEqual(email.get_attribute("value"), "")

    def test_success_message_dismissed_on_new_submission(self):
        """Test that success message disappears when starting a new form entry.

        Steps:
        1. Submit a valid form
        2. Verify success message
        3. Start filling a new form
        4. Verify success message is hidden
        """
        self.driver.get(self.FORM_URL)

        self._fill_form()
        self.driver.find_element(By.XPATH, self.SUBMIT_BUTTON).click()

        self.wait.until(EC.invisibility_of_element_located((By.XPATH, self.LOADING_SPINNER)))
        self.wait.until(EC.visibility_of_element_located((By.XPATH, self.SUCCESS_MESSAGE)))

        # Start new entry
        self.driver.find_element(By.XPATH, self.FIRST_NAME_INPUT).send_keys("New")

        # Success message should hide
        time.sleep(1)
        success_elements = self.driver.find_elements(By.XPATH, self.SUCCESS_MESSAGE)
        if success_elements:
            self.assertFalse(success_elements[0].is_displayed())


if __name__ == "__main__":
    unittest.main()
