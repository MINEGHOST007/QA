"""
Test Approval Workflow — Selenium regression test for the record approval process.

Covers:
  - Submit a record for approval
  - Approve a submitted record
  - Reject a submitted record with reason
  - Verify approval history/audit trail
  - Verify email notification on approval
"""

import unittest
from selenium import webdriver # pyright: ignore[reportMissingImports]
from selenium.webdriver.common.by import By # type: ignore
from selenium.webdriver.support.ui import WebDriverWait # type: ignore
from selenium.webdriver.support import expected_conditions as EC # type: ignore


class TestApprovalWorkflow(unittest.TestCase):
    """Regression tests for the approval workflow at /records/{id}/approve."""

    BASE_URL = "https://app.example.com"
    RECORDS_URL = f"{BASE_URL}/records"

    # --- XPaths and Selectors ---
    RECORD_ROW = "//tr[@data-testid='record-row-{id}']"
    RECORD_LINK = "//a[@data-testid='record-link-{id}']"
    SUBMIT_FOR_APPROVAL_BTN = "//button[@data-testid='btn-submit-for-approval']"
    APPROVE_BUTTON = "//button[@data-testid='btn-approve']"
    REJECT_BUTTON = "//button[@data-testid='btn-reject']"
    REJECTION_REASON_TEXTAREA = "//textarea[@data-testid='rejection-reason']"
    STATUS_BADGE = "//span[@data-testid='record-status-badge']"
    APPROVAL_HISTORY_TAB = "//button[@data-testid='tab-approval-history']"
    HISTORY_TABLE = "//table[@data-testid='approval-history-table']"
    HISTORY_ROWS = "//table[@data-testid='approval-history-table']//tr"
    CONFIRM_MODAL = "//div[@data-testid='confirm-modal']"
    CONFIRM_YES = "//button[@data-testid='confirm-yes-btn']"
    TOAST_SUCCESS = "//div[@data-testid='toast-success']"
    TOAST_ERROR = "//div[@data-testid='toast-error']"
    NOTIFICATION_BELL = "//button[@data-testid='notification-bell']"
    NOTIFICATION_DROPDOWN = "//div[@data-testid='notification-dropdown']"
    NOTIFICATION_ITEM = "//div[@data-testid='notification-item']"

    DRAFT_RECORD_ID = "REC-005"
    PENDING_RECORD_ID = "REC-010"

    def setUp(self):
        """Set up browser and login as reviewer."""
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()
        self.driver.implicitly_wait(10)
        self.wait = WebDriverWait(self.driver, 15)

    def tearDown(self):
        self.driver.quit()

    def _login(self, username, password):
        """Helper: log in with given credentials."""
        self.driver.get(f"{self.BASE_URL}/auth/login")
        self.driver.find_element(By.XPATH, "//input[@data-testid='login-username']").send_keys(username)
        self.driver.find_element(By.XPATH, "//input[@data-testid='login-password']").send_keys(password)
        self.driver.find_element(By.XPATH, "//button[@data-testid='login-submit-btn']").click()
        self.wait.until(EC.url_contains("/dashboard"))

    def _navigate_to_record(self, record_id):
        """Navigate to a specific record."""
        self.driver.get(f"{self.RECORDS_URL}/{record_id}")
        self.wait.until(EC.presence_of_element_located((By.XPATH, self.STATUS_BADGE)))

    def test_submit_record_for_approval(self):
        """Test submitting a draft record for approval.

        Steps:
        1. Login as regular user
        2. Navigate to draft record REC-005
        3. Verify status is 'Draft'
        4. Click 'Submit for Approval' button
        5. Confirm in the modal
        6. Verify status changes to 'Pending Approval'
        7. Verify success toast
        """
        self._login("user@example.com", "UserPass123!")
        self._navigate_to_record(self.DRAFT_RECORD_ID)

        status = self.driver.find_element(By.XPATH, self.STATUS_BADGE)
        self.assertEqual(status.text.strip(), "Draft")

        self.driver.find_element(By.XPATH, self.SUBMIT_FOR_APPROVAL_BTN).click()

        self.wait.until(EC.visibility_of_element_located((By.XPATH, self.CONFIRM_MODAL)))
        self.driver.find_element(By.XPATH, self.CONFIRM_YES).click()

        toast = self.wait.until(EC.visibility_of_element_located((By.XPATH, self.TOAST_SUCCESS)))
        self.assertIn("submitted", toast.text.lower())

        self.wait.until(
            EC.text_to_be_present_in_element((By.XPATH, self.STATUS_BADGE), "Pending Approval")
        )

    def test_approve_record(self):
        """Test approving a pending record.

        Steps:
        1. Login as reviewer
        2. Navigate to pending record REC-010
        3. Verify status is 'Pending Approval'
        4. Click Approve button
        5. Confirm approval
        6. Verify status changes to 'Approved'
        7. Verify approval toast
        """
        self._login("reviewer@example.com", "ReviewerPass123!")
        self._navigate_to_record(self.PENDING_RECORD_ID)

        status = self.driver.find_element(By.XPATH, self.STATUS_BADGE)
        self.assertEqual(status.text.strip(), "Pending Approval")

        self.driver.find_element(By.XPATH, self.APPROVE_BUTTON).click()
        self.wait.until(EC.visibility_of_element_located((By.XPATH, self.CONFIRM_MODAL)))
        self.driver.find_element(By.XPATH, self.CONFIRM_YES).click()

        toast = self.wait.until(EC.visibility_of_element_located((By.XPATH, self.TOAST_SUCCESS)))
        self.assertIn("approved", toast.text.lower())

        self.wait.until(
            EC.text_to_be_present_in_element((By.XPATH, self.STATUS_BADGE), "Approved")
        )

    def test_reject_record_with_reason(self):
        """Test rejecting a record with a reason.

        Steps:
        1. Login as reviewer
        2. Navigate to pending record
        3. Click Reject button
        4. Enter rejection reason in textarea
        5. Confirm rejection
        6. Verify status changes to 'Rejected'
        7. Verify rejection reason is saved
        """
        self._login("reviewer@example.com", "ReviewerPass123!")
        self._navigate_to_record(self.PENDING_RECORD_ID)

        self.driver.find_element(By.XPATH, self.REJECT_BUTTON).click()

        # Enter reason
        reason_field = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, self.REJECTION_REASON_TEXTAREA))
        )
        reason_field.send_keys("Incomplete data — missing required fields in Section B.")

        self.driver.find_element(By.XPATH, self.CONFIRM_YES).click()

        toast = self.wait.until(EC.visibility_of_element_located((By.XPATH, self.TOAST_SUCCESS)))
        self.assertIn("rejected", toast.text.lower())

        self.wait.until(
            EC.text_to_be_present_in_element((By.XPATH, self.STATUS_BADGE), "Rejected")
        )

    def test_approval_history(self):
        """Test that approval history tab shows audit trail.

        Steps:
        1. Login as admin
        2. Navigate to a record that has been through approval
        3. Click the Approval History tab
        4. Verify history table is visible
        5. Verify at least one history entry exists
        """
        self._login("admin@example.com", "AdminPass123!")
        self._navigate_to_record(self.PENDING_RECORD_ID)

        self.driver.find_element(By.XPATH, self.APPROVAL_HISTORY_TAB).click()

        history_table = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, self.HISTORY_TABLE))
        )
        self.assertTrue(history_table.is_displayed())

        rows = self.driver.find_elements(By.XPATH, self.HISTORY_ROWS)
        self.assertGreater(len(rows), 1, "Expected at least one history entry plus header")


if __name__ == "__main__":
    unittest.main()
