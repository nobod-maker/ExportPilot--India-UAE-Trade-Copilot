"""Trade and quote tools for ExportPilot.

Provides foreign exchange rates, destination buyer norms, trade news,
quote calculation, and persistent SQLite deal recording.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

# Fallback exchange rates if external network request fails
DEFAULT_FALLBACK_RATES: Dict[str, float] = {
    "AED": 0.0435,  # 1 INR ≈ 0.0435 AED (~22.98 INR/AED)
    "USD": 0.0118,
    "EUR": 0.0109,
    "GBP": 0.0093,
    "SAR": 0.0443,
}

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
BUYER_NORMS_PATH = DATA_DIR / "buyer_norms.json"
CACHED_NEWS_PATH = DATA_DIR / "cached_trade_news.json"
DEFAULT_DB_PATH = DATA_DIR / "exportpilot.db"


def get_fx(base: str = "INR", quote: str = "AED") -> Dict[str, Any]:
    """Fetch latest exchange rate from open.er-api.com with offline fallback.

    Args:
        base: Base currency code (default: INR).
        quote: Target quote currency code (default: AED).

    Returns:
        Dict with keys: base, quote, rate, timestamp, is_live.
    """
    base = base.upper().strip()
    quote = quote.upper().strip()

    if base == quote:
        return {
            "base": base,
            "quote": quote,
            "rate": 1.0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "is_live": True,
            "source": "identity",
        }

    url = f"https://open.er-api.com/v6/latest/{base}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("result") == "success" and quote in data.get("rates", {}):
                rate = float(data["rates"][quote])
                return {
                    "base": base,
                    "quote": quote,
                    "rate": rate,
                    "timestamp": data.get("time_last_update_utc", datetime.now(timezone.utc).isoformat()),
                    "is_live": True,
                    "source": "open.er-api.com",
                }
    except Exception as exc:
        logger.warning("FX fetch failed (%s), falling back to internal cached rates.", exc)

    # Cached fallback
    fallback_rate = DEFAULT_FALLBACK_RATES.get(quote, 0.0435)
    return {
        "base": base,
        "quote": quote,
        "rate": fallback_rate,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "is_live": False,
        "source": "cached_fallback",
    }


def get_buyer_norms(country: str = "UAE") -> Dict[str, Any]:
    """Retrieve structured business and cultural trade norms for a buyer country.

    Args:
        country: Target country name or alias (e.g. 'UAE', 'Dubai', 'Saudi Arabia').

    Returns:
        Dict of buyer norms including working week, greetings, payment terms, holidays.
    """
    # Normalize country alias
    country_query = (country or "UAE").strip().lower()
    canonical_key = "UAE"
    if any(alias in country_query for alias in ["saudi", "ksa", "riyadh"]):
        canonical_key = "Saudi Arabia"
    elif any(alias in country_query for alias in ["uae", "dubai", "emirates", "abu dhabi", "sharjah"]):
        canonical_key = "UAE"

    if BUYER_NORMS_PATH.exists():
        try:
            with open(BUYER_NORMS_PATH, "r", encoding="utf-8") as f:
                norms_db = json.load(f)
                if canonical_key in norms_db:
                    result = dict(norms_db[canonical_key])
                    result["resolved_country"] = canonical_key
                    return result
        except Exception as exc:
            logger.error("Failed to read buyer norms file: %s", exc)

    # Built-in robust fallback for UAE
    return {
        "resolved_country": "UAE",
        "country_name": "United Arab Emirates",
        "currency": "AED",
        "working_week": "Monday to Friday (Saturday & Sunday weekend; Friday midday prayer break).",
        "greeting_style": "Formal, polite business English. Address buyer by title and surname.",
        "payment_terms": "30% Advance TT deposit, 70% against Bill of Lading, or LC at Sight.",
        "holidays": "Eid al-Fitr, Eid al-Adha, UAE National Day (Dec 2-3). Reduced hours during Ramadan.",
        "negotiation_notes": "Specify Incoterms (CIF Jebel Ali). Value relationship building and clear quality specs.",
    }


def draft_quote(
    item: str,
    quantity: float,
    unit_price_inr: float,
    target_currency: str = "AED",
    fx_rate: Optional[float] = None,
    buffer_pct: float = 2.5,
    validity_days: int = 14,
) -> Dict[str, Any]:
    """Calculate structured pricing, FX conversion, and margin buffer protection.

    Args:
        item: Description of goods (e.g., '100% Combed Cotton T-Shirts').
        quantity: Quantity units.
        unit_price_inr: Unit price in Indian Rupees (INR).
        target_currency: Target quote currency (default: AED).
        fx_rate: Conversion rate from INR to target currency (fetched if None).
        buffer_pct: Volatility protection buffer percentage (default: 2.5%).
        validity_days: Quote validity period in days (default: 14).

    Returns:
        Structured quotation dictionary with explicit formulas and pricing.
    """
    if fx_rate is None or fx_rate <= 0:
        fx_info = get_fx("INR", target_currency)
        fx_rate = fx_info["rate"]

    total_inr = round(quantity * unit_price_inr, 2)
    # Total quote currency at base conversion
    base_quote_cur = total_inr * fx_rate
    # FX buffer calculation (clearly labeled as estimated volatility buffer)
    estimated_fx_buffer = round(base_quote_cur * (buffer_pct / 100.0), 2)
    total_quote_cur = round(base_quote_cur, 2)
    unit_price_quote_cur = round(total_quote_cur / quantity, 2) if quantity > 0 else 0.0

    return {
        "item": item,
        "quantity": quantity,
        "unit_price_inr": unit_price_inr,
        "total_inr": total_inr,
        "target_currency": target_currency.upper(),
        "fx_rate": fx_rate,
        "unit_price_target": unit_price_quote_cur,
        "total_target": total_quote_cur,
        "buffer_pct": buffer_pct,
        "estimated_fx_buffer": estimated_fx_buffer,
        "buffer_formula": f"Estimated FX Volatility Buffer = Total {target_currency} ({total_quote_cur:,.2f}) × {buffer_pct}%",
        "validity_days": validity_days,
        "incoterms": "CIF Jebel Ali (Dubai)",
    }


def get_trade_news(country: str = "UAE") -> Dict[str, Any]:
    """Fetch destination trade news, CEPA updates, and shipping alerts with cached fallback.

    Args:
        country: Target country name.

    Returns:
        Dict containing news articles and source attribution.
    """
    # 1. Attempt live RSS feed parsing if feedparser is available
    articles = []
    try:
        import feedparser
        # DGFT / Indian trade PIB feed or Gulf business trade RSS
        feed_url = "https://pib.gov.in/RssMain.aspx?ModId=6"  # Ministry of Commerce & Industry
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:3]:
            articles.append({
                "title": entry.get("title", "Trade Notification"),
                "source": "PIB Commerce / DGFT",
                "summary": entry.get("summary", "")[:200] + "...",
                "risk_impact": "Operational Trade Update",
            })
    except Exception as exc:
        logger.debug("Live RSS parsing skipped or failed: %s", exc)

    # 2. If live returned items, combine or return; otherwise use local cached fallback
    if not articles and CACHED_NEWS_PATH.exists():
        try:
            with open(CACHED_NEWS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {
                    "country": country,
                    "source": "cached_trade_intelligence",
                    "articles": data.get("articles", []),
                    "updated_at": data.get("updated_at", "2026-10-16"),
                }
        except Exception as exc:
            logger.error("Failed to load cached trade news: %s", exc)

    return {
        "country": country,
        "source": "live_or_default",
        "articles": articles or [
            {
                "title": "India-UAE CEPA Bilateral Trade Protocols Active",
                "source": "DGFT Trade Desk",
                "summary": "Preferential tariff access active for Indian textile, food, and manufacturing exports.",
                "risk_impact": "Low tariff risk under verified Certificate of Origin.",
            }
        ],
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }


def init_db(db_path: Path | str = DEFAULT_DB_PATH) -> None:
    """Initialize the SQLite database schema if not present."""
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_file))
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS deals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                exporter_query TEXT NOT NULL,
                item TEXT NOT NULL,
                quantity REAL NOT NULL,
                unit_price_inr REAL NOT NULL,
                total_inr REAL NOT NULL,
                total_target REAL NOT NULL,
                currency TEXT NOT NULL,
                fx_rate REAL NOT NULL,
                risk_level TEXT NOT NULL,
                buyer_message TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('approved', 'rejected', 'draft'))
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def save_deal(deal_data: Dict[str, Any], db_path: Path | str = DEFAULT_DB_PATH) -> int:
    """Save an approved deal to SQLite.

    HARD RULE: Must ONLY be called upon explicit human approval click.

    Args:
        deal_data: Dictionary containing deal fields.
        db_path: Path to SQLite database file.

    Returns:
        The inserted deal ID.
    """
    init_db(db_path)
    created_at = datetime.now(timezone.utc).isoformat()
    status = deal_data.get("status", "approved")

    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO deals (
                created_at, exporter_query, item, quantity,
                unit_price_inr, total_inr, total_target,
                currency, fx_rate, risk_level, buyer_message, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                created_at,
                deal_data.get("exporter_query", "Direct Quote"),
                deal_data.get("item", "Unspecified Goods"),
                float(deal_data.get("quantity", 0)),
                float(deal_data.get("unit_price_inr", 0)),
                float(deal_data.get("total_inr", 0)),
                float(deal_data.get("total_target", 0)),
                deal_data.get("currency", "AED"),
                float(deal_data.get("fx_rate", 1.0)),
                deal_data.get("risk_level", "Low"),
                deal_data.get("buyer_message", ""),
                status,
            ),
        )
        conn.commit()
        return cursor.lastrowid or 0
    finally:
        conn.close()


def get_deals(db_path: Path | str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Retrieve all saved deals from SQLite database."""
    init_db(db_path)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM deals ORDER BY id DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def init_audit_db(db_path: Path | str = DEFAULT_DB_PATH) -> None:
    """Initialize FedAI Control Tower audit logging schema."""
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_file))
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS control_tower_audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                reason TEXT NOT NULL,
                risk_level TEXT NOT NULL CHECK(risk_level IN ('Low', 'Medium', 'High')),
                governance_status TEXT NOT NULL,
                deal_id INTEGER
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def audit_log_event(
    action: str,
    reason: str,
    risk_level: str = "Low",
    status: str = "Completed",
    deal_id: Optional[int] = None,
    db_path: Path | str = DEFAULT_DB_PATH,
) -> int:
    """Record a governance and agent decision event to the FedAI Control Tower log."""
    init_audit_db(db_path)
    now_ts = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO control_tower_audit_logs (
                timestamp, action, reason, risk_level, governance_status, deal_id
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (now_ts, action, reason, risk_level, status, deal_id),
        )
        conn.commit()
        return cursor.lastrowid or 0
    finally:
        conn.close()


