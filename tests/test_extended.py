"""Unit tests for FedAI Control Tower, Risk Auditor, Document Agent, and Freight Estimator."""

from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from agent.tools import (
    audit_log_event,
    audit_risk_assessment,
    estimate_corridor_freight,
    generate_packing_list_and_compliance,
    get_audit_logs,
)


def test_control_tower_audit_logging():
    """Verify Control Tower records events with timestamp, action, and risk classification."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_db = Path(tmp_dir) / "audit_test.db"
        event_id = audit_log_event(
            action="Test Action",
            reason="Verifying Control Tower Logging",
            risk_level="High",
            status="Pending Approval",
            deal_id=42,
            db_path=test_db,
        )
        assert event_id > 0
        logs = get_audit_logs(limit=10, db_path=test_db)
        assert len(logs) == 1
        entry = logs[0]
        assert entry["action"] == "Test Action"
        assert entry["risk_level"] == "High"
        assert entry["deal_id"] == 42


def test_risk_auditor_bad_deal():
    """Verify that 100% post-delivery terms for new buyers are aggressively flagged High Risk."""
    bad_deal = "The buyer wants 100% payment after delivery and is a new customer."
    res = audit_risk_assessment(bad_deal)
    assert res["risk_level"] == "High"
    assert "REJECT" in res["recommendation"]
    assert any("Default" in r or "advance" in r.lower() for r in res["reasons"])


def test_risk_auditor_safe_deal():
    """Verify that structured Letter of Credit and advance deposit are classified Low Risk."""
    safe_deal = "The buyer pays 50% advance via letter of credit and has ordered 3 times before."
    res = audit_risk_assessment(safe_deal)
    assert res["risk_level"] == "Low"
    assert "ACCEPTABLE" in res["recommendation"]


def test_document_agent_packing_and_cepa():
    """Verify packing list carton calculations and CEPA certificate checklist."""
    doc_res = generate_packing_list_and_compliance(
        item="100% Combed Cotton T-Shirts",
        quantity=500,
        unit_price_inr=350.0,
    )
    pkl = doc_res["packing_list"]
    assert "Cotton" in pkl["item"]
    assert pkl["hs_code"] == "6205.20.00"
    assert "Cartons" in pkl["total_packages"]
    assert "KG" in pkl["gross_weight"]

    checklist = doc_res["compliance_checklist"]
    assert len(checklist) >= 4
    docs = [d["document"] for d in checklist]
    assert any("CEPA" in d for d in docs)
    assert any("Bill of Lading" in d for d in docs)


def test_freight_corridor_estimator():
    """Verify sea and air freight routes and transit estimates."""
    f_res = estimate_corridor_freight(
        origin_port="Nhava Sheva (Mumbai)",
        destination_port="Jebel Ali (Dubai)",
        cargo_weight_kg=500.0,
    )
    assert "sea_freight" in f_res
    assert "air_freight" in f_res
    assert "3 to 5 Days" in f_res["sea_freight"]["transit_time"]
    assert "Hours" in f_res["air_freight"]["transit_time"]
