"""
Employee Agent — Retired Selenium Script Finder

A deep agent that searches through old Selenium regression test scripts
to find the most similar ones for a given test case.

Usage:
    from employee.employee import create_employee_agent
    agent = create_employee_agent()

CLI:
    uv run python employee/employee.py "Submit the form and verify success"
    uv run python employee/employee.py --rebuild-index
    uv run python employee/employee.py --list-scripts
"""
