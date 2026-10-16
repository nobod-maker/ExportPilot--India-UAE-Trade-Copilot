"""Prompt templates and fallback extractors for ExportPilot.

Handles trade query entity extraction and culturally aligned business email drafting.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict

SYSTEM_EXTRACTOR_PROMPT = """You are ExportPilot, an expert trade assistant for Indian exporters dealing with international buyers (focus: UAE / GCC).
Your task is to parse an exporter's natural language request (in English, or translated from Tamil/Hindi) into a strict JSON object.

Extract:
- item: Description of the product (e.g., "100% Combed Cotton T-Shirts")
- quantity: Numerical quantity (e.g., 500)
- unit_price_inr: Unit price in INR if mentioned (e.g., 350.0). If missing, infer a realistic reasonable benchmark (e.g., 300.0)
- country: Destination country (default: "UAE")
- target_currency: Quote currency (default: "AED")
- incoterms: e.g. "CIF Jebel Ali (Dubai)" or "FOB Nhava Sheva"
- payment_terms: Preferred payment terms (e.g., "30% advance, 70% against B/L")

Respond ONLY with valid JSON. Do not include markdown codeblocks or commentary.
"""

SYSTEM_DRAFTER_PROMPT = """You are an international trade negotiator drafting a formal business quotation email for an Indian exporter to a UAE buyer.

Adhere strictly to UAE business norms:
1. Warm, respectful, and professional business English greeting.
2. Clear and transparent quotation breakdown (Item, Quantity, Unit Price in AED, Total Value CIF Jebel Ali).
3. Explicit quotation validity (e.g., 14 days) and standard commercial terms (e.g. 30% advance TT, 70% against Bill of Lading, or LC at sight).
4. Reference to India-UAE CEPA preferential tariff documentation (Certificate of Origin provided).
5. Courteous, relationship-oriented closing inviting discussion or sample review.

Respond with the complete, ready-to-review email body.
"""


def fallback_extract_query(text: str) -> Dict[str, Any]:
    """Heuristic rule-based extractor when Gemini API is unavailable.

    Guarantees the demo never dies on network or quota issues.
    """
    clean_text = text.lower().strip()

    # 1. Extract quantity (look for numbers before or after common units/goods)
    quantity = 500.0
    qty_match = re.search(r"(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:pcs|pieces|units|shirts|meters|kg|tons|boxes|pairs)?", clean_text)
    if qty_match:
        try:
            val_str = qty_match.group(1).replace(",", "")
            val = float(val_str)
            if val > 0:
                quantity = val
        except ValueError:
            pass

    # 2. Extract unit price in INR
    unit_price = 350.0
    price_match = re.search(r"(?:rs\.?|inr|@|price|at)\s*(\d+(?:\.\d+)?)", clean_text)
    if price_match:
        try:
            unit_price = float(price_match.group(1))
        except ValueError:
            pass

    # 3. Detect Item
    item = "Combed Cotton Garments"
    if "shirt" in clean_text:
        item = "Premium Cotton Shirts"
    elif "spice" in clean_text or "cardamom" in clean_text or "pepper" in clean_text:
        item = "Grade-A Export Spices"
    elif "leather" in clean_text or "shoe" in clean_text:
        item = "Finished Leather Goods"
    elif "rice" in clean_text or "basmati" in clean_text:
        item = "1121 XXL Steam Basmati Rice"
    elif "part" in clean_text or "auto" in clean_text:
        item = "Precision Auto Components"

    # 4. Detect Destination
    country = "UAE"
    target_currency = "AED"
    if "saudi" in clean_text or "riyadh" in clean_text:
        country = "Saudi Arabia"
        target_currency = "SAR"

    return {
        "item": item,
        "quantity": quantity,
        "unit_price_inr": unit_price,
        "country": country,
        "target_currency": target_currency,
        "incoterms": "CIF Jebel Ali (Dubai)",
        "payment_terms": "30% Advance TT deposit, balance 70% against Bill of Lading",
    }


def fallback_draft_email(deal: Dict[str, Any], norms: Dict[str, Any]) -> str:
    """Generate professional, culturally calibrated buyer email without calling external LLM."""
    item = deal.get("item", "Quality Goods")
    qty = deal.get("quantity", 500)
    total_aed = deal.get("total_target", 0.0)
    unit_aed = deal.get("unit_price_target", 0.0)
    currency = deal.get("target_currency", "AED")
    incoterms = deal.get("incoterms", "CIF Jebel Ali (Dubai)")
    payment_terms = norms.get("payment_terms", "30% Advance TT, 70% against shipping documents (B/L)")
    validity = deal.get("validity_days", 14)

    return f"""Dear Procurement Director,

Greetings and warm wishes. We hope this message finds you in good health and high spirits.

Further to our discussions regarding your sourcing requirements from India, we are pleased to submit our formal commercial quotation for your review:

--------------------------------------------------
COMMERCIAL QUOTATION
--------------------------------------------------
Product Description : {item}
Quantity            : {qty:,.0f} Units
Unit Price          : {currency} {unit_aed:,.2f} ({incoterms})
Total Value         : {currency} {total_aed:,.2f}
Incoterms           : {incoterms}
Payment Terms       : {payment_terms}
Quote Validity      : {validity} Calendar Days
CEPA Preferential   : Comprehensive Economic Partnership Agreement (CEPA)
                      Certificate of Origin provided for zero/concessional customs duty.
--------------------------------------------------

Our production facility maintains strict ISO and international export quality standards. We can arrange express lab dispatch of production samples upon your request.

We look forward to establishing an enduring trade partnership with your esteemed organization.

Warm regards,

Export Trade Desk | ExportPilot India
Email: exports@pilottrade.in | Tel: +91-44-2850-XXXX
"""
