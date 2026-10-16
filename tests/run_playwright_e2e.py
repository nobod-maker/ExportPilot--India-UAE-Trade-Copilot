"""Standalone Playwright CLI test runner for ExportPilot Stripe Design System."""

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
        context = browser.new_context(viewport={"width": 1400, "height": 900})
        page = context.new_page()

        try:
            # -----------------------------------------------------------------
            # TEST 1: Stripe Design Tokens & Pure White Canvas
            # -----------------------------------------------------------------
            print("\n[TEST 1] Verifying Stripe Financial Ledger Design Tokens...")
            page.goto(BASE_URL, wait_until="networkidle", timeout=30000)

            # Check Canvas Background and wait for hydration
            app_container = page.locator('[data-testid="stAppViewContainer"]')
            app_container.wait_for(state="visible", timeout=20000)

            page.wait_for_function("() => document.title.includes('ExportPilot')", timeout=15000)
            title = page.title()
            print("  [PASS] Page title verified:", title)
            bg_color = app_container.evaluate("el => window.getComputedStyle(el).backgroundColor")
            assert "255, 255, 255" in bg_color, f"Canvas background must be white (#ffffff), got {bg_color}"
            print("  [PASS] Canvas background is Pure White (#ffffff):", bg_color)

            # Check Primary Button (Indigo Ink #533afd, 4px radius, no box shadow)
            primary_btn = page.locator('button[kind="primary"]').first
            primary_btn.wait_for(state="visible", timeout=10000)
            btn_styles = primary_btn.evaluate(
                """el => {
                    const cs = window.getComputedStyle(el);
                    return {
                        backgroundColor: cs.backgroundColor,
                        borderRadius: cs.borderRadius,
                        boxShadow: cs.boxShadow
                    };
                }"""
            )
            print("  [INFO] Primary Button styles:", btn_styles)
            assert "83, 58, 253" in btn_styles["backgroundColor"], f"Expected #533afd (rgb(83, 58, 253)), got {btn_styles['backgroundColor']}"
            assert btn_styles["borderRadius"] == "4px", f"Expected 4px radius, got {btn_styles['borderRadius']}"
            assert btn_styles["boxShadow"] == "none", f"Expected no box-shadow, got {btn_styles['boxShadow']}"
            print("  [PASS] Verified: 4px radius, #533afd Indigo Ink fill, zero drop-shadow.")

            home_ss = SCREENSHOT_DIR / "01_stripe_home.png"
            page.screenshot(path=str(home_ss), full_page=True)
            print(f"  [SAVED] Screenshot: {home_ss}")

            # -----------------------------------------------------------------
            # TEST 2: Vernacular Sample Deal Loading & Quotation Calculation
            # -----------------------------------------------------------------
            print("\n[TEST 2] Verifying Deal Calculation & Quotation Breakdown...")
            load_sample_btn = page.locator('button:has-text("LOAD EN SAMPLE")').first
            load_sample_btn.wait_for(state="visible", timeout=5000)
            load_sample_btn.click()
            page.wait_for_timeout(1500)

            # Click SEND TO AGENT
            send_btn = page.locator('button:has-text("SEND TO AGENT")').first
            send_btn.wait_for(state="visible", timeout=5000)
            send_btn.click()
            print("  [INFO] Clicked 'SEND TO AGENT', waiting for copilot calculations...")

            # Wait for calculation results
            quote_card = page.locator('text=Commercial Quotation Breakdown').first
            quote_card.wait_for(state="visible", timeout=20000)
            print("  [PASS] Commercial Quotation breakdown rendered successfully.")

            # Check structured details
            page.locator('text=Drafted English Buyer Message').first.wait_for(state="visible", timeout=5000)
            page.locator('text=Estimated FX Margin Buffer Protected').first.wait_for(state="visible", timeout=5000)
            print("  [PASS] Buyer message draft and FX buffer card verified.")

            quote_ss = SCREENSHOT_DIR / "02_stripe_quotation.png"
            page.screenshot(path=str(quote_ss), full_page=True)
            print(f"  [SAVED] Screenshot: {quote_ss}")

            # -----------------------------------------------------------------
            # TEST 3: Human Approval Gate & FedAI Persistence
            # -----------------------------------------------------------------
            print("\n[TEST 3] Testing Human-in-the-Loop Approval Gate...")
            approve_btn = page.locator('button:has-text("APPROVE & SAVE DEAL")').first
            approve_btn.wait_for(state="visible", timeout=5000)
            approve_btn.click()

            approval_msg = page.locator('text=approved and stored in SQLite database').first
            approval_msg.wait_for(state="visible", timeout=10000)
            print("  [PASS] Explicit human approval gate successfully saved deal.")

            approved_ss = SCREENSHOT_DIR / "03_stripe_approved.png"
            page.screenshot(path=str(approved_ss), full_page=True)
            print(f"  [SAVED] Screenshot: {approved_ss}")

            # -----------------------------------------------------------------
            # TEST 4: Adversarial Risk Auditor Tab
            # -----------------------------------------------------------------
            print("\n[TEST 4] Testing Adversarial Risk Auditor Tab...")
            risk_tab = page.locator('[data-baseweb="tab"]:has-text("RISK AUDITOR")').first
            risk_tab.click()
            page.wait_for_timeout(1000)

            # Click Audit button
            audit_btn = page.locator('button:has-text("AUDIT DEAL RISK")').first
            audit_btn.wait_for(state="visible", timeout=5000)
            audit_btn.click()

            verdict = page.locator('text=Risk Auditor Verdict').first
            verdict.wait_for(state="visible", timeout=10000)
            print("  [PASS] Adversarial risk verdict rendered.")

            reasons = page.locator('text=Reasons NOT to Accept This Deal').first
            reasons.wait_for(state="visible", timeout=5000)
            print("  [PASS] Reasons NOT to accept deal displayed.")

            risk_ss = SCREENSHOT_DIR / "04_stripe_risk_auditor.png"
            page.screenshot(path=str(risk_ss), full_page=True)
            print(f"  [SAVED] Screenshot: {risk_ss}")

            # -----------------------------------------------------------------
            # TEST 5: Document Agent Tab
            # -----------------------------------------------------------------
            print("\n[TEST 5] Testing Document Agent Tab...")
            doc_tab = page.locator('[data-baseweb="tab"]:has-text("DOCUMENTS")').first
            doc_tab.click()
            page.wait_for_timeout(1000)

            gen_doc_btn = page.locator('button:has-text("GENERATE SHIPMENT PAPERS")').first
            gen_doc_btn.wait_for(state="visible", timeout=5000)
            gen_doc_btn.click()

            page.locator('text=Packing Specification').first.wait_for(state="visible", timeout=10000)
            page.locator('text=UAE CEPA Import Compliance Checklist').first.wait_for(state="visible", timeout=5000)
            print("  [PASS] Document Agent packing list and CEPA compliance verified.")

            doc_ss = SCREENSHOT_DIR / "05_stripe_documents.png"
            page.screenshot(path=str(doc_ss), full_page=True)
            print(f"  [SAVED] Screenshot: {doc_ss}")

            # -----------------------------------------------------------------
            # TEST 6: FedAI Control Tower Audit Log Tab
            # -----------------------------------------------------------------
            print("\n[TEST 6] Testing FedAI Control Tower Audit Log...")
            audit_tab = page.locator('[data-baseweb="tab"]:has-text("AUDIT LOG")').first
            audit_tab.click()
            page.wait_for_timeout(1000)

            page.locator('text=FedAI Control Tower & Audit Log').first.wait_for(state="visible", timeout=10000)
            page.locator('text=Action').first.wait_for(state="visible", timeout=5000)
            page.locator('text=Risk Tier').first.wait_for(state="visible", timeout=5000)
            print("  [PASS] Control Tower immutable audit table and risk columns verified.")

            audit_ss = SCREENSHOT_DIR / "06_stripe_control_tower.png"
            page.screenshot(path=str(audit_ss), full_page=True)
            print(f"  [SAVED] Screenshot: {audit_ss}")

            # -----------------------------------------------------------------
            # TEST 7: Cost & Route Corridor Estimator Tab
            # -----------------------------------------------------------------
            print("\n[TEST 7] Testing Cost & Route Corridor Estimator...")
            route_tab = page.locator('[data-baseweb="tab"]:has-text("COST & ROUTE")').first
            route_tab.click()
            page.wait_for_timeout(1000)

            page.locator('text=Corridor Freight & Transit Estimator').first.wait_for(state="visible", timeout=10000)
            calc_route_btn = page.locator('button:has-text("CALCULATE ROUTE BENCHMARKS")').first
            calc_route_btn.wait_for(state="visible", timeout=5000)
            calc_route_btn.click()

            page.locator('text=Transit Window').first.wait_for(state="visible", timeout=10000)
            print("  [PASS] Corridor Freight Estimator verified.")

            route_ss = SCREENSHOT_DIR / "07_stripe_cost_route.png"
            page.screenshot(path=str(route_ss), full_page=True)
            print(f"  [SAVED] Screenshot: {route_ss}")

            print("\n==================================================")
            print("ALL PLAYWRIGHT E2E TESTS PASSED SUCCESSFULLY!")
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
