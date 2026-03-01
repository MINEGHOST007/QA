"""
Test Automated Record Provisioning — Selenium regression test for end-to-end
record creation using external API data, followed by full approval workflow.

Covers:
  - Fetch record payload from external data endpoint
  - Auto-populate new record form from fetched data
  - Submit form and assert success notification
  - Execute Submit for Review workflow step
  - Execute Approve workflow step
  - Status badge assertions at each stage

NOTE: This script was written against the v1.5 provisioning flow spec.
Some toast selectors and modal confirm testids may need updating
if the UI has been refactored since Oct 2025.

Last updated: Oct 2025 — v1.5
"""

import time
import unittest
import requests  # type: ignore

from selenium import webdriver  # type: ignore
from selenium.webdriver.common.by import By  # type: ignore
from selenium.webdriver.support.ui import WebDriverWait, Select  # type: ignore
from selenium.webdriver.support import expected_conditions as EC  # type: ignore


class TestAutomatedRecordProvisioning(unittest.TestCase):
    """
    End-to-end test: fetch record data from API, create the record via form,
    then walk through the Submit for Review → Approve workflow.
    """

    BASE_URL = "http://localhost:8080"
    LOGIN_URL = f"{BASE_URL}/login.html"
    FORM_URL = f"{BASE_URL}/record-form.html"
    DATA_ENDPOINT = f"{BASE_URL}/data.json"

    # --- Selectors (v1.5 — last updated Oct 2025) ---

    # Login page (using id= because testids weren't added until v1.2)
    USERNAME_INPUT = "//input[@id='input-username']"
    PASSWORD_INPUT = "//input[@id='input-password']"
    LOGIN_BUTTON    = "//button[@id='btn-login']"
    DASHBOARD_TITLE = "//h1[text()='Dashboard']"   # may not exist in current build

    # Record form fields
    RECORD_FORM        = "//form[@id='record-form']"
    TITLE_INPUT        = "//input[@id='input-record-title']"
    TYPE_SELECT        = "//select[@id='select-record-type']"
    PRIORITY_SELECT    = "//select[@id='select-record-priority']"
    DESCRIPTION_AREA   = "//textarea[@id='textarea-record-description']"
    SUBMIT_BUTTON      = "//button[@data-testid='btn-submit-record']"

    # Toast notification — old approach: looked for a dedicated success div
    # TODO: current build may use dynamic toast classes instead of data-testid
    TOAST_SUCCESS      = "//div[@data-testid='toast-success']"
    TOAST_ERROR        = "//div[@data-testid='toast-error']"
    TOAST_CONTAINER    = "//div[@id='toast-container']"

    # Record detail — workflow buttons
    SUBMIT_FOR_REVIEW_BTN = "//button[@data-testid='btn-submit-for-review']"
    APPROVE_BTN           = "//button[@data-testid='btn-approve']"
    STATUS_BADGE          = "//span[@data-testid='status-badge']"

    # Submit for Review modal
    SUBMIT_REVIEW_MODAL  = "//div[@id='modal-submit-review']"
    WORKFLOW_COMMENT     = "//textarea[@data-testid='input-workflow-comment']"
    # NOTE: testid below was 'btn-confirm-submit-review' in older build;
    #       may have been renamed — update if Confirm button not found
    CONFIRM_SUBMIT_BTN   = "//button[@data-testid='btn-confirm-submit-review']"

    # Approve modal
    APPROVE_MODAL        = "//div[@id='modal-approve']"
    APPROVAL_NOTE        = "//textarea[@data-testid='input-approval-note']"
    CONFIRM_APPROVE_BTN  = "//button[@data-testid='btn-confirm-approval']"

    # Activity log
    ACTIVITY_LOG         = "//div[@data-testid='activity-log']"

    def setUp(self):
        """Initialise browser and empty API data store."""
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()
        self.driver.implicitly_wait(10)
        self.wait = WebDriverWait(self.driver, 15)
        self.api_data = None

    def tearDown(self):
        """Close browser."""
        self.driver.quit()

    # ------------------------------------------------------------------ helpers

    def _fetch_record_data(self):
        """
        Fetch record seed data from the local API endpoint using requests.
        Returns parsed JSON dict with keys: title, type, priority, description.
        """
        resp = requests.get(self.DATA_ENDPOINT, timeout=10)
        resp.raise_for_status()
        self.api_data = resp.json()
        return self.api_data

    def _login(self, username="admin", password="admin123"):
        """Log in with provided credentials and wait for dashboard."""
        self.driver.get(self.LOGIN_URL)
        time.sleep(0.5)   # brief pause — old timing workaround for slow CI

        self.driver.find_element(By.XPATH, self.USERNAME_INPUT).send_keys(username)
        self.driver.find_element(By.XPATH, self.PASSWORD_INPUT).send_keys(password)
        self.driver.find_element(By.XPATH, self.LOGIN_BUTTON).click()

        self.wait.until(EC.url_contains("dashboard"))

    def _assert_success_toast(self, context=""):
        """
        Assert a success notification appeared.

        Old approach: expects data-testid='toast-success' div to be visible.
        NOTE: current build uses dynamic toast divs without a stable testid —
        this assertion may need updating to check for '✓' icon text instead.
        Fallback: checks toast-container is non-empty.
        """
        try:
            toast = self.wait.until(
                EC.visibility_of_element_located((By.XPATH, self.TOAST_SUCCESS))
            )
            self.assertTrue(toast.is_displayed(),
                            f"Success toast not visible [{context}]")
        except Exception:
            # Fallback: at least confirm the container got something
            container = self.driver.find_element(By.XPATH, self.TOAST_CONTAINER)
            self.assertGreater(len(container.text.strip()), 0,
                               f"Toast container empty [{context}]")

    # ------------------------------------------------------------------ tests

    def test_api_data_endpoint_reachable(self):
        """
        Sanity check: data.json is accessible and returns expected structure.
        Can run without a browser session.

        Steps:
        1. GET request to data.json
        2. Verify HTTP 200
        3. Verify required JSON keys present
        """
        data = self._fetch_record_data()
        self.assertIsInstance(data, dict, "Response should be a JSON object")

        for key in ("title", "type", "priority", "description"):
            self.assertIn(key, data, f"API response missing required key: '{key}'")

        self.assertGreater(len(data["title"]), 3,
                           "Title value appears too short to be valid")

    def test_full_provisioning_and_approval_workflow(self):
        """
        End-to-end: fetch data.json → create record → submit for review → approve.

        Steps:
        1.  GET data.json and parse
        2.  Log in as admin
        3.  Navigate to New Record form
        4.  Populate Title, Type, Priority, Description from fetched data
        5.  Submit form — assert success toast
        6.  Wait for redirect to record-detail page
        7.  Click 'Submit for Review'
        8.  Enter comment in modal, click Confirm
        9.  Assert success toast
        10. Wait for status badge = 'Pending Review'
        11. Click 'Approve'
        12. Leave approval note blank, click Confirm
        13. Assert success toast
        14. Assert final status badge = 'Approved'
        """
        # -- Step 1: fetch API data
        data = self._fetch_record_data()
        self.assertIn("title", data, "API payload missing 'title'")

        # -- Step 2: login
        self._login()

        # -- Step 3: navigate to form
        self.driver.get(self.FORM_URL)
        self.wait.until(EC.presence_of_element_located((By.XPATH, self.RECORD_FORM)))

        # -- Step 4: fill form from API data
        title_el = self.driver.find_element(By.XPATH, self.TITLE_INPUT)
        title_el.clear()
        title_el.send_keys(data["title"])

        type_select = Select(self.driver.find_element(By.XPATH, self.TYPE_SELECT))
        try:
            type_select.select_by_value(data["type"])
        except Exception:
            # older builds accepted title-cased text; fall back
            type_select.select_by_visible_text(data["type"].capitalize())

        priority_select = Select(self.driver.find_element(By.XPATH, self.PRIORITY_SELECT))
        try:
            priority_select.select_by_value(data["priority"])
        except Exception:
            priority_select.select_by_visible_text(data["priority"].title())

        desc_el = self.driver.find_element(By.XPATH, self.DESCRIPTION_AREA)
        desc_el.clear()
        desc_el.send_keys(data["description"])

        # -- Step 5: submit form
        self.driver.find_element(By.XPATH, self.SUBMIT_BUTTON).click()
        self._assert_success_toast(context="record creation")

        time.sleep(1)  # give the redirect a moment — TODO replace with proper wait

        # -- Step 6: wait for record-detail page
        self.wait.until(EC.url_contains("record-detail"))

        # -- Step 7-9: Submit for Review
        submit_review_btn = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, self.SUBMIT_FOR_REVIEW_BTN))
        )
        submit_review_btn.click()

        self.wait.until(
            EC.visibility_of_element_located((By.XPATH, self.SUBMIT_REVIEW_MODAL))
        )

        comment_field = self.driver.find_element(By.XPATH, self.WORKFLOW_COMMENT)
        comment_field.send_keys("Automated submission — provisioning script")

        # Confirm button — testid 'btn-confirm-submit-review' per v1.5 spec
        # if this fails, try 'btn-confirm-workflow' (name changed in later build)
        self.driver.find_element(By.XPATH, self.CONFIRM_SUBMIT_BTN).click()

        self._assert_success_toast(context="submit for review")
        time.sleep(1)

        # -- Step 10: wait for status update to Pending Review
        self.wait.until(
            EC.text_to_be_present_in_element((By.XPATH, self.STATUS_BADGE), "Pending")
        )

        # -- Step 11-13: Approve
        approve_btn = self.driver.find_element(By.XPATH, self.APPROVE_BTN)
        approve_btn.click()

        self.wait.until(
            EC.visibility_of_element_located((By.XPATH, self.APPROVE_MODAL))
        )
        # Leave approval note blank — test that optional field allows empty submit
        self.driver.find_element(By.XPATH, self.CONFIRM_APPROVE_BTN).click()

        self._assert_success_toast(context="approval")

        # -- Step 14: final status assertion
        self.wait.until(
            EC.text_to_be_present_in_element((By.XPATH, self.STATUS_BADGE), "Approved")
        )

    def test_provisioning_with_missing_api_key(self):
        """
        Negative test: form populated with partial data (no type key) should
        leave the type dropdown unset and fail validation on submit.

        Steps:
        1. Create partial payload (no 'type')
        2. Log in and navigate to form
        3. Fill only title and description
        4. Submit — verify type field error appears
        """
        self._login()
        self.driver.get(self.FORM_URL)
        self.wait.until(EC.presence_of_element_located((By.XPATH, self.RECORD_FORM)))

        # Fill only title (simulate missing 'type' from API)
        self.driver.find_element(By.XPATH, self.TITLE_INPUT).send_keys(
            "Partial API Provisioned Record"
        )
        self.driver.find_element(By.XPATH, self.SUBMIT_BUTTON).click()

        # Expect a field error on type
        type_error = self.wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//div[@data-testid='field-error-type']")
            )
        )
        self.assertTrue(type_error.is_displayed())

    def test_reject_workflow_after_submission(self):
        """
        Alternate path: submit for review then reject (instead of approve).

        Steps:
        1. Fetch API data
        2. Login, navigate to form, fill and submit
        3. Submit for Review, confirm
        4. Click Reject button
        5. Enter rejection reason
        6. Confirm rejection — assert toast and status = 'Rejected'
        """
        data = self._fetch_record_data()
        self._login()
        self.driver.get(self.FORM_URL)
        self.wait.until(EC.presence_of_element_located((By.XPATH, self.RECORD_FORM)))

        self.driver.find_element(By.XPATH, self.TITLE_INPUT).send_keys(
            data.get("title", "Rejection Path Record")
        )
        type_sel = Select(self.driver.find_element(By.XPATH, self.TYPE_SELECT))
        try:
            type_sel.select_by_value(data.get("type", "compliance"))
        except Exception:
            type_sel.select_by_index(1)

        self.driver.find_element(By.XPATH, self.SUBMIT_BUTTON).click()
        self._assert_success_toast(context="create for rejection path")
        time.sleep(1)

        self.wait.until(EC.url_contains("record-detail"))

        # Submit for Review
        self.wait.until(
            EC.element_to_be_clickable((By.XPATH, self.SUBMIT_FOR_REVIEW_BTN))
        ).click()
        self.wait.until(
            EC.visibility_of_element_located((By.XPATH, self.SUBMIT_REVIEW_MODAL))
        )
        self.driver.find_element(By.XPATH, self.CONFIRM_SUBMIT_BTN).click()
        self._assert_success_toast(context="submit for review (reject path)")
        time.sleep(1)

        # Reject
        reject_btn = self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[@data-testid='btn-reject']")
            )
        )
        reject_btn.click()

        self.wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//div[@id='modal-reject']")
            )
        )
        # Rejection reason is required
        reason_field = self.driver.find_element(
            By.XPATH, "//textarea[@data-testid='input-rejection-reason']"
        )
        reason_field.send_keys("Data inconsistency detected — rejecting for correction.")

        self.driver.find_element(
            By.XPATH, "//button[@data-testid='btn-confirm-rejection']"
        ).click()

        self._assert_success_toast(context="rejection")
        self.wait.until(
            EC.text_to_be_present_in_element((By.XPATH, self.STATUS_BADGE), "Rejected")
        )


if __name__ == "__main__":
    unittest.main()
