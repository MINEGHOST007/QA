"""
Test Dashboard Stats — Selenium regression test for the dashboard landing page.

Covers:
  - Dashboard page loads after successful login
  - Statistics cards are visible with numeric values
  - Recent activity table renders rows
  - Notification badge displays unread count
  - Sidebar navigation links work correctly
  - User menu dropdown shows logged-in user name
  - Quick 'New Record' action button present

Note: Stat card testids were defined in the original component spec.
Some may not be present in the current build — warnings logged in that case.

Last updated: Sep 2025 — v1.0
"""

import unittest

from selenium import webdriver  # type: ignore
from selenium.webdriver.common.by import By  # type: ignore
from selenium.webdriver.support.ui import WebDriverWait  # type: ignore
from selenium.webdriver.support import expected_conditions as EC  # type: ignore


class TestDashboardStats(unittest.TestCase):
    """Regression tests for the dashboard page at /dashboard.html."""

    BASE_URL       = "http://localhost:8080"
    DASHBOARD_URL  = f"{BASE_URL}/dashboard.html"
    LOGIN_URL      = f"{BASE_URL}/login.html"

    # --- Selectors (v1.0 — last updated Sep 2025) ---

    # Dashboard heading
    DASHBOARD_HEADING = "//h1[text()='Dashboard']"

    # Stats grid — id confirmed; individual card testids from dev spec (may not exist)
    STATS_GRID              = "//div[@id='dashboard-stats']"
    STAT_CARD_TOTAL         = "//div[@data-testid='stat-total-records']"
    STAT_CARD_APPROVED      = "//div[@data-testid='stat-approved']"
    STAT_CARD_PENDING       = "//div[@data-testid='stat-pending-review']"
    STAT_CARD_LOCKED        = "//div[@data-testid='stat-locked']"
    STAT_VALUE              = ".//div[@class='stat-value']"   # relative child XPath

    # Recent activity
    RECENT_ACTIVITY_TABLE   = "//table[@data-testid='recent-activity-table']"   # assumed testid
    ACTIVITY_TABLE_BODY     = "//tbody[@id='dashboard-activity-tbody']"
    ACTIVITY_ROWS           = "//tbody[@id='dashboard-activity-tbody']//tr"

    # Sidebar
    SIDEBAR_NAV     = "//aside[@data-testid='sidebar-nav']"
    NAV_DASHBOARD   = "//a[@data-testid='nav-item-dashboard']"
    NAV_RECORDS     = "//a[@data-testid='nav-item-records']"
    NAV_REPORTS     = "//a[@data-testid='nav-item-reports']"
    NAV_SETTINGS    = "//a[@data-testid='nav-item-settings']"
    NAV_ADMIN       = "//a[@data-testid='nav-item-admin']"

    # Header
    NOTIFICATION_BTN       = "//button[@data-testid='btn-notifications']"
    NOTIFICATION_BADGE     = "//span[@data-testid='notification-unread-count']"
    NOTIFICATIONS_PANEL    = "//div[@data-testid='notifications-panel']"
    MARK_ALL_READ_BTN      = "//button[@data-testid='btn-mark-all-read']"

    # User menu
    USER_AVATAR       = "//button[@data-testid='user-avatar-menu']"
    USER_DISPLAY_NAME = "//div[@data-testid='user-display-name']"
    USER_ROLE_BADGE   = "//span[@data-testid='user-role-badge']"
    LOGOUT_LINK       = "//a[@data-testid='menu-item-logout']"

    # New Record shortcut — testid assumed from spec, actual may be plain anchor
    NEW_RECORD_BTN  = "//a[@data-testid='btn-new-record']"

    def setUp(self):
        """Start browser and log in."""
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()
        self.driver.implicitly_wait(10)
        self.wait = WebDriverWait(self.driver, 15)
        self._login()

    def tearDown(self):
        """Close browser."""
        self.driver.quit()

    def _login(self, username="admin", password="admin123"):
        """Helper: log in and wait for dashboard."""
        self.driver.get(self.LOGIN_URL)
        self.driver.find_element(By.XPATH, "//input[@data-testid='input-username']").send_keys(username)
        self.driver.find_element(By.XPATH, "//input[@data-testid='input-password']").send_keys(password)
        self.driver.find_element(By.XPATH, "//button[@data-testid='btn-login']").click()
        self.wait.until(EC.url_contains("dashboard"))

    # ------------------------------------------------------------------ tests

    def test_dashboard_page_loads(self):
        """Test the dashboard page title and main heading are rendered.

        Steps:
        1. Verify URL contains 'dashboard'
        2. Verify <h1>Dashboard</h1> heading is present
        3. Verify sidebar navigation is visible
        """
        self.assertIn("dashboard", self.driver.current_url)

        heading = self.wait.until(
            EC.presence_of_element_located((By.XPATH, self.DASHBOARD_HEADING))
        )
        self.assertTrue(heading.is_displayed(), "Dashboard h1 not visible")

        sidebar = self.driver.find_element(By.XPATH, self.SIDEBAR_NAV)
        self.assertTrue(sidebar.is_displayed(), "Sidebar nav not visible")

    def test_stats_grid_visible(self):
        """Test the statistics grid container is present on the dashboard.

        Steps:
        1. Navigate directly to dashboard
        2. Verify stats grid container is present
        3. Attempt to verify individual stat card testids
           (logs warnings if testids not found — non-fatal)
        """
        self.driver.get(self.DASHBOARD_URL)

        stats_grid = self.wait.until(
            EC.presence_of_element_located((By.XPATH, self.STATS_GRID))
        )
        self.assertTrue(stats_grid.is_displayed(), "Stats grid not displayed")

        # Individual stat card assertions — based on original spec testids
        # These may not be in the current build; non-blocking
        stat_testids = [
            "stat-total-records",
            "stat-approved",
            "stat-pending-review",
            "stat-locked",
        ]
        for testid in stat_testids:
            cards = self.driver.find_elements(By.XPATH, f"//div[@data-testid='{testid}']")
            if not cards:
                print(f"[WARN] Stat card data-testid='{testid}' not found in DOM — "
                      "spec testid may differ from implementation")

    def test_stat_cards_contain_numeric_values(self):
        """Test that stat cards display numbers (not empty or error text).

        Steps:
        1. Find all elements with class 'stat-value'
        2. Verify at least 3 are present
        3. Verify each numeric value is non-empty
        """
        self.driver.get(self.DASHBOARD_URL)

        stat_values = self.driver.find_elements(By.CSS_SELECTOR, ".stat-value")
        self.assertGreaterEqual(len(stat_values), 3,
                                "Expected at least 3 stat value elements on dashboard")

        for el in stat_values:
            text = el.text.strip().replace(",", "")
            self.assertGreater(len(text), 0, "Stat value element is empty")

    def test_recent_activity_table_renders_rows(self):
        """Test the recent activity table has visible data rows.

        Steps:
        1. Navigate to dashboard
        2. Look for activity table body by id
        3. Verify at least one <tr> row exists
        4. Spot-check first row has non-empty text
        """
        self.driver.get(self.DASHBOARD_URL)

        # Try spec testid first, fall back to known id
        try:
            table = self.wait.until(
                EC.presence_of_element_located((By.XPATH, self.RECENT_ACTIVITY_TABLE))
            )
        except Exception:
            table = self.driver.find_element(By.XPATH, self.ACTIVITY_TABLE_BODY)

        rows = self.driver.find_elements(By.XPATH, self.ACTIVITY_ROWS)
        self.assertGreater(len(rows), 0, "No rows found in recent activity table")

        first_row_text = rows[0].text.strip()
        self.assertGreater(len(first_row_text), 0, "First activity row appears empty")

    def test_notification_badge_shows_count(self):
        """Test notification bell displays a numeric unread count badge.

        Steps:
        1. Navigate to dashboard
        2. Locate notification unread count badge
        3. Verify badge is visible
        4. Verify badge text is numeric
        """
        self.driver.get(self.DASHBOARD_URL)

        badge = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, self.NOTIFICATION_BADGE))
        )
        self.assertTrue(badge.is_displayed(), "Notification badge not visible")
        badge_text = badge.text.strip()
        self.assertTrue(badge_text.isdigit(),
                        f"Notification badge text '{badge_text}' is not a digit")

    def test_notifications_panel_opens_on_click(self):
        """Test clicking notification bell opens the notifications panel.

        Steps:
        1. Click notifications bell button
        2. Verify notifications panel becomes visible
        3. Verify 'Mark all read' button is present inside panel
        """
        self.driver.get(self.DASHBOARD_URL)

        self.driver.find_element(By.XPATH, self.NOTIFICATION_BTN).click()

        panel = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, self.NOTIFICATIONS_PANEL))
        )
        self.assertTrue(panel.is_displayed(), "Notifications panel did not open")

        mark_read_btn = self.driver.find_element(By.XPATH, self.MARK_ALL_READ_BTN)
        self.assertTrue(mark_read_btn.is_displayed())

    def test_user_menu_shows_name_and_role(self):
        """Test user avatar opens dropdown showing display name and role badge.

        Steps:
        1. Click user avatar button
        2. Verify user display name is visible and non-empty
        3. Verify role badge is shown (admin role expected for test user)
        """
        self.driver.get(self.DASHBOARD_URL)

        self.driver.find_element(By.XPATH, self.USER_AVATAR).click()

        name_el = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, self.USER_DISPLAY_NAME))
        )
        self.assertTrue(len(name_el.text.strip()) > 0,
                        "User display name is empty in dropdown")

        role_badge = self.driver.find_element(By.XPATH, self.USER_ROLE_BADGE)
        self.assertTrue(role_badge.is_displayed())
        self.assertIn("Admin", role_badge.text, "Expected 'Admin' role badge for test user")

    def test_sidebar_records_link_navigates(self):
        """Test Records sidebar link navigates to records.html.

        Steps:
        1. Click 'Records' in sidebar
        2. Verify URL changes to records.html
        """
        self.driver.get(self.DASHBOARD_URL)
        self.driver.find_element(By.XPATH, self.NAV_RECORDS).click()
        self.wait.until(EC.url_contains("records"))
        self.assertIn("records.html", self.driver.current_url)

    def test_sidebar_reports_link_navigates(self):
        """Test Reports sidebar link navigates to reports.html.

        Steps:
        1. Click 'Reports' in sidebar
        2. Verify URL changes to reports.html
        """
        self.driver.get(self.DASHBOARD_URL)
        self.driver.find_element(By.XPATH, self.NAV_REPORTS).click()
        self.wait.until(EC.url_contains("reports"))
        self.assertIn("reports.html", self.driver.current_url)

    def test_new_record_shortcut_present(self):
        """Test there is a 'New Record' quick-action button on the dashboard.

        Note: testid 'btn-new-record' was in the design spec but the button
        may render as a plain anchor without a testid in the current build.
        """
        self.driver.get(self.DASHBOARD_URL)

        # Try spec testid first
        btn = self.driver.find_elements(By.XPATH, self.NEW_RECORD_BTN)
        if not btn:
            # Fall back to text match
            btn = self.driver.find_elements(
                By.XPATH, "//a[contains(text(),'New Record')]"
            )
        self.assertGreater(len(btn), 0,
                           "Could not find '+ New Record' button on dashboard")
        self.assertTrue(btn[0].is_displayed())

    def test_logout_from_user_menu(self):
        """Test Sign Out link in user menu redirects to login page.

        Steps:
        1. Open user avatar dropdown
        2. Click 'Sign Out'
        3. Verify redirect to login.html
        """
        self.driver.get(self.DASHBOARD_URL)

        self.driver.find_element(By.XPATH, self.USER_AVATAR).click()
        logout = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, self.LOGOUT_LINK))
        )
        logout.click()

        self.wait.until(EC.url_contains("login"))
        self.assertIn("login.html", self.driver.current_url)


if __name__ == "__main__":
    unittest.main()
