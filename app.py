"""ExportPilot — India-UAE Trade Copilot.

A Streamlit AI Copilot for Indian exporters quoting and managing deals with UAE buyers.
Complies with zero-cost free-tier architecture, strict Human-in-the-Loop approval,
vernacular voice input (Tamil/Hindi/English), and live FX & trade intelligence.
"""

from __future__ import annotations

import io
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from agent.graph import run_trade_copilot
from agent.tools import get_buyer_norms, get_deals, get_fx, get_trade_news, save_deal
from agent.voice import SAMPLE_VERNACULAR_QUERIES, transcribe_and_translate_audio

load_dotenv()

# Streamlit Page Setup
st.set_page_config(
    page_title="ExportPilot | India–UAE Trade Copilot",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom High-End Executive Styling (Theme-Independent Anti-Slop CSS)
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

/* Force light root canvas regardless of browser theme */
html, body, .stApp, [data-testid="stAppViewContainer"], .main, .block-container {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background-color: #f8fafc !important;
    color: #0f172a !important;
}

code, kbd, samp, pre {
    font-family: 'JetBrains Mono', monospace !important;
}

/* Explicit text color for all headings and text elements in main area */
h1, h2, h3, h4, h5, h6,
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6,
.stMarkdown p, .stMarkdown span, .stMarkdown div, .stMarkdown li,
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] span {
    color: #0f172a !important;
}

.stCaption, [data-testid="stMarkdownContainer"] small {
    color: #475569 !important;
    font-size: 0.85rem !important;
}

/* Sidebar Explicit Theming */
[data-testid="stSidebar"] {
    background-color: #0f172a !important;
    border-right: 1px solid #1e293b !important;
}

[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span {
    color: #f8fafc !important;
}

[data-testid="stSidebar"] .metric-box {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
}

[data-testid="stSidebar"] .metric-box .metric-label {
    color: #94a3b8 !important;
}

[data-testid="stSidebar"] .metric-box .metric-val {
    color: #f8fafc !important;
}

[data-testid="stSidebar"] .metric-box .metric-sub {
    color: #38bdf8 !important;
}

/* Header Banner */
.brand-header {
    background: #0f172a !important;
    color: #f8fafc !important;
    padding: 1.5rem 2rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    border-left: 6px solid #0284c7;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08);
}

.brand-title {
    font-size: 1.85rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.025em;
    margin: 0 !important;
    color: #ffffff !important;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.brand-subtitle {
    font-size: 0.95rem !important;
    color: #94a3b8 !important;
    margin-top: 0.35rem !important;
    margin-bottom: 0 !important;
}

/* Metric / Status Cards in Main View */
.metric-box {
    background: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 10px;
    padding: 1.1rem 1.25rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
}

.metric-box * {
    color: #0f172a !important;
}

.metric-label {
    font-size: 0.78rem !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #475569 !important;
    font-weight: 700 !important;
}

.metric-val {
    font-size: 1.45rem !important;
    font-weight: 700 !important;
    color: #0f172a !important;
    margin-top: 0.25rem;
}

.metric-sub {
    font-size: 0.82rem !important;
    color: #0284c7 !important;
    margin-top: 0.15rem;
}

/* Status Badges */
.badge-live {
    background: #ecfdf5 !important;
    color: #065f46 !important;
    border: 1px solid #a7f3d0 !important;
    padding: 0.2rem 0.6rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    display: inline-block;
}

.badge-risk-low {
    background: #f0fdf4 !important;
    color: #166534 !important;
    border: 1px solid #bbf7d0 !important;
    padding: 0.25rem 0.6rem;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 600;
}

.badge-hitl {
    background: #fffbeb !important;
    color: #b45309 !important;
    border: 1px solid #fde68a !important;
    padding: 0.2rem 0.6rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
}

/* Quote Sheet Container & High-Contrast Table */
.quote-sheet {
    background: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 10px;
    padding: 1.25rem 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
}

.quote-sheet table {
    width: 100%;
    border-collapse: collapse;
}

.quote-sheet table tr {
    border-bottom: 1px solid #f1f5f9;
}

.quote-label {
    padding: 8px 0;
    color: #475569 !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
}

.quote-val {
    padding: 8px 0;
    color: #0f172a !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    text-align: right;
}

.quote-val-accent {
    padding: 8px 0;
    color: #0284c7 !important;
    font-weight: 800 !important;
    font-size: 1.05rem !important;
    text-align: right;
}

.quote-val-total {
    padding: 10px 0;
    color: #0f172a !important;
    font-weight: 800 !important;
    font-size: 1.2rem !important;
    text-align: right;
}

.section-label {
    font-size: 0.92rem !important;
    font-weight: 700 !important;
    color: #1e293b !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.75rem;
}

/* Input / Textarea Contrast Override */
textarea, input, [data-baseweb="textarea"] textarea {
    background-color: #ffffff !important;
    color: #0f172a !important;
    border: 1px solid #94a3b8 !important;
    border-radius: 8px !important;
    font-size: 0.95rem !important;
}

textarea:focus, input:focus {
    border-color: #0284c7 !important;
    box-shadow: 0 0 0 2px rgba(2, 132, 199, 0.2) !important;
}

/* Buttons */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
}

