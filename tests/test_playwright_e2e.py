"""Playwright pytest suite for ExportPilot Stripe Design System and workflows."""

from __future__ import annotations

import os
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright

BASE_URL = os.getenv("EXPORTPILOT_URL", "http://localhost:8501")
SCREENSHOT_DIR = Path("tests/screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="module")
def browser_page():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1400, "height": 900})
        page = context.new_page()
        page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
        yield page
        context.close()
        browser.close()


def test_stripe_canvas_and_tokens(browser_page):
    """Verify Pure White canvas and Stripe tokens."""
    app_container = browser_page.locator('[data-testid="stAppViewContainer"]')
    app_container.wait_for(state="visible", timeout=15000)
    bg_color = app_container.evaluate("el => window.getComputedStyle(el).backgroundColor")
    assert "255, 255, 255" in bg_color

    primary_btn = browser_page.locator('button[kind="primary"]').first
    primary_btn.wait_for(state="visible", timeout=10000)
    styles = primary_btn.evaluate(
        """el => {
            const cs = window.getComputedStyle(el);
            return {
                bg: cs.backgroundColor,
                radius: cs.borderRadius,
                shadow: cs.boxShadow
            };
        }"""
    )
    assert "83, 58, 253" in styles["bg"]
    assert styles["radius"] == "4px"
    assert styles["shadow"] == "none"
