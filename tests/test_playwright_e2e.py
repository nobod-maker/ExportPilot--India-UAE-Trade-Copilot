"""Playwright pytest suite for ExportPilot Monad Design System, Auth & Audit Log."""

from __future__ import annotations

import os
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright

BASE_URL = os.getenv("EXPORTPILOT_URL", "http://localhost:8501")
SCREENSHOT_DIR = Path("tests/screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="module")
def browser_context():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1400, "height": 950})
        yield context
        context.close()
        browser.close()


def test_monad_login_gate(browser_context):
    """Verify application gate and Monad warm parchment canvas."""
    page = browser_context.new_page()
    page.goto(BASE_URL, wait_until="networkidle", timeout=30000)

    app_container = page.locator('[data-testid="stAppViewContainer"]')
    app_container.wait_for(state="visible", timeout=20000)

    # Check background color is Monad parchment
    bg_color = app_container.evaluate("el => window.getComputedStyle(el).backgroundColor")
    assert "246, 243, 241" in bg_color

    # Verify login elements are present
    demo_cred = page.locator('text=Demo Credentials').first
    demo_cred.wait_for(state="visible", timeout=15000)
    assert demo_cred.is_visible()
    assert page.locator('button:has-text("Login")').first.is_visible()
    page.close()


def test_exporter_workflow_and_audit_table(browser_context):
    """Verify exporter login, quotation calculation, approval, and aligned audit table."""
    page = browser_context.new_page()
    page.goto(BASE_URL, wait_until="networkidle", timeout=30000)

    # Login as exporter
    page.locator('input[aria-label="Username"], input[type="text"]').first.fill("exporter")
    page.locator('input[aria-label="Password"], input[type="password"]').first.fill("export123")
    page.locator('button:has-text("Login")').first.click()

    # Verify session header
    user_badge = page.locator('text=Logged in as Priya Exporter').first
    user_badge.wait_for(state="visible", timeout=15000)

    # Load sample & calculate
    page.locator('button:has-text("LOAD EN SAMPLE")').first.click()
    page.wait_for_timeout(1000)
    page.locator('button:has-text("SEND TO AGENT")').first.click()

    quote_card = page.locator('text=Commercial Quotation Breakdown').first
    quote_card.wait_for(state="visible", timeout=20000)

    # Human approval gate
    page.locator('button:has-text("APPROVE & SAVE DEAL")').first.click()
    approval_msg = page.locator('text=approved and stored in SQLite database').first
    approval_msg.wait_for(state="visible", timeout=10000)

    # Check Audit table alignment & colgroup
    page.locator('[data-baseweb="tab"]:has-text("AUDIT LOG")').first.click()
    page.wait_for_timeout(1500)

    audit_table = page.locator('table.audit-table').first
    audit_table.wait_for(state="visible", timeout=10000)

    col_widths = page.evaluate(
        """() => {
            const table = document.querySelector('table.audit-table');
            const cols = table.querySelectorAll('colgroup col');
            return Array.from(cols).map(c => c.className);
        }"""
    )
    for expected_col in ["col-time", "col-act", "col-rat", "col-risk", "col-stat", "col-user"]:
        assert expected_col in col_widths

    page.close()


def test_admin_governance(browser_context):
    """Verify Admin authentication and access to full audit log."""
    page = browser_context.new_page()
    page.goto(BASE_URL, wait_until="networkidle", timeout=30000)

    # If logged in as exporter, logout
    logout_btns = page.locator('button:has-text("LOG OUT")')
    if logout_btns.count() > 0:
        logout_btns.first.click()
        page.wait_for_timeout(1000)

    page.locator('input[aria-label="Username"], input[type="text"]').first.fill("admin")
    page.locator('input[aria-label="Password"], input[type="password"]').first.fill("admin123")
    page.locator('button:has-text("Login")').first.click()

    page.locator('text=Logged in as FedAI Control Admin').first.wait_for(state="visible", timeout=15000)
    assert page.locator('text=ADMIN').first.is_visible()

    admin_audit_tab = page.locator('[data-baseweb="tab"]:has-text("AUDIT LOG")').first
    admin_audit_tab.wait_for(state="visible", timeout=10000)
    admin_audit_tab.click(force=True)
    page.wait_for_timeout(2500)

    full_audit_label = page.locator('text=Full Audit Log').first
    full_audit_label.wait_for(state="visible", timeout=15000)
    assert full_audit_label.is_visible()
    page.close()

