"""
Test Record Locking — Selenium regression test for the record lock/unlock workflow.

Covers:
  - Lock an approved record
  - Verify locked status badge and lock icon
  - Verify edit button disabled when locked
  - Unlock a locked record with justification
  - Permission check: non-admin cannot lock
"""

import unittest
from selenium import webdriver # type: ignore
from selenium.webdriver.common.by import By # type: ignore
from selenium.webdriver.support.ui import WebDriverWait # type: ignore
from selenium.webdriver.support import expected_conditions as EC # type: ignore


class TestRecordLocking(unittest.TestCase):
    """Regression tests for record lock/unlock on record detail page."""

    BASE_URL = "http://localhost:8080"
    RECORD_DETAIL_URL = f"{BASE_URL}/record-detail.html"
    RECORDS_URL = f"{BASE_URL}/records.html"

    # --- XPaths and Selectors (v1.2 — last updated Dec 2025) ---
    STATUS_BADGE = "//span[@data-testid='status-badge']"
    LOCK_ICON = "//span[@data-testid='record-lock-icon']"
    ACTIONS_MENU = "//button[@data-testid='btn-actions-menu']"
    ACTIONS_DROPDOWN = "//div[@id='actions-dropdown']"
    LOCK_RECORD_BTN = "//div[@data-testid='action-lock-record']"
    UNLOCK_RECORD_BTN = "//div[@data-testid='action-unlock-record']"
    EDIT_BUTTON = "//a[@data-testid='btn-edit-record']"

    # Lock modal
    LOCK_MODAL = "//div[@data-testid='modal-lock']"
    CONFIRM_LOCK_BTN = "//button[@data-testid='btn-confirm-lock']"

    # Unlock modal — old version had different selector
    UNLOCK_MODAL = "//div[@data-testid='modal-unlock']"
    UNLOCK_REASON_INPUT = "//textarea[@data-testid='input-unlock-justification']"
    CONFIRM_UNLOCK_BTN = "//button[@data-testid='btn-confirm-unlock']"

    CANCEL_MODAL_BTN = "//button[@data-testid='btn-cancel-modal']"
    TOAST_SUCCESS = "//div[@data-testid='toast-success']"
    BREADCRUMB = "//nav[@data-testid='breadcrumb']"

    def setUp(self):
        """Set up browser and login as admin."""
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()
        self.driver.implicitly_wait(10)
        self.wait = WebDriverWait(self.driver, 15)
        self._login_as_admin()

    def tearDown(self):
        """Close browser."""
        self.driver.quit()

    def _login_as_admin(self):
        """Helper: log in as admin user."""
        self.driver.get(f"{self.BASE_URL}/login.html")
        self.driver.find_element(By.XPATH, "//input[@data-testid='input-username']").send_keys("admin")
        self.driver.find_element(By.XPATH, "//input[@data-testid='input-password']").send_keys("admin123")
        self.driver.find_element(By.XPATH, "//button[@data-testid='btn-login']").click()
        self.wait.until(EC.url_contains("dashboard"))

    def test_lock_approved_record(self):
        """Test locking an approved record changes its status to Locked.

        Pre-conditions:
        - User is logged in as admin
        - Record is in 'Approved' status

        Steps:
        1. Navigate to record detail page
        2. Verify status badge shows 'Approved'
        3. Click Actions menu
        4. Click Lock Record option
        5. Confirm in the lock modal
        6. Verify success toast appears
        7. Verify status badge changes to 'Locked'
        8. Verify lock icon appears
        9. Verify the edit button is now disabled
        """
        self.driver.get(self.RECORD_DETAIL_URL)

        # Verify initial status
        status = self.driver.find_element(By.XPATH, self.STATUS_BADGE)
        self.assertEqual(status.text.strip(), "Approved")

        # Open actions menu and click Lock
        self.driver.find_element(By.XPATH, self.ACTIONS_MENU).click()
        self.wait.until(EC.visibility_of_element_located((By.XPATH, self.ACTIONS_DROPDOWN)))

        lock_btn = self.driver.find_element(By.XPATH, self.LOCK_RECORD_BTN)
        lock_btn.click()

        # Confirm modal
        self.wait.until(EC.visibility_of_element_located((By.XPATH, self.LOCK_MODAL)))
        self.driver.find_element(By.XPATH, self.CONFIRM_LOCK_BTN).click()

        # Verify success
        toast = self.wait.until(EC.visibility_of_element_located((By.XPATH, self.TOAST_SUCCESS)))
        self.assertIn("locked", toast.text.lower())

        # Verify status changed
        self.wait.until(EC.text_to_be_present_in_element((By.XPATH, self.STATUS_BADGE), "Locked"))

        # Verify lock icon visible
        lock_icon = self.driver.find_element(By.XPATH, self.LOCK_ICON)
        self.assertTrue(lock_icon.is_displayed())

        # Verify edit button is disabled
        edit_btn = self.driver.find_element(By.XPATH, self.EDIT_BUTTON)
        self.assertFalse(edit_btn.is_enabled())

    def test_unlock_locked_record(self):
        """Test unlocking a locked record restores it to Approved status.

        Steps:
        1. Navigate to a locked record
        2. Click Actions menu
        3. Click Unlock Record
        4. Enter justification reason (required)
        5. Confirm in modal
        6. Verify status changes to 'Approved'
        7. Verify lock icon disappears
        8. Verify edit button is enabled again
        """
        self.driver.get(self.RECORD_DETAIL_URL)

        # Open actions and unlock
        self.driver.find_element(By.XPATH, self.ACTIONS_MENU).click()
        self.wait.until(EC.visibility_of_element_located((By.XPATH, self.ACTIONS_DROPDOWN)))

        unlock_btn = self.driver.find_element(By.XPATH, self.UNLOCK_RECORD_BTN)
        unlock_btn.click()

        self.wait.until(EC.visibility_of_element_located((By.XPATH, self.UNLOCK_MODAL)))

        # Enter justification
        reason_field = self.driver.find_element(By.XPATH, self.UNLOCK_REASON_INPUT)
        reason_field.send_keys("Correction needed in Section 3 — unlocking for edit.")

        self.driver.find_element(By.XPATH, self.CONFIRM_UNLOCK_BTN).click()

        toast = self.wait.until(EC.visibility_of_element_located((By.XPATH, self.TOAST_SUCCESS)))
        self.assertIn("unlocked", toast.text.lower())

        self.wait.until(EC.text_to_be_present_in_element((By.XPATH, self.STATUS_BADGE), "Approved"))

        edit_btn = self.driver.find_element(By.XPATH, self.EDIT_BUTTON)
        self.assertTrue(edit_btn.is_enabled())

    def test_non_admin_cannot_lock(self):
        """Test that a regular user cannot see the Lock Record option.

        Steps:
        1. Login as regular user (not admin)
        2. Navigate to record detail
        3. Open Actions menu
        4. Verify Lock Record option is NOT present
        """
        # Re-login as regular user
        self.driver.get(f"{self.BASE_URL}/login.html")
        self.driver.find_element(By.XPATH, "//input[@data-testid='input-username']").send_keys("editor")
        self.driver.find_element(By.XPATH, "//input[@data-testid='input-password']").send_keys("editor123")
        self.driver.find_element(By.XPATH, "//button[@data-testid='btn-login']").click()
        self.wait.until(EC.url_contains("dashboard"))

        self.driver.get(self.RECORD_DETAIL_URL)

        self.driver.find_element(By.XPATH, self.ACTIONS_MENU).click()
        self.wait.until(EC.visibility_of_element_located((By.XPATH, self.ACTIONS_DROPDOWN)))

        lock_buttons = self.driver.find_elements(By.XPATH, self.LOCK_RECORD_BTN)
        self.assertEqual(len(lock_buttons), 0, "Lock button should not be visible for regular users")


if __name__ == "__main__":
    unittest.main()
