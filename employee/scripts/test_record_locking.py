"""
Test Record Locking — Selenium regression test for the record lock/unlock workflow.

Covers:
  - Lock an approved record
  - Verify locked status badge
  - Verify edit button disabled when locked
  - Unlock a locked record
  - Permission check: non-admin cannot lock
"""

import unittest
from selenium import webdriver # type: ignore
from selenium.webdriver.common.by import By # type: ignore
from selenium.webdriver.support.ui import WebDriverWait # type: ignore
from selenium.webdriver.support import expected_conditions as EC # type: ignore


class TestRecordLocking(unittest.TestCase):
    """Regression tests for record lock/unlock at /records/{id}."""

    BASE_URL = "https://app.example.com"
    RECORDS_LIST_URL = f"{BASE_URL}/records"

    # --- XPaths and Selectors ---
    RECORD_ROW = "//tr[@data-testid='record-row-{id}']"
    RECORD_LINK = "//tr[@data-testid='record-row-{id}']//a[@data-testid='record-link']"
    STATUS_BADGE = "//span[@data-testid='record-status-badge']"
    LOCK_BUTTON = "//button[@data-testid='btn-lock-record']"
    UNLOCK_BUTTON = "//button[@data-testid='btn-unlock-record']"
    EDIT_BUTTON = "//button[@data-testid='btn-edit-record']"
    ACTIONS_MENU = "//button[@data-testid='actions-menu-trigger']"
    ACTIONS_DROPDOWN = "//div[@data-testid='actions-dropdown']"
    CONFIRM_MODAL = "//div[@data-testid='confirm-modal']"
    CONFIRM_YES_BUTTON = "//button[@data-testid='confirm-yes-btn']"
    CONFIRM_NO_BUTTON = "//button[@data-testid='confirm-no-btn']"
    TOAST_SUCCESS = "//div[@data-testid='toast-success']"
    TOAST_ERROR = "//div[@data-testid='toast-error']"
    BREADCRUMB = "//nav[@data-testid='breadcrumb']"

    # Test data
    APPROVED_RECORD_ID = "REC-001"

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
        self.driver.get(f"{self.BASE_URL}/auth/login")
        self.driver.find_element(By.XPATH, "//input[@data-testid='login-username']").send_keys("admin@example.com")
        self.driver.find_element(By.XPATH, "//input[@data-testid='login-password']").send_keys("AdminPass123!")
        self.driver.find_element(By.XPATH, "//button[@data-testid='login-submit-btn']").click()
        self.wait.until(EC.url_contains("/dashboard"))

    def _navigate_to_record(self, record_id: str):
        """Helper: navigate to a specific record's detail page."""
        self.driver.get(self.RECORDS_LIST_URL)
        record_link = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, self.RECORD_LINK.format(id=record_id)))
        )
        record_link.click()
        self.wait.until(EC.presence_of_element_located((By.XPATH, self.STATUS_BADGE)))

    def test_lock_approved_record(self):
        """Test locking an approved record changes its status to Locked.

        Pre-conditions:
        - User is logged in as admin
        - Record REC-001 exists with status 'Approved'

        Steps:
        1. Navigate to records list
        2. Click on record REC-001
        3. Verify status badge shows 'Approved'
        4. Click Actions menu
        5. Click Lock Record button
        6. Confirm in the confirmation modal
        7. Verify success toast appears
        8. Verify status badge changes to 'Locked'
        9. Verify the edit button is now disabled
        """
        self._navigate_to_record(self.APPROVED_RECORD_ID)

        # Verify initial status
        status = self.driver.find_element(By.XPATH, self.STATUS_BADGE)
        self.assertEqual(status.text.strip(), "Approved")

        # Open actions menu and click Lock
        self.driver.find_element(By.XPATH, self.ACTIONS_MENU).click()
        self.wait.until(EC.visibility_of_element_located((By.XPATH, self.ACTIONS_DROPDOWN)))

        lock_btn = self.driver.find_element(By.XPATH, self.LOCK_BUTTON)
        lock_btn.click()

        # Confirm modal
        self.wait.until(EC.visibility_of_element_located((By.XPATH, self.CONFIRM_MODAL)))
        self.driver.find_element(By.XPATH, self.CONFIRM_YES_BUTTON).click()

        # Verify success
        toast = self.wait.until(EC.visibility_of_element_located((By.XPATH, self.TOAST_SUCCESS)))
        self.assertIn("locked", toast.text.lower())

        # Verify status changed
        self.wait.until(EC.text_to_be_present_in_element((By.XPATH, self.STATUS_BADGE), "Locked"))
        status = self.driver.find_element(By.XPATH, self.STATUS_BADGE)
        self.assertEqual(status.text.strip(), "Locked")

        # Verify edit button is disabled
        edit_btn = self.driver.find_element(By.XPATH, self.EDIT_BUTTON)
        self.assertFalse(edit_btn.is_enabled())

    def test_unlock_locked_record(self):
        """Test unlocking a locked record restores it to Approved status.

        Steps:
        1. Navigate to a locked record
        2. Click Actions menu
        3. Click Unlock Record
        4. Confirm in modal
        5. Verify status changes to 'Approved'
        6. Verify edit button is enabled again
        """
        self._navigate_to_record(self.APPROVED_RECORD_ID)

        # Open actions and unlock
        self.driver.find_element(By.XPATH, self.ACTIONS_MENU).click()
        self.wait.until(EC.visibility_of_element_located((By.XPATH, self.ACTIONS_DROPDOWN)))

        unlock_btn = self.driver.find_element(By.XPATH, self.UNLOCK_BUTTON)
        unlock_btn.click()

        self.wait.until(EC.visibility_of_element_located((By.XPATH, self.CONFIRM_MODAL)))
        self.driver.find_element(By.XPATH, self.CONFIRM_YES_BUTTON).click()

        toast = self.wait.until(EC.visibility_of_element_located((By.XPATH, self.TOAST_SUCCESS)))
        self.assertIn("unlocked", toast.text.lower())

        self.wait.until(EC.text_to_be_present_in_element((By.XPATH, self.STATUS_BADGE), "Approved"))

        edit_btn = self.driver.find_element(By.XPATH, self.EDIT_BUTTON)
        self.assertTrue(edit_btn.is_enabled())

    def test_non_admin_cannot_lock(self):
        """Test that a regular user cannot see the Lock Record option.

        Steps:
        1. Login as regular user (not admin)
        2. Navigate to an approved record
        3. Open Actions menu
        4. Verify Lock Record button is NOT present
        """
        # Re-login as regular user
        self.driver.get(f"{self.BASE_URL}/auth/login")
        self.driver.find_element(By.XPATH, "//input[@data-testid='login-username']").send_keys("user@example.com")
        self.driver.find_element(By.XPATH, "//input[@data-testid='login-password']").send_keys("UserPass123!")
        self.driver.find_element(By.XPATH, "//button[@data-testid='login-submit-btn']").click()
        self.wait.until(EC.url_contains("/dashboard"))

        self._navigate_to_record(self.APPROVED_RECORD_ID)

        self.driver.find_element(By.XPATH, self.ACTIONS_MENU).click()
        self.wait.until(EC.visibility_of_element_located((By.XPATH, self.ACTIONS_DROPDOWN)))

        lock_buttons = self.driver.find_elements(By.XPATH, self.LOCK_BUTTON)
        self.assertEqual(len(lock_buttons), 0, "Lock button should not be visible for regular users")


if __name__ == "__main__":
    unittest.main()
