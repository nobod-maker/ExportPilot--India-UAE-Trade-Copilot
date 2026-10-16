"""Unit tests for ExportPilot tools.

Verifies FX conversion, buyer norms retrieval, quote drafting calculations,
and SQLite persistence.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from agent.tools import (
    get_fx,
    get_buyer_norms,
    draft_quote,
    get_trade_news,
    save_deal,
    get_deals,
    init_db,
)


def test_get_fx_inr_to_aed():
    """Verify FX rate returns positive rate and correct metadata."""
    res = get_fx("INR", "AED")
    assert res["base"] == "INR"
    assert res["quote"] == "AED"
    assert isinstance(res["rate"], float)
    assert res["rate"] > 0
    assert "timestamp" in res
    assert "is_live" in res


def test_get_fx_identity():
    """Verify identical base and quote returns rate of 1.0."""
    res = get_fx("AED", "AED")
    assert res["rate"] == 1.0
    assert res["is_live"] is True


def test_get_buyer_norms_uae():
    """Verify UAE trade customs contain all required fields."""
    norms = get_buyer_norms("UAE")
    assert norms["resolved_country"] == "UAE"
    assert "working_week" in norms
    assert "greeting_style" in norms
    assert "payment_terms" in norms
    assert "holidays" in norms
    assert "negotiation_notes" in norms
    # Verify Dubai alias resolves to UAE
    dubai_norms = get_buyer_norms("Dubai")
    assert dubai_norms["resolved_country"] == "UAE"


def test_draft_quote_math():
    """Verify quote calculations and estimated FX buffer formula."""
    quote = draft_quote(
        item="Combed Cotton Polo Shirts",
        quantity=500,
        unit_price_inr=400.0,
        target_currency="AED",
        fx_rate=0.0435,
        buffer_pct=2.5,
    )
    assert quote["item"] == "Combed Cotton Polo Shirts"
    assert quote["quantity"] == 500
    assert quote["unit_price_inr"] == 400.0
    assert quote["total_inr"] == 200000.0  # 500 * 400
    expected_total_target = round(200000.0 * 0.0435, 2)  # 8700.0
    assert quote["total_target"] == expected_total_target
    assert quote["target_currency"] == "AED"
    assert "Estimated FX Volatility Buffer" in quote["buffer_formula"]
    assert quote["estimated_fx_buffer"] == round(expected_total_target * 0.025, 2)


def test_sqlite_deal_persistence():
    """Verify deal saving and retrieval with explicit human approval flag."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_db = Path(tmp_dir) / "test_deals.db"
        init_db(test_db)

        deal_data = {
            "exporter_query": "Quote 500 cotton shirts to Dubai",
            "item": "Cotton Shirts",
            "quantity": 500,
            "unit_price_inr": 350.0,
            "total_inr": 175000.0,
            "total_target": 7612.5,
            "currency": "AED",
            "fx_rate": 0.0435,
            "risk_level": "Low",
            "buyer_message": "Formal quotation email draft",
            "status": "approved",
        }

        inserted_id = save_deal(deal_data, db_path=test_db)
        assert inserted_id > 0

        deals = get_deals(db_path=test_db)
        assert len(deals) == 1
        saved = deals[0]
        assert saved["id"] == inserted_id
        assert saved["item"] == "Cotton Shirts"
        assert saved["status"] == "approved"
        assert saved["currency"] == "AED"


def test_get_trade_news_fallback():
    """Verify trade news provides articles and handles offline fallback."""
    news = get_trade_news("UAE")
    assert news["country"] == "UAE"
    assert isinstance(news["articles"], list)
    assert len(news["articles"]) > 0
    article = news["articles"][0]
    assert "title" in article
    assert "risk_impact" in article