/* Hide default streamlit header clutter */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


@st.cache_data(ttl=600)
def cached_fx(base: str = "INR", quote: str = "AED") -> Dict[str, Any]:
    return get_fx(base, quote)


@st.cache_data(ttl=1800)
def cached_news(country: str = "UAE") -> Dict[str, Any]:
    return get_trade_news(country)


def init_session_state() -> None:
    """Initialize application session states."""
    if "current_deal" not in st.session_state:
        st.session_state.current_deal = None
    if "voice_meta" not in st.session_state:
        st.session_state.voice_meta = None
    if "approval_message" not in st.session_state:
        st.session_state.approval_message = None


init_session_state()

# Header Display
st.markdown(
    """
    <div class="brand-header">
        <h1 class="brand-title">🚢 ExportPilot <span style="font-size: 1.1rem; font-weight: 400; color: #38bdf8;">| India–UAE Trade Copilot</span></h1>
        <p class="brand-subtitle">
            Voice-driven deal quoting, CEPA tariff intelligence, live INR/AED rates, and cultural buyer negotiation drafting.
            <span class="badge-hitl" style="margin-left: 10px;">🛡️ Zero-finalize without Human Approval</span>
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Sidebar: Live Feeds & Settings
with st.sidebar:
    st.markdown("### 🌐 Market & Corridor Desk")
    live_fx = cached_fx("INR", "AED")
    st.markdown(
        f"""
        <div class="metric-box" style="margin-bottom: 1rem;">
            <div class="metric-label">INR / AED Exchange Rate</div>
            <div class="metric-val">1 INR = {live_fx['rate']:.4f} AED</div>
            <div class="metric-sub">1 AED ≈ {1.0 / live_fx['rate']:.2f} INR</div>
            <div style="margin-top: 0.5rem;">
                <span class="badge-live">{'● Live Open Feed' if live_fx.get('is_live') else '● Offline Fallback Rate'}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 🇦🇪 Destination: UAE Trade Norms")
    uae_norms = get_buyer_norms("UAE")
    with st.expander("View UAE Business Norms", expanded=False):
        st.markdown(f"**Working Week:**\n{uae_norms['working_week']}")
        st.markdown(f"**Greeting Protocol:**\n{uae_norms['greeting_style']}")
        st.markdown(f"**Payment Norms:**\n{uae_norms['payment_terms']}")
        st.markdown(f"**Key Holidays & Ramadan:**\n{uae_norms['holidays']}")
        st.markdown(f"**Incoterms & Ports:**\n{uae_norms['negotiation_notes']}")

    st.markdown("---")
    st.markdown("### ⚙️ Engine Status")
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    has_gemini = bool(gemini_key and not gemini_key.startswith("your_") and len(gemini_key) > 10)
    if has_gemini:
        st.success(f"Gemini Connected ({os.getenv('GEMINI_MODEL', 'gemini-3.8-flash')})")
    else:
        st.info("Operating in Resilient Offline Fallback mode (No API Key Required)")

    st.caption("Dubai Create AI Agents Championship | Cost: ₹0")


# Main Workspace Tabs
tab_quote, tab_history, tab_benchmarks = st.tabs(["💬 Deal Copilot Workbench", "📜 Deals History & Audit", "🧪 Vernacular Test Bench"])

with tab_quote:
    col_input, col_info = st.columns([1.2, 0.8], gap="large")

    with col_input:
        st.markdown("#### 1. Speak or Enter Your Deal Request")
        st.caption("Accepts Tamil (தமிழ்), Hindi (हिन्दी), or English voice notes & text.")

        # Voice Input Component with Safe Error Handling
        try:
            audio_val = st.audio_input("🎙️ Record Voice Request")
            if audio_val is not None:
                audio_bytes = audio_val.read()
                with st.spinner("Processing speech via Gemini..."):
                    v_res = transcribe_and_translate_audio(audio_bytes)
                    if v_res and v_res.get("english"):
                        st.session_state.voice_meta = v_res
                    else:
                        st.warning("Speech not detected clearly. Please type your deal below.")
        except Exception as mic_err:
            st.warning("Mic unavailable. Please type your request below or check microphone permissions.")

        st.markdown(
            """
            <p style="font-size: 0.78rem; color: #64748b; margin-top: -6px; margin-bottom: 12px;">
                🔒 <em>Tip: If your browser shows 'An error has occurred', click the lock icon left of <strong>localhost:8501</strong>, set <strong>Microphone → Allow</strong>, and reload. Or simply type your request in the box below.</em>
            </p>
            """,
            unsafe_allow_html=True,
        )

        # If voice was recorded or loaded, show transcription badge
        if st.session_state.voice_meta:
            vm = st.session_state.voice_meta
            st.info(
                f"**Detected Language:** `{vm['language'].upper()}` | **Original Voice:** *\"{vm['transcript']}\"*\n\n"
                f"**Translated Request:** *\"{vm['english']}\"*"
            )

        # Typed Fallback Box
        default_query_text = (
            st.session_state.voice_meta.get("english", "")
            if st.session_state.voice_meta
            else "Quote 500 cotton shirts to a Dubai buyer at 350 INR each, CIF Jebel Ali"
        )

        query_text = st.text_area(
            "Exporter Deal Request (English):",
            value=default_query_text,
            height=90,
            help="Type or edit the deal instructions here.",
        )

        # Quick preset buttons for instant evaluation
        st.markdown("<p style='font-size: 0.82rem; color: #475569; font-weight: 600; margin-bottom: 0.35rem;'>Or select quick sample scenario:</p>", unsafe_allow_html=True)
        q_cols = st.columns(3)
        with q_cols[0]:
            if st.button("👕 500 Cotton Shirts (Dubai)", use_container_width=True):
                query_text = "Quote 500 cotton shirts to a Dubai buyer at 350 INR each, CIF Jebel Ali"
                st.session_state.voice_meta = None
        with q_cols[1]:
            if st.button("🌶️ 1000 kg Cardamom (UAE)", use_container_width=True):
                query_text = "Quote 1000 kg Grade-A Cardamom to UAE buyer at 1800 INR per kg, 30% advance"
                st.session_state.voice_meta = None
        with q_cols[2]:
            if st.button("👜 300 Leather Bags (Abu Dhabi)", use_container_width=True):
                query_text = "Quote 300 genuine leather bags to Abu Dhabi distributor at 1200 INR each"
                st.session_state.voice_meta = None

        if st.button("⚡ Run ExportPilot Agent", type="primary", use_container_width=True):
            if query_text.strip():
                with st.spinner("ExportPilot Agent: Analyzing deal, calculating live FX, checking trade risks, and drafting quote..."):
                    result = run_trade_copilot(query_text)
                    st.session_state.current_deal = result
                    st.session_state.approval_message = None
            else:
                st.warning("Please enter or speak a deal request first.")

    with col_info:
        st.markdown("#### 2. Trade & Regulatory Risk Intelligence")
        news_data = cached_news("UAE")
        st.markdown(
            f"""
            <div class="metric-box" style="margin-bottom: 1rem;">
                <div class="metric-label">India–UAE CEPA Bilateral Corridor</div>
                <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 0.5rem;">
                    <span class="badge-risk-low">🛡️ Overall Risk: Low</span>
                    <span style="font-size: 0.8rem; color: #475569;">Source: {news_data.get('source', 'DGFT Desk')}</span>
                </div>
                <ul style="font-size: 0.84rem; margin-top: 0.75rem; padding-left: 1.2rem; color: #1e293b; line-height: 1.5;">
                    <li><strong>CEPA Duty Access:</strong> Zero or concessional tariffs on 90%+ Indian goods.</li>
                    <li><strong>Maritime Logistics:</strong> Western Indian ports (Nhava Sheva/Mundra) to Jebel Ali operating on regular 3–5 day direct sailing.</li>
                    <li><strong>Currency Peg:</strong> USD/AED pegged at 3.6725 ensuring predictable cross-rates.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander("Recent Trade & Logistics Bulletins", expanded=False):
            for art in news_data.get("articles", []):
                st.markdown(f"**{art['title']}**")
                st.caption(f"Source: {art['source']} | Impact: {art['risk_impact']}")
                st.write(art["summary"])
                st.markdown("---")

    # Agent Result Display & Human Approval Section
    if st.session_state.current_deal:
        deal = st.session_state.current_deal
        q_data = deal.get("quote_data", {})

        st.markdown("---")
        st.markdown("### 3. Agent Review & Human Approval Gate")
        st.caption("Examine the generated quotation breakdown and buyer draft. The deal is **NOT saved** until you click 'Approve & Save Deal to Archive'.")

        col_q, col_draft = st.columns([1, 1.2], gap="large")

        with col_q:
            st.markdown("<div class=\"section-label\">📊 Structured Quotation Breakdown</div>", unsafe_allow_html=True)
            st.markdown(
                f"""
                <div class="quote-sheet">
                    <table>
                        <tr>
                            <td class="quote-label">Product Description</td>
                            <td class="quote-val">{q_data.get('item', 'Goods')}</td>
                        </tr>
                        <tr>
                            <td class="quote-label">Quantity Units</td>
                            <td class="quote-val">{q_data.get('quantity', 0):,.0f}</td>
                        </tr>
                        <tr>
                            <td class="quote-label">Unit Price (INR)</td>
                            <td class="quote-val">₹{q_data.get('unit_price_inr', 0):,.2f}</td>
                        </tr>
                        <tr>
                            <td class="quote-label">Total Value (INR)</td>
                            <td class="quote-val">₹{q_data.get('total_inr', 0):,.2f}</td>
                        </tr>
                        <tr>
                            <td class="quote-label">Applied FX Rate</td>
                            <td class="quote-val">1 INR = {q_data.get('fx_rate', 0):.4f} AED</td>
                        </tr>
                        <tr style="background: #f8fafc; border-top: 1px solid #cbd5e1; border-bottom: 1px solid #cbd5e1;">
                            <td class="quote-label" style="font-weight: 700 !important; color: #0f172a !important;">Unit Price (AED)</td>
                            <td class="quote-val-accent">AED {q_data.get('unit_price_target', 0):,.2f}</td>
                        </tr>
                        <tr style="background: #f1f5f9;">
                            <td class="quote-label" style="font-weight: 800 !important; color: #0f172a !important; font-size: 1rem !important;">Total Quote (CIF Dubai)</td>
                            <td class="quote-val-total">AED {q_data.get('total_target', 0):,.2f}</td>
                        </tr>
                    </table>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Estimated FX Margin Buffer Panel (with explicit formula)
            est_buffer = q_data.get("estimated_fx_buffer", 0.0)
            st.markdown(
                f"""
                <div class="metric-box" style="margin-top: 1rem; border-left: 4px solid #10b981;">
                    <div class="metric-label">Estimated FX Volatility Buffer Protected</div>
                    <div class="metric-val" style="color: #065f46 !important;">AED {est_buffer:,.2f}</div>
                    <div style="font-size: 0.8rem; color: #334155; margin-top: 0.35rem;">
                        <strong>Transparent Formula:</strong> <code>{q_data.get('buffer_formula')}</code>
                    </div>
                    <div style="font-size: 0.78rem; color: #64748b; margin-top: 0.25rem;">
                        Protects MSME margin against 2.5% inter-bank settlement fluctuation during shipping and payment cycle.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_draft:
            st.markdown("<div class=\"section-label\">✉️ Drafted English Buyer Email</div>", unsafe_allow_html=True)
            draft_text = st.text_area(
                "Review or edit before human approval:",
                value=deal.get("buyer_message", ""),
                height=300,
            )

            # Human Approval Gate Button (HARD RULE)
            st.markdown("#### 🛡️ Explicit Human-in-the-Loop Gate")
            btn_col1, btn_col2 = st.columns([1.5, 1])

            with btn_col1:
                if st.button("✅ Approve & Save Deal to Archive", type="primary", use_container_width=True):
                    deal_record = {
                        "exporter_query": deal.get("query", "Voice/Text Quote"),
                        "item": q_data.get("item", "Custom Goods"),
                        "quantity": q_data.get("quantity", 0),
                        "unit_price_inr": q_data.get("unit_price_inr", 0),
                        "total_inr": q_data.get("total_inr", 0),
                        "total_target": q_data.get("total_target", 0),
                        "currency": q_data.get("target_currency", "AED"),
                        "fx_rate": q_data.get("fx_rate", 0.0435),
                        "risk_level": deal.get("risk_level", "Low"),
                        "buyer_message": draft_text,
                        "status": "approved",
                    }
                    new_id = save_deal(deal_record)
                    st.session_state.approval_message = f"Deal #{new_id} successfully approved and saved to database! Check 'Deals History' tab."
                    st.success(st.session_state.approval_message)

            with btn_col2:
                if st.button("❌ Discard Draft", use_container_width=True):
                    st.session_state.current_deal = None
                    st.session_state.approval_message = "Quotation draft discarded. Nothing was saved."
                    st.rerun()

            if st.session_state.approval_message:
                st.caption(f"Status: {st.session_state.approval_message}")


with tab_history:
    st.markdown("#### 📜 Archive of Approved Deals")
    st.caption("Every record in this database underwent mandatory explicit human approval before persistence.")

    deals = get_deals()
    if deals:
        df_deals = pd.DataFrame(deals)
        display_cols = [
            "id",
            "created_at",
            "item",
            "quantity",
            "unit_price_inr",
            "total_inr",
            "total_target",
            "currency",
            "fx_rate",
            "risk_level",
            "status",
        ]
        available_cols = [c for c in display_cols if c in df_deals.columns]
        st.dataframe(df_deals[available_cols], use_container_width=True)

        # CSV Export
        csv_buffer = io.StringIO()
        df_deals.to_csv(csv_buffer, index=False)
        st.download_button(
            label="📥 Export Deals CSV",
            data=csv_buffer.getvalue(),
            file_name=f"exportpilot_deals_{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )

        st.markdown("---")
        st.markdown("##### 🔍 Inspection of Selected Deal Record")
        deal_ids = [d["id"] for d in deals]
        selected_id = st.selectbox("Select Deal ID to inspect complete audit trail:", deal_ids)
        selected_rec = next((d for d in deals if d["id"] == selected_id), None)
        if selected_rec:
            st.markdown(f"**Original Exporter Query:** *\"{selected_rec['exporter_query']}\"*")
            st.markdown(f"**Approved Timestamp:** `{selected_rec['created_at']}` | **Status:** `{selected_rec['status'].upper()}`")
            with st.expander("View Saved Buyer Message Draft", expanded=True):
                st.text(selected_rec["buyer_message"])
    else:
        st.info("No approved deals saved yet. Use the 'Deal Copilot Workbench' tab to generate and approve your first deal.")


with tab_benchmarks:
    st.markdown("#### 🧪 Vernacular Multi-Language Test Bench (Tamil, Hindi, English)")
    st.caption("Demonstrating ExportPilot's multilingual audio and text capability across 30 curated trade queries.")

    bench_lang = st.radio("Select Test Language:", ["Tamil (தமிழ்)", "Hindi (हिन्दी)", "English"], horizontal=True)
    lang_key = "ta" if "Tamil" in bench_lang else ("hi" if "Hindi" in bench_lang else "en")

    samples = SAMPLE_VERNACULAR_QUERIES.get(lang_key, [])
    st.markdown(f"**Showing 10 Curated {bench_lang} Trade Scenarios:**")

    for idx, item in enumerate(samples, 1):
        with st.container():
            c1, c2, c3 = st.columns([1.2, 1.2, 0.6])
            with c1:
                st.markdown(f"**#{idx}. Spoken Text:**\n`{item['transcript']}`")
            with c2:
                st.markdown(f"**English Translation:**\n*{item['english']}*")
            with c3:
                if st.button(f"Load #{idx}", key=f"btn_bench_{lang_key}_{idx}"):
                    st.session_state.voice_meta = {
                        "language": lang_key,
                        "transcript": item["transcript"],
                        "english": item["english"],
                    }
                    st.session_state.current_deal = run_trade_copilot(item["english"])
                    st.success(f"Loaded scenario #{idx} into Deal Copilot Workbench!")
            st.markdown("---")
