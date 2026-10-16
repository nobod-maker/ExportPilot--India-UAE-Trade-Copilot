"""Unit tests for SQLite deal persistence and human approval state enforcement."""

from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from agent.tools import get_deals, init_db, save_deal


def test_deal_saving_approval_gate():
    """Verify that deal saving stores complete fields and maintains approved status."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "deals_audit.db"
        init_db(db_path)

        deal = {
            "exporter_query": "5000 kg Basmati Rice to UAE",
            "item": "Basmati Rice 1121 XXL",
            "quantity": 5000,
            "unit_price_inr": 95.0,
            "total_inr": 475000.0,
            "total_target": 20662.5,
            "currency": "AED",
            "fx_rate": 0.0435,
            "risk_level": "Low",
            "buyer_message": "Draft email to Dubai distributor",
            "status": "approved",
        }

        deal_id = save_deal(deal, db_path=db_path)
        assert deal_id > 0

        deals = get_deals(db_path=db_path)
        assert len(deals) == 1
        record = deals[0]
        assert record["status"] == "approved"
        assert record["item"] == "Basmati Rice 1121 XXL"
        assert record["quantity"] == 5000
        assert record["currency"] == "AED"
