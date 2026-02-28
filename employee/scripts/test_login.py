"""
Test Login Page — Selenium regression test for user authentication.

Covers:
  - Valid login with correct credentials
  - Invalid login with wrong password
  - Empty field validation
  - Remember me checkbox
  - Forgot password link navigation
"""

import time
import unittest
from selenium import webdriver # type: ignore
from selenium.webdriver.common.by import By # type: ignore
from selenium.webdriver.support.ui import WebDriverWait # type: ignore
from selenium.webdriver.support import expected_conditions as EC # type: ignore


class TestLoginPage(unittest.TestCase):
    """Regression tests for the login page."""

    BASE_URL = "http://localhost:8080"
    LOGIN_URL = f"{BASE_URL}/login.html"

    # --- XPaths and Selectors (v1.2 — last updated Jan 2026) ---
    USERNAME_INPUT = "//input[@data-testid='input-username']"
    PASSWORD_INPUT = "//input[@data-testid='input-password']"
    LOGIN_BUTTON = "//button[@data-testid='btn-login']"
    REMEMBER_ME_CHECKBOX = "//input[@data-testid='checkbox-remember-me']"
    FORGOT_PASSWORD_LINK = "//a[@data-testid='link-forgot-password']"
    ERROR_MESSAGE = "//div[@data-testid='alert-login-error']"
    SUCCESS_TOAST = "//div[@data-testid='toast-success']"
    DASHBOARD_HEADER = "//h1[text()='Dashboard']"

    def setUp(self):
        """Set up browser driver before each test."""
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()
        self.driver.implicitly_wait(10)
        self.wait = WebDriverWait(self.driver, 15)

    def tearDown(self):
        """Close browser after each test."""
        self.driver.quit()

    def test_valid_login(self):
        """Test successful login with valid credentials.

        Steps:
        1. Navigate to login page
        2. Enter valid username
        3. Enter valid password
        4. Click Sign In button
        5. Verify redirect to dashboard
        6. Verify dashboard heading appears
        """
        self.driver.get(self.LOGIN_URL)

        # Enter credentials
        username_field = self.driver.find_element(By.XPATH, self.USERNAME_INPUT)
        username_field.clear()
        username_field.send_keys("admin")

        password_field = self.driver.find_element(By.XPATH, self.PASSWORD_INPUT)
        password_field.clear()
        password_field.send_keys("admin123")

        # Click login
        login_btn = self.driver.find_element(By.XPATH, self.LOGIN_BUTTON)
        login_btn.click()

        # Verify dashboard loaded
        self.wait.until(EC.presence_of_element_located((By.XPATH, self.DASHBOARD_HEADER)))
        self.assertIn("dashboard", self.driver.current_url)

    def test_invalid_password(self):
        """Test login failure with wrong password.

        Steps:
        1. Navigate to login page
        2. Enter valid username
        3. Enter wrong password
        4. Click Sign In button
        5. Verify error message displayed
        6. Verify still on login page
        """
        self.driver.get(self.LOGIN_URL)

        self.driver.find_element(By.XPATH, self.USERNAME_INPUT).send_keys("admin")
        self.driver.find_element(By.XPATH, self.PASSWORD_INPUT).send_keys("WrongPass!")
        self.driver.find_element(By.XPATH, self.LOGIN_BUTTON).click()

        # Verify error
        error = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, self.ERROR_MESSAGE))
        )
        self.assertIn("Invalid", error.text)
        self.assertIn("login.html", self.driver.current_url)

    def test_empty_fields_validation(self):
        """Test that submitting empty form shows validation errors.

        Steps:
        1. Navigate to login page
        2. Click Sign In without entering any data
        3. Verify error banner appears
        """
        self.driver.get(self.LOGIN_URL)
        self.driver.find_element(By.XPATH, self.LOGIN_BUTTON).click()

        error = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, self.ERROR_MESSAGE))
        )
        self.assertTrue(error.is_displayed())

    def test_remember_me_checkbox(self):
        """Test remember me functionality persists session.

        Steps:
        1. Navigate to login page
        2. Enter valid credentials
        3. Check the Remember Me checkbox
        4. Click Sign In
        5. Verify checkbox stores cookie
        """
        self.driver.get(self.LOGIN_URL)

        self.driver.find_element(By.XPATH, self.USERNAME_INPUT).send_keys("admin")
        self.driver.find_element(By.XPATH, self.PASSWORD_INPUT).send_keys("admin123")

        remember_me = self.driver.find_element(By.XPATH, self.REMEMBER_ME_CHECKBOX)
        if not remember_me.is_selected():
            remember_me.click()

        self.driver.find_element(By.XPATH, self.LOGIN_BUTTON).click()

        self.wait.until(EC.presence_of_element_located((By.XPATH, self.DASHBOARD_HEADER)))
        cookies = self.driver.get_cookies()
        cookie_names = [c["name"] for c in cookies]
        self.assertIn("remember_token", cookie_names)

    def test_forgot_password_link(self):
        """Test forgot password link navigates to reset page.

        Steps:
        1. Navigate to login page
        2. Click Forgot Password link
        3. Verify navigation to password reset page
        """
        self.driver.get(self.LOGIN_URL)

        forgot_link = self.driver.find_element(By.XPATH, self.FORGOT_PASSWORD_LINK)
        forgot_link.click()

        self.wait.until(EC.url_contains("forgot-password"))
        self.assertIn("forgot-password", self.driver.current_url)


if __name__ == "__main__":
    unittest.main()
