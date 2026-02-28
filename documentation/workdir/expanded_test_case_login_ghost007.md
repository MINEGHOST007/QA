## Test Case: Login with ghost007 and ghost007 as username and password and verify the dashboard loads

### Pre-conditions
- URL: http://localhost:8080/login.html
- User role: Any (Login page is public)
- Application state: Initial application state

### Steps

| # | Action | Locator / Selector | Expected Result |
|---|--------|--------------------|-----------------|
| 1 | Navigate to login page | N/A | Browser opens `http://localhost:8080/login.html` |
| 2 | Enter username | `[data-testid="input-username"]` | "ghost007" appears in username field |
| 3 | Enter password | `[data-testid="input-password"]` | "ghost007" appears in password field (masked) |
| 4 | Click Sign In | `[data-testid="btn-login"]` | Form submits, button may show loading state |
| 5 | Verify successful login | URL check or dashboard presence | Browser redirects to `http://localhost:8080/dashboard.html` |

### Post-conditions
- User is authenticated and dashboard is displayed
- URL has changed to dashboard.html
- Main content area is visible and accessible

### Key References
- **URL(s)**: 
  - Login: `http://localhost:8080/login.html`
  - Dashboard: `http://localhost:8080/dashboard.html`
- **Selectors**:
  - Username field: `[data-testid="input-username"]`
  - Password field: `[data-testid="input-password"]`
  - Sign In button: `[data-testid="btn-login"]`
- **Related keywords**: Login form, authentication, username field, password field, primary action button

### Documentation Gaps
- **Submit button**: The login navigation guide specifies `[data-testid="btn-login"]` but the keywords guide mentions a "Sign In" button without specifying the data-testid. Need verification.
- **Test credentials**: The documentation shows valid credentials as `admin` / `admin123`, but test case uses `ghost007` / `ghost007`. The username `ghost007` may not be a valid test credential and could fail authentication.
- **Login form**: No specific "login form" keyword entry was found, though individual fields are documented.