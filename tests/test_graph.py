"""Unit tests for LangGraph agent workflow in ExportPilot.

Verifies end-to-end state transitions, FX binding, buyer norms extraction,
and human-approval draft status guarantee.
"""

from __future__ import annotations

import pytest
from agent.graph import run_trade_copilot


def test_langgraph_flow_end_to_end():
    """Verify that LangGraph executes all nodes and outputs structured quote and draft."""
    query = "Quote 500 cotton shirts to a Dubai buyer at 350 INR each"
    state = run_trade_copilot(query)

    # 1. Verification of entity extraction
    assert "cotton" in state["item"].lower() or "garments" in state["item"].lower()
    assert state["quantity"] == 500
    assert state["unit_price_inr"] == 350.0
    assert state["country"] == "UAE"
    assert state["target_currency"] == "AED"

    # 2. Verification of FX rates
    assert state["fx_rate"] > 0
    assert "fx_info" in state

    # 3. Verification of buyer norms
    assert state["buyer_norms"]["resolved_country"] == "UAE"
    assert "Monday to Friday" in state["buyer_norms"]["working_week"]

    # 4. Verification of trade risk
    assert state["risk_level"] in ["Low", "Medium", "High"]
    assert len(state["risk_reasons"]) > 0

    # 5. Verification of quote data & formula
    quote = state["quote_data"]
    assert quote["total_inr"] == 175000.0  # 500 * 350
    assert quote["total_target"] > 0
    assert "Estimated FX Volatility Buffer" in quote["buffer_formula"]

    # 6. Verification of drafted buyer message
    buyer_msg = state["buyer_message"]
    assert "COMMERCIAL QUOTATION" in buyer_msg or "Dear" in buyer_msg
    assert "AED" in buyer_msg or "CIF Jebel Ali" in buyer_msg

    # 7. HARD RULE CHECK: status must be draft (never finalized without user approval)
    assert state["status"] == "draft"