def get_audit_logs(limit: int = 50, db_path: Path | str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Retrieve audit history from the FedAI Control Tower."""
    init_audit_db(db_path)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM control_tower_audit_logs ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def audit_risk_assessment(deal_input: str | Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate deal terms aggressively from a risk auditor perspective.

    Argues why an exporter should NOT accept bad trade terms (e.g. 100% post delivery).
    """
    text = deal_input if isinstance(deal_input, str) else str(deal_input)
    lower_text = text.lower()

    # High Risk Patterns
    is_post_delivery = any(p in lower_text for p in ["after delivery", "post delivery", "100% after", "payment on arrival", "open account"])
    is_new_customer = any(p in lower_text for p in ["new customer", "first time", "unverified buyer", "unknown buyer"])
    is_safe_advance = any(p in lower_text for p in ["letter of credit", "lc", "advance", "30%", "50%", "deposit", "tt in advance"])

    if is_post_delivery or (is_new_customer and not is_safe_advance):
        risk_level = "High"
        recommendation = "REJECT / COUNTER-OFFER REQUIRED"
        reasons = [
            "Severe Payment Default Risk: Buyer requests 100% payment after delivery without financial collateral or LC.",
            "Lack of Recourse: Once cargo clears Jebel Ali customs, repossession costs from UAE exceed 40% of cargo value.",
            "Cross-Border Working Capital Lockup: Unfunded manufacturing and transit time causes severe cashflow strain.",
            "Counter-Offer Directive: Insist on minimum 30% advance TT deposit prior to container dispatch, and balance against draft Bill of Lading, or Irrevocable LC at Sight issued by a reputable UAE bank (e.g., Emirates NBD, FAB).",
        ]
    elif is_safe_advance:
        risk_level = "Low"
        recommendation = "ACCEPTABLE WITH STANDARD CEPA SAFEGUARDS"
        reasons = [
            "Structured Financial Protection: Advance deposit or Letter of Credit protects the manufacturing cost floor.",
            "Bilateral Legal Enforcement: LC governed by UCP 600 rules provides bank-guaranteed payment upon compliant documentation.",
            "Pre-shipment verification and CEPA Certificate of Origin ensures zero-tariff clearance.",
        ]
    else:
        risk_level = "Medium"
        recommendation = "CONDITIONAL APPROVAL (CREDIT VERIFICATION REQUIRED)"
        reasons = [
            "Payment terms are partially ambiguous or lack standard Incoterms clarity.",
            "Recommend obtaining export credit insurance (ECGC India) and specifying CIF Jebel Ali terms.",
        ]

    # Log to Control Tower
    audit_log_event(
        action="Adversarial Risk Audit",
        reason=f"Risk Auditor evaluated terms: '{text[:80]}...' -> {recommendation}",
        risk_level=risk_level,
        status="Review Completed",
    )

    return {
        "risk_level": risk_level,
        "recommendation": recommendation,
        "reasons": reasons,
        "analyzed_query": text,
    }


def generate_packing_list_and_compliance(
    item: str,
    quantity: float,
    unit_price_inr: float,
    currency: str = "AED",
) -> Dict[str, Any]:
    """Generate export packing list and UAE import compliance checklist."""
    # Infer unit metrics
    qty = max(1.0, float(quantity))
    unit_net_kg = 0.4 if "shirt" in item.lower() else (1.0 if "kg" in item.lower() else 1.2)
    total_net_kg = round(qty * unit_net_kg, 2)
    total_gross_kg = round(total_net_kg * 1.08, 2)
    packages_count = max(1, int(qty / 50)) if "shirt" in item.lower() else max(1, int(qty / 25))

    # HS Code Inference
    hs_code = "6205.20.00"  # Cotton shirts
    if "spice" in item.lower() or "cardamom" in item.lower():
        hs_code = "0908.31.00"
    elif "pepper" in item.lower():
        hs_code = "0904.11.00"
    elif "leather" in item.lower():
        hs_code = "4202.21.00"
    elif "rice" in item.lower():
        hs_code = "1006.30.00"
    elif "part" in item.lower() or "auto" in item.lower():
        hs_code = "8708.29.00"

    packing_list = {
        "item": item,
        "hs_code": hs_code,
        "total_units": f"{qty:,.0f} Units",
        "total_packages": f"{packages_count} Export Cartons",
        "package_type": "Corrugated Heavy-Duty Export Cartons (Palletized)",
        "net_weight": f"{total_net_kg:,.1f} KG",
        "gross_weight": f"{total_gross_kg:,.1f} KG",
        "dimensions": "50 cm × 40 cm × 30 cm per carton",
        "marks_and_numbers": "EXP-PILOT / DXB / 001 - " + f"{packages_count:03d}",
    }

    compliance_checklist = [
        {"document": "Commercial Invoice", "authority": "Chamber of Commerce", "status": "Mandatory", "notes": "Must state HS Code, CIF value, and invoice currency."},
        {"document": "India–UAE CEPA Certificate of Origin", "authority": "DGFT India Online Portal", "status": "Mandatory for 0% Duty", "notes": "Enables preferential zero-tariff clearance at Dubai Customs under Bilateral CEPA."},
        {"document": "Ocean Bill of Lading (Clean on Board)", "authority": "Shipping Carrier / Freight Forwarder", "status": "Mandatory", "notes": "Port of loading: Nhava Sheva / Chennai; Port of discharge: Jebel Ali (Dubai)."},
        {"document": "Packing List", "authority": "Exporter", "status": "Mandatory", "notes": "Itemized gross weight, net weight, carton dimensions, and shipping marks."},
        {"document": "UAE MoIAT Conformity / Emirates Quality Mark", "authority": "Ministry of Industry & Advanced Tech (UAE)", "status": "Required for regulated goods", "notes": "Textiles & garments require standard lab test certificates."},
    ]

    # Log to Control Tower
    audit_log_event(
        action="Document Agent Packaging & Compliance",
        reason=f"Generated packing list ({packages_count} cartons) and CEPA checklist for {item}",
        risk_level="Low",
        status="Generated",
    )

    return {
        "packing_list": packing_list,
        "compliance_checklist": compliance_checklist,
    }


def estimate_corridor_freight(
    origin_port: str = "Nhava Sheva (Mumbai)",
    destination_port: str = "Jebel Ali (Dubai)",
    cargo_weight_kg: float = 500.0,
) -> Dict[str, Any]:
    """Estimate shipping cost, transit times, and routes for India-to-UAE corridor."""
    weight = max(10.0, float(cargo_weight_kg))

    # Sea Freight Benchmark
    sea_transit_days = "3 to 5 Days (Direct Maritime Corridor)"
    sea_cost_inr = round(32000.0 + (weight * 12.0), 2)
    sea_cost_aed = round(sea_cost_inr * 0.0386, 2)

    # Air Freight Benchmark
    air_transit_hours = "4 to 8 Hours (Direct Flight BOM/MAA -> DXB)"
    air_cost_inr = round(weight * 135.0, 2)
    air_cost_aed = round(air_cost_inr * 0.0386, 2)

    # Log to Control Tower
    audit_log_event(
        action="Corridor Freight Estimation",
        reason=f"Computed sea and air transit route benchmarks for {origin_port} -> {destination_port} ({weight} kg)",
        risk_level="Low",
        status="Estimated",
    )

    return {
        "origin_port": origin_port,
        "destination_port": destination_port,
        "cargo_weight_kg": weight,
        "sea_freight": {
            "mode": "Sea Cargo (FCL / LCL Container)",
            "transit_time": sea_transit_days,
            "cost_inr": f"₹{sea_cost_inr:,.2f}",
            "cost_aed": f"AED {sea_cost_aed:,.2f}",
            "recommended_for": "Bulk orders, garments, agro-commodities, heavy engineering",
        },
        "air_freight": {
            "mode": "Express Air Cargo (Direct Passenger / Freighter Flight)",
            "transit_time": air_transit_hours,
            "cost_inr": f"₹{air_cost_inr:,.2f}",
            "cost_aed": f"AED {air_cost_aed:,.2f}",
            "recommended_for": "Urgent samples, high-value jewelry, time-sensitive perishables",
        },
    }

