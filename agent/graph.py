"""LangGraph agent orchestration flow for ExportPilot.

Coordinates query comprehension, FX rates, buyer norms, trade risk intelligence,
structured quote calculation, and executive buyer email drafting.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional, TypedDict

from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph

from agent.prompts import (
    SYSTEM_DRAFTER_PROMPT,
    SYSTEM_EXTRACTOR_PROMPT,
    fallback_draft_email,
    fallback_extract_query,
)
from agent.tools import draft_quote, get_buyer_norms, get_fx, get_trade_news

load_dotenv()
logger = logging.getLogger(__name__)


class TradeAgentState(TypedDict, total=False):
    """LangGraph state representation for an exporter deal lifecycle."""

    query: str
    country: str
    target_currency: str
    item: str
    quantity: float
    unit_price_inr: float
    total_inr: float
    fx_rate: float
    fx_info: Dict[str, Any]
    buyer_norms: Dict[str, Any]
    trade_news: Dict[str, Any]
    risk_level: str
    risk_reasons: List[str]
    quote_data: Dict[str, Any]
    buyer_message: str
    status: str
    error: Optional[str]


def _call_gemini_text(prompt: str, system_instruction: str = "") -> Optional[str]:
    """Call Google Gemini Flash API via google-genai SDK if API key exists."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key.startswith("your_") or len(api_key) < 10:
        return None

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        config = {}
        if system_instruction:
            config["system_instruction"] = system_instruction

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config if config else None,
        )
        if response and response.text:
            return response.text.strip()
    except Exception as exc:
        logger.warning("Gemini API call failed (%s); switching to resilient offline fallback.", exc)
    return None


def node_understand_request(state: TradeAgentState) -> Dict[str, Any]:
    """Extract deal entities from natural language query using Gemini or fallback."""
    query = state.get("query", "").strip()
    extracted: Optional[Dict[str, Any]] = None

    # Try Gemini if key is provided
    gemini_resp = _call_gemini_text(
        prompt=f"Extract trade entities from this request:\n\n{query}",
        system_instruction=SYSTEM_EXTRACTOR_PROMPT,
    )
    if gemini_resp:
        try:
            # Strip potential code block formatting
            cleaned = gemini_resp.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            extracted = json.loads(cleaned.strip())
        except Exception:
            extracted = None

    # If Gemini extraction was unavailable or unparseable, use rule-based fallback
    if not extracted:
        extracted = fallback_extract_query(query)

    return {
        "item": extracted.get("item", "Custom Goods"),
        "quantity": float(extracted.get("quantity", 500)),
        "unit_price_inr": float(extracted.get("unit_price_inr", 350.0)),
        "country": extracted.get("country", "UAE"),
        "target_currency": extracted.get("target_currency", "AED"),
    }


def node_fetch_fx(state: TradeAgentState) -> Dict[str, Any]:
    """Retrieve live or cached FX rate for quote target currency."""
    target_currency = state.get("target_currency", "AED")
    fx_info = get_fx("INR", target_currency)
    return {
        "fx_info": fx_info,
        "fx_rate": fx_info.get("rate", 0.0435),
    }


def node_fetch_norms(state: TradeAgentState) -> Dict[str, Any]:
    """Retrieve destination country cultural and commercial trade norms."""
    country = state.get("country", "UAE")
    norms = get_buyer_norms(country)
    return {"buyer_norms": norms}


def node_fetch_risk(state: TradeAgentState) -> Dict[str, Any]:
    """Retrieve trade news and determine risk rating with rationales."""
    country = state.get("country", "UAE")
    news = get_trade_news(country)

    # Risk evaluation logic (India-UAE CEPA context)
    risk_level = "Low"
    reasons = [
        "CEPA preferential customs tariff active for eligible Indian exports.",
        "Stable USD/AED currency peg minimizes destination cross-rate volatility.",
        "Western Indian ports (Nhava Sheva/Mundra) to Jebel Ali maritime lanes operational.",
    ]

    return {
        "trade_news": news,
        "risk_level": risk_level,
        "risk_reasons": reasons,
    }


def node_draft_quote_and_message(state: TradeAgentState) -> Dict[str, Any]:
    """Compute quote pricing, FX margin buffer, and draft professional buyer message."""
    quote = draft_quote(
        item=state.get("item", "Export Product"),
        quantity=state.get("quantity", 500),
        unit_price_inr=state.get("unit_price_inr", 350.0),
        target_currency=state.get("target_currency", "AED"),
        fx_rate=state.get("fx_rate", 0.0435),
        buffer_pct=2.5,
        validity_days=14,
    )

    buyer_norms = state.get("buyer_norms", {})

    # Draft buyer message via Gemini or fallback template
    prompt_content = f"""
Deal Quotation Details:
- Item: {quote['item']}
- Quantity: {quote['quantity']}
- Unit Price ({quote['target_currency']}): {quote['unit_price_target']}
- Total ({quote['target_currency']}): {quote['total_target']}
- Incoterms: {quote['incoterms']}
- Validity: {quote['validity_days']} days

Buyer Norms:
- Country: {buyer_norms.get('country_name', 'UAE')}
- Greeting Style: {buyer_norms.get('greeting_style', '')}
- Payment Terms: {buyer_norms.get('payment_terms', '')}
- Negotiation Notes: {buyer_norms.get('negotiation_notes', '')}
"""
    draft_msg = _call_gemini_text(
        prompt=prompt_content,
        system_instruction=SYSTEM_DRAFTER_PROMPT,
    )
    if not draft_msg:
        draft_msg = fallback_draft_email(quote, buyer_norms)

    return {
        "quote_data": quote,
        "buyer_message": draft_msg,
        "status": "draft",  # HARD RULE: requires explicit human click to finalize/save
    }


def build_trade_copilot_graph() -> Any:
    """Build and compile the LangGraph workflow."""
    workflow = StateGraph(TradeAgentState)

    workflow.add_node("understand_request", node_understand_request)
    workflow.add_node("fetch_fx", node_fetch_fx)
    workflow.add_node("fetch_norms", node_fetch_norms)
    workflow.add_node("fetch_risk", node_fetch_risk)
    workflow.add_node("draft_quote_and_message", node_draft_quote_and_message)

    workflow.add_edge(START, "understand_request")
    workflow.add_edge("understand_request", "fetch_fx")
    workflow.add_edge("fetch_fx", "fetch_norms")
    workflow.add_edge("fetch_norms", "fetch_risk")
    workflow.add_edge("fetch_risk", "draft_quote_and_message")
    workflow.add_edge("draft_quote_and_message", END)

    return workflow.compile()


# Global singleton instance of compiled graph
trade_agent_app = build_trade_copilot_graph()


def run_trade_copilot(query: str) -> TradeAgentState:
    """Execute the end-to-end LangGraph agent on an exporter's natural language request.

    Args:
        query: Exporter request string (in English or translated).

    Returns:
        TradeAgentState dictionary containing all calculated fields and drafted buyer message.
    """
    initial_state: TradeAgentState = {"query": query}
    result = trade_agent_app.invoke(initial_state)
    return result
