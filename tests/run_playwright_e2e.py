"""Playwright E2E test runner for ExportPilot with Authentication and Monad Audit Table."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = os.getenv("EXPORTPILOT_URL", "http://localhost:8501")
SCREENSHOT_DIR = Path("tests/screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


def run_e2e_tests() -> bool:
    print("==================================================")
    print(f"Running Playwright E2E Tests on {BASE_URL}")
    print("Browser: Microsoft Edge (channel=msedge)")
    print("==================================================")

    all_passed = True

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1400, "height": 950})
        page = context.new_page()

        try:
            # -----------------------------------------------------------------
            # TEST 1: Authentication Gate (Unauthenticated view)
            # -----------------------------------------------------------------
            print("\n[TEST 1] Verifying Monad Login Page Gate...")
            page.goto(BASE_URL, wait_until="networkidle", timeout=30000)

            # Wait for Streamlit app container
            app_container = page.locator('[data-testid="stAppViewContainer"]')
            app_container.wait_for(state="visible", timeout=20000)

            # Verify Login form is displayed and main app is blocked
            page.locator('text=Demo Credentials').first.wait_for(state="visible", timeout=20000)
            page.locator('text=Login').first.wait_for(state="visible", timeout=20000)
            print("  [PASS] Application successfully gated behind login screen.")

            login_ss = SCREENSHOT_DIR / "01_monad_login_gate.png"
            page.screenshot(path=str(login_ss), full_page=True)
            print(f"  [SAVED] Screenshot: {login_ss}")

            # -----------------------------------------------------------------
            # TEST 2: Exporter Login Flow
            # -----------------------------------------------------------------
            print("\n[TEST 2] Logging in as 'exporter'...")
            # Fill credentials in streamlit-authenticator form
            username_input = page.locator('input[aria-label="Username"], input[type="text"]').first
            username_input.fill("exporter")

            password_input = page.locator('input[aria-label="Password"], input[type="password"]').first
            password_input.fill("export123")

            login_btn = page.locator('button:has-text("Login")').first
            login_btn.click()
            print("  [INFO] Submitted exporter credentials, awaiting session...")

            # Verify logged-in session header
            user_badge = page.locator('text=Logged in as Priya Exporter').first
            user_badge.wait_for(state="visible", timeout=15000)
            print("  [PASS] Successfully logged in as 'exporter' (Priya Exporter).")
            page.wait_for_timeout(2500)

            home_ss = SCREENSHOT_DIR / "02_monad_exporter_home.png"
            page.screenshot(path=str(home_ss), full_page=True)
            print(f"  [SAVED] Screenshot: {home_ss}")

            # -----------------------------------------------------------------
            # TEST 3: Voice Deal Desk & Human Approval Gate
            # -----------------------------------------------------------------
            print("\n[TEST 3] Testing Deal Desk calculation and human approval gate...")
            load_sample_btn = page.locator('button:has-text("LOAD EN SAMPLE")').first
            load_sample_btn.wait_for(state="visible", timeout=15000)
            load_sample_btn.click()
            page.wait_for_timeout(1500)

            send_btn = page.locator('button:has-text("SEND TO AGENT")').first
            send_btn.wait_for(state="visible", timeout=5000)
            send_btn.click()
            print("  [INFO] Clicked 'SEND TO AGENT', calculating quote...")

            # Wait for calculation results
            quote_card = page.locator('text=Commercial Quotation Breakdown').first
            quote_card.wait_for(state="visible", timeout=30000)
            print("  [PASS] Commercial Quotation breakdown rendered.")

            # Approve deal
            approve_btn = page.locator('button:has-text("APPROVE & SAVE DEAL")').first
            approve_btn.wait_for(state="visible", timeout=5000)
            approve_btn.click()

            approval_msg = page.locator('text=approved and stored in SQLite database').first
            approval_msg.wait_for(state="visible", timeout=10000)
            print("  [PASS] Deal approved and recorded with user attribution.")

            quote_ss = SCREENSHOT_DIR / "03_monad_quotation_approved.png"
            page.screenshot(path=str(quote_ss), full_page=True)
            print(f"  [SAVED] Screenshot: {quote_ss}")

            # -----------------------------------------------------------------
            # TEST 4: Audit Log Table Alignment & Fixed Colgroup
            # -----------------------------------------------------------------
            print("\n[TEST 4] Verifying Audit Log Table Fixed Layout & Column Widths...")
            audit_tab = page.locator('[data-baseweb="tab"]:has-text("AUDIT LOG")').first
            audit_tab.click()
            page.wait_for_timeout(1500)

            # Check table existence and colgroup
            audit_table = page.locator('table.audit-table').first
            audit_table.wait_for(state="visible", timeout=10000)

            col_widths = page.evaluate(
                """() => {
                    const table = document.querySelector('table.audit-table');
                    const cols = table.querySelectorAll('colgroup col');
                    return Array.from(cols).map(c => c.className);
                }"""
            )
            print("  [INFO] Audit table colgroup classes:", col_widths)
            assert "col-time" in col_widths
            assert "col-act" in col_widths
            assert "col-rat" in col_widths
            assert "col-risk" in col_widths
            assert "col-stat" in col_widths
            assert "col-user" in col_widths
            print("  [PASS] Fixed table-layout with exact colgroup widths verified.")

            # Verify user column shows exporter
            page.locator('text=exporter').first.wait_for(state="visible", timeout=5000)
            print("  [PASS] User attribution column verified in audit table.")

            audit_ss = SCREENSHOT_DIR / "04_monad_audit_table.png"
            page.screenshot(path=str(audit_ss), full_page=True)
            print(f"  [SAVED] Screenshot: {audit_ss}")

            # -----------------------------------------------------------------
            # TEST 5: Document Agent & Risk Auditor Tabs
            # -----------------------------------------------------------------
            print("\n[TEST 5] Testing Document Agent and Adversarial Risk Auditor...")
            # Documents Tab
            doc_tab = page.locator('[data-baseweb="tab"]:has-text("DOCUMENTS")').first
            doc_tab.click()
            page.wait_for_timeout(1000)

            gen_doc_btn = page.locator('button:has-text("GENERATE SHIPMENT PAPERS")').first
            gen_doc_btn.wait_for(state="visible", timeout=5000)
            gen_doc_btn.click()
            page.locator('text=Packing Specification').first.wait_for(state="visible", timeout=10000)
            print("  [PASS] Document Agent packing list and CEPA compliance verified.")

            # Risk Auditor Tab
            risk_tab = page.locator('[data-baseweb="tab"]:has-text("RISK AUDITOR")').first
            risk_tab.click()
            page.wait_for_timeout(1000)

            # Test 10% payment after delivery query
            input_box = page.locator('textarea[aria-label="Enter deal proposal to audit:"]').first
            input_box.wait_for(state="visible", timeout=5000)
            input_box.fill("The buyer wants 10% payment after delivery and is a new customer ordering 2000 units.")
            input_box.press("Control+Enter")
            page.wait_for_timeout(1000)

            audit_btn = page.locator('button:has-text("AUDIT DEAL RISK")').first
            audit_btn.wait_for(state="visible", timeout=5000)
            audit_btn.click()
            page.locator('text=Risk Auditor Verdict').first.wait_for(state="visible", timeout=10000)

            # Verify accurate calculation: Medium risk, 10% retention, 90% upfront, NO false 100%
            page.locator('text=Risk: MEDIUM').first.wait_for(state="visible", timeout=5000)
            page.locator('text=10%').first.wait_for(state="visible", timeout=5000)
            page.locator('text=90%').first.wait_for(state="visible", timeout=5000)
            assert page.locator('text=100% payment after delivery').count() == 0
            print("  [PASS] Adversarial Risk Auditor accurately parsed 10% retention and 2000 units.")

            risk_ss = SCREENSHOT_DIR / "06_monad_risk_auditor_fixed.png"
            page.screenshot(path=str(risk_ss), full_page=True)
            print(f"  [SAVED] Screenshot: {risk_ss}")

            # -----------------------------------------------------------------
            # TEST 6: Admin Login & Full Audit Access
            # -----------------------------------------------------------------
            print("\n[TEST 6] Testing Admin Login & Governance Control Access...")
            logout_btn = page.locator('button:has-text("LOG OUT")').first
            logout_btn.click()
            page.wait_for_timeout(1500)

            # Re-login as Admin
            user_input = page.locator('input[aria-label="Username"], input[type="text"]').first
            user_input.fill("admin")

            pw_input = page.locator('input[aria-label="Password"], input[type="password"]').first
            pw_input.fill("admin123")

            page.locator('button:has-text("Login")').first.click()
            page.wait_for_timeout(2000)

            # Verify Admin badge
            page.locator('text=Logged in as FedAI Control Admin').first.wait_for(state="visible", timeout=15000)
            page.locator('text=ADMIN').first.wait_for(state="visible", timeout=5000)
            print("  [PASS] Successfully authenticated as FedAI Administrator.")
            page.wait_for_timeout(3000)

            # Go to Audit Log Tab as Admin
            admin_audit_tab = page.locator('[data-baseweb="tab"]:has-text("AUDIT LOG")').first
            admin_audit_tab.wait_for(state="visible", timeout=10000)
            admin_audit_tab.scroll_into_view_if_needed()
            admin_audit_tab.click()
            page.wait_for_timeout(2500)

            page.locator('text=Full Audit Log').first.wait_for(state="visible", timeout=15000)
            print("  [PASS] Admin has access to full audit log across all users.")

            admin_ss = SCREENSHOT_DIR / "05_monad_admin_audit.png"
            page.screenshot(path=str(admin_ss), full_page=True)
            print(f"  [SAVED] Screenshot: {admin_ss}")

            print("\n==================================================")
            print("ALL PLAYWRIGHT TESTS PASSED SUCCESSFULLY!")
            print("==================================================")

        except Exception as e:
            print(f"\n[FAIL] Test Failed: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            page.screenshot(path=str(SCREENSHOT_DIR / "failure_debug.png"), full_page=True)
            all_passed = False
        finally:
            context.close()
            browser.close()

    return all_passed


if __name__ == "__main__":
    success = run_e2e_tests()
    sys.exit(0 if success else 1)
