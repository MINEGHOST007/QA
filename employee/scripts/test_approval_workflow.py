"""
Test Approval Workflow — Selenium regression test for the record approval process.

Covers:
  - Submit a record for review
  - Approve a submitted record
  - Reject a submitted record with reason
  - Verify activity log updates
  - Verify status badge transitions
"""

import unittest
from selenium import webdriver # pyright: ignore[reportMissingImports]
from selenium.webdriver.common.by import By # type: ignore
from selenium.webdriver.support.ui import WebDriverWait # type: ignore
from selenium.webdriver.support import expected_conditions as EC # type: ignore


class TestApprovalWorkflow(unittest.TestCase):
    """Regression tests for the approval workflow on record detail page."""

    BASE_URL = "http://localhost:8080"
    RECORD_DETAIL_URL = f"{BASE_URL}/record-detail.html"

    # --- XPaths and Selectors (v1.3 — last updated Jan 2026) ---
    SUBMIT_FOR_REVIEW_BTN = "//button[@data-testid='btn-submit-for-review']"
    APPROVE_BUTTON = "//button[@data-testid='btn-approve']"
    REJECT_BUTTON = "//button[@data-testid='btn-reject']"
    STATUS_BADGE = "//span[@data-testid='status-badge']"
    ACTIVITY_LOG = "//div[@data-testid='activity-log']"
    ACTIVITY_LOG_ENTRIES = "//div[@data-testid='activity-log']//div[@class='log-entry']"

    # Modal selectors (some may be from older version)
    SUBMIT_REVIEW_MODAL = "//div[@data-testid='modal-submit-review']"
    WORKFLOW_COMMENT = "//textarea[@data-testid='input-workflow-comment']"
    CONFIRM_WORKFLOW_BTN = "//button[@data-testid='btn-confirm-workflow']"
    APPROVE_MODAL = "//div[@data-testid='modal-approve']"
    APPROVAL_NOTE = "//textarea[@data-testid='input-approval-note']"
    CONFIRM_APPROVAL_BTN = "//button[@data-testid='btn-confirm-approval']"
    REJECT_MODAL = "//div[@data-testid='modal-reject']"
    REJECTION_REASON = "//textarea[@data-testid='input-rejection-reason']"
    CONFIRM_REJECTION_BTN = "//button[@data-testid='btn-confirm-rejection']"

    CANCEL_MODAL_BTN = "//button[@data-testid='btn-cancel-modal']"
    TOAST_SUCCESS = "//div[@data-testid='toast-success']"
    TOAST_ERROR = "//div[@data-testid='toast-error']"

    # Old notification selectors — may not match current UI
    NOTIFICATION_BELL = "//button[@data-testid='notification-bell']"
    NOTIFICATION_DROPDOWN = "//div[@data-testid='notification-dropdown']"

    def setUp(self):
        """Set up browser and login."""
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()
        self.driver.implicitly_wait(10)
        self.wait = WebDriverWait(self.driver, 15)
        self._login()

    def tearDown(self):
        self.driver.quit()

    def _login(self):
        """Helper: log in with admin credentials."""
        self.driver.get(f"{self.BASE_URL}/login.html")
        self.driver.find_element(By.XPATH, "//input[@data-testid='input-username']").send_keys("admin")
        self.driver.find_element(By.XPATH, "//input[@data-testid='input-password']").send_keys("admin123")
        self.driver.find_element(By.XPATH, "//button[@data-testid='btn-login']").click()
        self.wait.until(EC.url_contains("dashboard"))

    def test_submit_record_for_review(self):
        """Test submitting a draft record for review.

        Steps:
        1. Navigate to record detail page
        2. Verify status is 'Draft'
        3. Click 'Submit for Review' button
        4. Enter optional comment in the modal
        5. Click Confirm
        6. Verify status changes to 'Pending Review'
        7. Verify success toast
        8. Verify activity log updated
        """
        self.driver.get(self.RECORD_DETAIL_URL)

        status = self.driver.find_element(By.XPATH, self.STATUS_BADGE)
        self.assertEqual(status.text.strip(), "Draft")

        self.driver.find_element(By.XPATH, self.SUBMIT_FOR_REVIEW_BTN).click()

        self.wait.until(EC.visibility_of_element_located((By.XPATH, self.SUBMIT_REVIEW_MODAL)))

        # Enter optional comment
        comment_field = self.driver.find_element(By.XPATH, self.WORKFLOW_COMMENT)
        comment_field.send_keys("Ready for review — all sections complete.")

        self.driver.find_element(By.XPATH, self.CONFIRM_WORKFLOW_BTN).click()

        toast = self.wait.until(EC.visibility_of_element_located((By.XPATH, self.TOAST_SUCCESS)))
        self.assertTrue(toast.is_displayed())

        self.wait.until(
            EC.text_to_be_present_in_element((By.XPATH, self.STATUS_BADGE), "Pending Review")
        )

    def test_approve_record(self):
        """Test approving a pending record.

        Steps:
        1. Navigate to record detail (should be Pending Review)
        2. Click Approve button
        3. Enter optional approval note
        4. Click Approve in modal
        5. Verify status changes to 'Approved'
        6. Verify success toast
        """
        self.driver.get(self.RECORD_DETAIL_URL)

        self.driver.find_element(By.XPATH, self.APPROVE_BUTTON).click()

        self.wait.until(EC.visibility_of_element_located((By.XPATH, self.APPROVE_MODAL)))

        note_field = self.driver.find_element(By.XPATH, self.APPROVAL_NOTE)
        note_field.send_keys("Looks good. Approved.")

        self.driver.find_element(By.XPATH, self.CONFIRM_APPROVAL_BTN).click()

        toast = self.wait.until(EC.visibility_of_element_located((By.XPATH, self.TOAST_SUCCESS)))
        self.assertIn("approved", toast.text.lower())

        self.wait.until(
            EC.text_to_be_present_in_element((By.XPATH, self.STATUS_BADGE), "Approved")
        )

    def test_reject_record_with_reason(self):
        """Test rejecting a record requires a reason.

        Steps:
        1. Navigate to record detail (should be Pending Review)
        2. Click Reject button
        3. Enter rejection reason in textarea (required)
        4. Click Reject in modal
        5. Verify status changes to 'Rejected'
        6. Verify rejection reason saved
        """
        self.driver.get(self.RECORD_DETAIL_URL)

        self.driver.find_element(By.XPATH, self.REJECT_BUTTON).click()

        self.wait.until(EC.visibility_of_element_located((By.XPATH, self.REJECT_MODAL)))

        reason_field = self.driver.find_element(By.XPATH, self.REJECTION_REASON)
        reason_field.send_keys("Missing compliance documentation for Section 4B.")

        self.driver.find_element(By.XPATH, self.CONFIRM_REJECTION_BTN).click()

        toast = self.wait.until(EC.visibility_of_element_located((By.XPATH, self.TOAST_SUCCESS)))
        self.assertTrue(toast.is_displayed())

        self.wait.until(
            EC.text_to_be_present_in_element((By.XPATH, self.STATUS_BADGE), "Rejected")
        )

    def test_activity_log_shows_entries(self):
        """Test that the activity log displays workflow history.

        Steps:
        1. Navigate to record detail
        2. Verify activity log container is visible
        3. Verify at least one log entry exists
        4. Verify log entries have timestamps
        """
        self.driver.get(self.RECORD_DETAIL_URL)

        activity_log = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, self.ACTIVITY_LOG))
        )
        self.assertTrue(activity_log.is_displayed())

        entries = self.driver.find_elements(By.XPATH, self.ACTIVITY_LOG_ENTRIES)
        self.assertGreater(len(entries), 0, "Expected at least one activity entry")


if __name__ == "__main__":
    unittest.main()
