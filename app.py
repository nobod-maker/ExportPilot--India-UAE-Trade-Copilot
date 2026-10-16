"""ExportPilot — India-UAE Trade Copilot.

Monad Editorial Design System on warm parchment (#f6f3f1) with faster-whisper
local speech processing, FedAI Control Tower governance, adversarial Risk Auditor,
Export Document Agent, Corridor Freight Estimator, and role-based authentication.
"""

from __future__ import annotations

import hashlib
import html
import io
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st
import yaml
from dotenv import load_dotenv
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth

from agent.graph import run_trade_copilot
from agent.tools import (
    audit_log_event,
    audit_risk_assessment,
    estimate_corridor_freight,
    generate_packing_list_and_compliance,
    get_audit_logs,
    get_buyer_norms,
    get_deals,
    get_fx,
    get_trade_news,
    save_deal,
    update_audit_log_status,
)
from agent.voice import (
    SAMPLE_VERNACULAR_QUERIES,
    transcribe_audio_pipeline,
)
from styles import load_monad_styles

load_dotenv()

# Streamlit Page Configuration
st.set_page_config(
    page_title="ExportPilot · India–UAE Trade Copilot",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Apply Monad Editorial Stylesheet
load_monad_styles()

# -----------------------------------------------------------------------------
# 1. SECURITY & AUTHENTICATION (streamlit-authenticator)
# -----------------------------------------------------------------------------
AUTH_CONFIG_PATH = Path("auth_config.yaml")

# Load or initialize auth configuration
if AUTH_CONFIG_PATH.exists():
    with open(AUTH_CONFIG_PATH, "r", encoding="utf-8") as f:
        auth_config = yaml.load(f, Loader=SafeLoader)
else:
    auth_config = {
        "credentials": {
            "usernames": {
                "admin": {
                    "email": "admin@exportpilot.trade",
                    "name": "FedAI Control Admin",
                    "password": "$2b$12$/8JkBiteUmi2AaFXr9/X8Oos8K16ZRYZVowEsxNA7mat2ziC.hkgq",
                    "roles": ["admin"],
                },
                "exporter": {
                    "email": "priya@exportpilot.trade",
                    "name": "Priya Exporter",
                    "password": "$2b$12$zTppiqRYE9LaqMsgjY5DM.TdU5vBvSb07OPZ0GawWndoNnMZGQhGa",
                    "roles": ["exporter"],
                },
            }
        },
        "cookie": {
            "expiry_days": 1.0,
            "key": "exportpilot_jwt_signature_secret_key_2026",
            "name": "exportpilot_cookie",
        },
    }

authenticator = stauth.Authenticate(
    auth_config["credentials"],
    auth_config["cookie"]["name"],
    auth_config["cookie"]["key"],
    auth_config["cookie"]["expiry_days"],
)

# -----------------------------------------------------------------------------
# 2. INACTIVITY SESSION TIMEOUT (30 MINUTES)
# -----------------------------------------------------------------------------
SESSION_TIMEOUT_SECONDS = 30 * 60  # 30 minutes
current_time = time.time()
if "last_activity_timestamp" in st.session_state:
    if current_time - st.session_state["last_activity_timestamp"] > SESSION_TIMEOUT_SECONDS:
        st.session_state.clear()
        st.warning("⚠️ Session expired after 30 minutes of inactivity. Please log in again.")
        st.stop()
st.session_state["last_activity_timestamp"] = current_time

# Render Login Dialog
authenticator.login()

# Gate application strictly behind authentication
auth_status = st.session_state.get("authentication_status")

if auth_status is False:
    st.error("❌ Username or password is incorrect. Please try again.")
    st.markdown(
        """
        <div class="monad-card" style="max-width: 500px; margin: 2rem auto; padding: 24px;">
            <div class="serif-card-title" style="font-size: 20px;">Demo Credentials</div>
            <p style="font-size: 13px; color: #797776; margin-bottom: 8px;">Use the following pre-configured accounts:</p>
            <div style="font-size: 13px; color: #242424; line-height: 1.8;">
                <strong>Admin Role:</strong> <code>admin</code> / <code>admin123</code><br>
                <strong>Exporter Role:</strong> <code>exporter</code> / <code>export123</code>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()
elif auth_status is None:
    st.markdown(
        """
        <div class="monad-card" style="max-width: 540px; margin: 3rem auto; padding: 32px; text-align: center;">
            <div class="serif-hero" style="font-size: 38px; margin-bottom: 8px;">ExportPilot</div>
            <div style="font-size: 14px; color: #797776; margin-bottom: 24px;">
                India–UAE Trade Copilot · FedAI Governance Gateway
            </div>
            <div style="background-color: #faf8f5; border: 1px solid #e5e1db; border-radius: 20px; padding: 18px; text-align: left; font-size: 13px;">
                <div style="font-weight: 600; margin-bottom: 6px; color: #242424;">Demo Credentials:</div>
                <div style="color: #4e4d4d; line-height: 1.8;">
                    • <strong>Exporter Role:</strong> <code>exporter</code> / <code>export123</code><br>
                    • <strong>Admin Role:</strong> <code>admin</code> / <code>admin123</code>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

# Retrieve Authenticated User Details
current_user = st.session_state.get("username", "exporter")
user_full_name = st.session_state.get("name", "Priya Exporter")
user_roles = st.session_state.get("roles", ["exporter"])
is_admin = "admin" in user_roles

# Security: File Upload Thresholds
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_AUDIO_EXTS = {"wav", "mp3", "m4a", "ogg", "opus", "webm"}
ALLOWED_DOC_EXTS = {"pdf", "png", "jpg", "jpeg"}


@st.cache_data(ttl=600)
def cached_fx(base: str = "INR", quote: str = "AED") -> Dict[str, Any]:
    return get_fx(base, quote)


@st.cache_data(ttl=1800)
def cached_news(country: str = "UAE") -> Dict[str, Any]:
    return get_trade_news(country)


def init_session_state() -> None:
    """Initialize persistent session states."""
    if "deal_query_input" not in st.session_state:
        st.session_state.deal_query_input = "Quote 500 cotton shirts to a Dubai buyer at 350 INR each, CIF Jebel Ali"
    if "editable_transcript" not in st.session_state:
        st.session_state.editable_transcript = ""
    if "detected_voice_meta" not in st.session_state:
        st.session_state.detected_voice_meta = None
    if "current_deal" not in st.session_state:
        st.session_state.current_deal = None
    if "approval_message" not in st.session_state:
        st.session_state.approval_message = None
    if "last_processed_audio_hash" not in st.session_state:
        st.session_state.last_processed_audio_hash = None
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = 0


init_session_state()

# -----------------------------------------------------------------------------
# 3. TOP ANNOUNCEMENT & SESSION BAR
# -----------------------------------------------------------------------------
role_badge_class = "role-tag-admin" if is_admin else "role-tag-exporter"
role_label = "ADMIN" if is_admin else "EXPORTER"

st.markdown(
    f"""
    <div class="announcement-bar">
        <span>ExportPilot · Trade Copilot</span>
        <span>
            Logged in as <strong>{html.escape(user_full_name)}</strong> (@{html.escape(current_user)})
            <span class="{role_badge_class}" style="margin-left: 8px;">{role_label}</span>
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)

# Top Bar Header with Logout in right column
col_head1, col_head2 = st.columns([4, 1])
with col_head1:
    st.markdown(
        """
        <div class="hero-wrapper" style="padding-top: 1rem; margin-bottom: 1.5rem;">
            <div class="serif-hero">Export smarter.<br>Speak in your language.</div>
            <div class="hero-subtitle">
                India–UAE export trade deals quoted in seconds. Speak in Tamil, Hindi, or English — automated CEPA tariff intelligence, live INR/AED hedging, and FedAI Control Tower governance.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_head2:
    st.markdown("<div style='text-align: right; margin-top: 1.5rem;'>", unsafe_allow_html=True)
    authenticator.logout("LOG OUT ⎋", "main")
    st.markdown("</div>", unsafe_allow_html=True)

# Market Ticker Bar (Parchment Card)
live_fx = cached_fx("INR", "AED")
news_data = cached_news("UAE")

col_tick1, col_tick2, col_tick3 = st.columns([1, 1, 1.2])
with col_tick1:
    st.markdown(
        f"""
        <div class="monad-card" style="padding: 20px 28px; margin-bottom: 2rem;">
            <div style="font-size: 11px; text-transform: uppercase; color: #797776; letter-spacing: 0.05em;">Live FX Rate (open.er-api.com)</div>
            <div style="font-size: 20px; font-weight: 500; color: #242424; margin-top: 4px;">1 INR = {live_fx['rate']:.4f} AED</div>
            <div style="font-size: 12px; color: #2b59d1; margin-top: 2px;">1 AED ≈ {1.0 / live_fx['rate']:.2f} INR</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_tick2:
    st.markdown(
        """
        <div class="monad-card" style="padding: 20px 28px; margin-bottom: 2rem;">
            <div style="font-size: 11px; text-transform: uppercase; color: #797776; letter-spacing: 0.05em;">Corridor Status</div>
            <div style="font-size: 20px; font-weight: 500; color: #242424; margin-top: 4px;">India–UAE CEPA Active</div>
            <div style="font-size: 12px; color: #1b633e; margin-top: 2px;"><span class="pill-badge pill-low">0% Tariff Preference</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_tick3:
    st.markdown(
        """
        <div class="monad-card" style="padding: 20px 28px; margin-bottom: 2rem;">
            <div style="font-size: 11px; text-transform: uppercase; color: #797776; letter-spacing: 0.05em;">Governance Framework</div>
            <div style="font-size: 20px; font-weight: 500; color: #242424; margin-top: 4px;">FedAI Control Tower</div>
            <div style="font-size: 12px; color: #797776; margin-top: 2px;">Human Approval Gate Enforced</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# -----------------------------------------------------------------------------
# 4. TABS NAVIGATION
# -----------------------------------------------------------------------------
tab_voice, tab_docs, tab_risk, tab_tower, tab_route = st.tabs([
    "VOICE ASSISTANT",
    "DOCUMENTS",
    "RISK AUDITOR",
    "AUDIT LOG",
    "COST & ROUTE",
])

# =============================================================================
# TAB 1: VOICE ASSISTANT (BUG FIX: DEFAULT TO ENGLISH, NO DUPLICATE LOGS)
# =============================================================================
with tab_voice:
    st.markdown(
        """
        <div class="monad-card">
            <div class="serif-card-title">Multilingual Voice Deal Desk</div>
            <p style="color: #797776; font-size: 14px; margin-bottom: 1.5rem;">
                Record speech or upload audio in English, Hindi, or Tamil. Local faster-whisper converts speech to text, detects the language, and translates to international trade English.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_v1, col_v2 = st.columns([1.1, 0.9], gap="large")

    with col_v1:
        st.markdown("<div class=\"serif-card-title\" style=\"font-size: 20px;\">Step 1: Audio Input & Settings</div>", unsafe_allow_html=True)

        c_opt1, c_opt2 = st.columns(2)
        with c_opt1:
            # BUG FIX: Default language to English to prevent "NN" auto-detect failures
            lang_selector = st.selectbox(
                "Language Selector",
                ["English", "Hindi", "Tamil", "Auto-detect"],
                index=0,
                help="Defaulted to English. Select native Hindi or Tamil for vernacular transcription.",
            )
        with c_opt2:
            model_selector = st.selectbox(
                "Whisper Model (Local)",
                ["base", "small"],
                index=0,
                help="Base is fast and lightweight on CPU (~140MB). Small offers higher accuracy.",
            )

        # Dual Audio Input: Microphone or File Upload
        input_mode = st.radio(
            "Input Method",
            ["🎙️ Microphone Recorder", "📁 Upload Voice Note (WAV, MP3, M4A, OGG, OPUS, WEBM)"],
            horizontal=True,
        )

        audio_bytes: Optional[bytes] = None
        format_hint: Optional[str] = None

        if "Microphone" in input_mode:
            try:
                mic_file = st.audio_input("Record Voice Deal Note")
                if mic_file is not None:
                    raw_mic = mic_file.read()
                    if len(raw_mic) > MAX_FILE_SIZE_BYTES:
                        st.error("⚠️ Recorded audio exceeds the 10 MB limit.")
                    else:
                        audio_bytes = raw_mic
                        format_hint = "webm"
            except Exception as e:
                st.error(f"Microphone access notice: {e}. Please ensure browser mic permission is allowed.")
        else:
            up_file = st.file_uploader(
                "Upload voice note (Max 10 MB)",
                type=["wav", "mp3", "m4a", "ogg", "opus", "webm"],
                help="Supports all major audio formats up to 10 MB.",
            )
            if up_file is not None:
                ext = up_file.name.split(".")[-1].lower()
                if ext not in ALLOWED_AUDIO_EXTS:
                    st.error(f"⚠️ Unsupported audio format: .{ext}. Allowed: {', '.join(ALLOWED_AUDIO_EXTS)}")
                elif up_file.size > MAX_FILE_SIZE_BYTES:
                    st.error(f"⚠️ File size ({up_file.size / 1024 / 1024:.1f} MB) exceeds maximum allowed 10 MB limit.")
                else:
                    audio_bytes = up_file.read()
                    format_hint = ext

        # Automatic Audio Processing guarded against duplicate execution
        if audio_bytes is not None:
            a_hash = hashlib.md5(audio_bytes).hexdigest()
            if st.session_state.last_processed_audio_hash != a_hash:
                with st.spinner("Processing audio with local faster-whisper (converting to 16 kHz mono)..."):
                    res = transcribe_audio_pipeline(
                        audio_bytes=audio_bytes,
                        language_choice=lang_selector,
                        model_size=model_selector,
                        format_hint=format_hint,
                    )
                    st.session_state.last_processed_audio_hash = a_hash

                    if res.get("success"):
                        st.session_state.detected_voice_meta = res
                        st.session_state.editable_transcript = res.get("transcript", "")
                        st.session_state.deal_query_input = res.get("english", res.get("transcript", ""))
                        audit_log_event(
                            action="Voice Transcription",
                            reason=f"Transcribed {res.get('duration_sec')}s audio in [{res.get('language_name')}] via faster-whisper {model_selector}",
                            risk_level="Low",
                            status="Transcribed",
                            user=current_user,
                        )
                        st.rerun()
                    else:
                        st.error(f"⚠️ {res.get('error', 'Could not process audio')}")

        # Step 2: Review & Edit Transcript
        st.markdown("<hr style='margin: 1.5rem 0;'>", unsafe_allow_html=True)
        st.markdown("<div class=\"serif-card-title\" style=\"font-size: 20px;\">Step 2: Review & Send to Agent</div>", unsafe_allow_html=True)

        if st.session_state.detected_voice_meta:
            vm = st.session_state.detected_voice_meta
            st.markdown(
                f"""
                <div style="margin-bottom: 12px;">
                    <span class="pill-badge pill-low">Detected: {html.escape(str(vm.get('language_name')))} ({html.escape(str(vm.get('language')))})</span>
                    <span class="pill-badge" style="margin-left: 6px;">Duration: {vm.get('duration_sec')}s</span>
                    <span class="pill-badge" style="margin-left: 6px;">Size: {vm.get('byte_size'):,} Bytes</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Editable Transcript Box
        st.session_state.editable_transcript = st.text_area(
            "Native Transcript (Editable):",
            value=st.session_state.editable_transcript,
            height=70,
            help="You can manually correct the transcript here before submitting.",
        )

        # Translated English Deal Query (Sent to Agent)
        st.session_state.deal_query_input = st.text_area(
            "English Deal Instructions (Sent to Agent):",
            value=st.session_state.deal_query_input,
            height=90,
            help="The agent uses this English deal specification to calculate pricing, verify customs, and draft buyer emails.",
        )

        col_act1, col_act2 = st.columns([1.5, 1])
        with col_act1:
            if st.button("SEND TO AGENT ▸", type="primary", use_container_width=True):
                clean_query = st.session_state.deal_query_input.strip()
                if clean_query:
                    with st.spinner("ExportPilot Agent: Calculating FX, verifying CEPA protocols, and drafting quote..."):
                        deal_result = run_trade_copilot(clean_query)
                        st.session_state.current_deal = deal_result
                        st.session_state.approval_message = None
                        audit_log_event(
                            action="Deal Quotation Drafted",
                            reason=f"Calculated quote for query: {clean_query[:60]}...",
                            risk_level="Medium",
                            status="Pending Human Approval",
                            user=current_user,
                        )
                        st.rerun()
                else:
                    st.warning("Please record voice or enter deal instructions first.")

        with col_act2:
            if st.button("RESET INPUT", use_container_width=True):
                st.session_state.deal_query_input = ""
                st.session_state.editable_transcript = ""
                st.session_state.detected_voice_meta = None
                st.session_state.current_deal = None
                st.rerun()

    with col_v2:
        # Voice Test & Self-Check Expander
        with st.expander("🔬 VOICE TEST & SELF-CHECK", expanded=True):
            st.markdown(
                """
                <p style="font-size: 13px; color: #4e4d4d; margin-bottom: 12px;">
                    Test sentences to verify pronunciation, language detection, and audio fidelity:
                </p>
                """,
                unsafe_allow_html=True,
            )

            test_cases = [
                ("EN", "I want to export 500 kilograms of turmeric to Dubai.", "English"),
                ("HI", "मुझे दुबई में हल्दी भेजनी है, कौन से दस्तावेज़ चाहिए?", "Hindi"),
                ("TA", "நான் துபாய்க்கு மஞ்சள் ஏற்றுமதி செய்ய வேண்டும்", "Tamil"),
            ]

            for code, sentence, lang_label in test_cases:
                st.markdown(f"**{lang_label} ({code}):**")
                st.code(sentence, language="text")
                if st.button(f"LOAD {code} SAMPLE ▸", key=f"btn_sample_{code}"):
                    st.session_state.deal_query_input = sentence
                    st.session_state.editable_transcript = sentence
                    st.session_state.detected_voice_meta = {
                        "language": code.lower(),
                        "language_name": lang_label,
                        "duration_sec": 3.2,
                        "byte_size": 102400,
                        "transcript": sentence,
                        "english": sentence if code == "EN" else "I want to export turmeric to Dubai.",
                    }
                    st.rerun()

        # UAE Buyer Protocol Overview Card
        uae_norms = get_buyer_norms("UAE")
        st.markdown(
            f"""
            <div class="monad-card" style="padding: 30px; margin-top: 1.5rem;">
                <div class="serif-card-title" style="font-size: 20px;">Destination: UAE Buyer Norms</div>
                <div style="font-size: 13px; color: #4e4d4d; line-height: 1.6; margin-top: 10px;">
                    <strong>Working Week:</strong> {html.escape(uae_norms['working_week'])}<br>
                    <strong>Payment Norms:</strong> {html.escape(uae_norms['payment_terms'])}<br>
                    <strong>Port Protocols:</strong> {html.escape(uae_norms['negotiation_notes'])}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Agent Result Display & Human Approval Section
    if st.session_state.current_deal:
        deal = st.session_state.current_deal
        q_data = deal.get("quote_data", {})

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<div class=\"serif-section\">Agent Quotation & Human Approval</div>", unsafe_allow_html=True)
        st.markdown(
            "<p style='color: #797776; font-size: 14px;'>Under the FedAI Control Tower governance mandate, this deal is in <code>DRAFT</code> status until you explicitly click Approve.</p>",
            unsafe_allow_html=True,
        )

        col_res1, col_res2 = st.columns([1, 1], gap="large")

        with col_res1:
            st.markdown(
                f"""
                <div class="monad-card">
                    <div class="serif-card-title">Commercial Quotation Breakdown</div>
                    <table style="margin-top: 1rem; width: 100%;">
                        <tr><td>Item Description</td><td style="text-align: right; font-weight: 500;">{html.escape(str(q_data.get('item')))}</td></tr>
                        <tr><td>Quantity</td><td style="text-align: right; font-weight: 500;">{q_data.get('quantity', 0):,.0f} Units</td></tr>
                        <tr><td>Unit Price (INR)</td><td style="text-align: right; font-weight: 500;">₹{q_data.get('unit_price_inr', 0):,.2f}</td></tr>
                        <tr><td>Total FOB Value (INR)</td><td style="text-align: right; font-weight: 500;">₹{q_data.get('total_inr', 0):,.2f}</td></tr>
                        <tr><td>FX Rate Applied</td><td style="text-align: right; font-weight: 500;">1 INR = {q_data.get('fx_rate', 0):.4f} AED</td></tr>
                        <tr style="border-top: 2px solid #cecac8;">
                            <td style="font-weight: 500; font-size: 15px;">Unit Price (AED)</td>
                            <td style="text-align: right; font-size: 16px; font-weight: 500; color: #2b59d1;">AED {q_data.get('unit_price_target', 0):,.2f}</td>
                        </tr>
                        <tr style="background: #e9e6e3;">
                            <td style="font-weight: 500; font-size: 16px;">Total Quote (CIF Jebel Ali)</td>
                            <td style="text-align: right; font-size: 18px; font-weight: 500; color: #242424;">AED {q_data.get('total_target', 0):,.2f}</td>
                        </tr>
                    </table>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Highlight Card (Estimated FX Margin Buffer Protected)
            est_buffer = q_data.get("estimated_fx_buffer", 0.0)
            st.markdown(
                f"""
                <div class="monad-card-highlight">
                    <div style="font-size: 11px; text-transform: uppercase; color: #2b59d1; font-weight: 500; letter-spacing: 0.05em;">Estimated FX Margin Buffer Protected</div>
                    <div style="font-size: 26px; font-weight: 500; color: #242424; margin-top: 4px;">AED {est_buffer:,.2f}</div>
                    <div style="font-size: 12px; color: #4e4d4d; margin-top: 6px;">
                        Formula: <code>{html.escape(str(q_data.get('buffer_formula', '')))}</code>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_res2:
            st.markdown(
                """
                <div class="monad-card">
                    <div class="serif-card-title">Drafted English Buyer Message</div>
                    <p style="color: #797776; font-size: 12px; margin-bottom: 12px;">Culturally calibrated for UAE commercial negotiation protocols.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            edited_buyer_msg = st.text_area(
                "Buyer Email Body:",
                value=deal.get("buyer_message", ""),
                height=260,
            )

            st.markdown("<div style='margin-top: 1.5rem;'>", unsafe_allow_html=True)
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button("APPROVE & SAVE DEAL ▸", type="primary", use_container_width=True):
                    record = {
                        "exporter_query": st.session_state.deal_query_input,
                        "item": q_data.get("item", "Goods"),
                        "quantity": q_data.get("quantity", 0),
                        "unit_price_inr": q_data.get("unit_price_inr", 0),
                        "total_inr": q_data.get("total_inr", 0),
                        "total_target": q_data.get("total_target", 0),
                        "currency": q_data.get("target_currency", "AED"),
                        "fx_rate": q_data.get("fx_rate", 0.0435),
                        "risk_level": deal.get("risk_level", "Low"),
                        "buyer_message": edited_buyer_msg,
                        "status": "approved",
                    }
                    new_id = save_deal(record)
                    audit_log_event(
                        action="Deal Approved & Archived",
                        reason=f"Human approved deal #{new_id} ({q_data.get('item')}, Total: AED {q_data.get('total_target')})",
                        risk_level="Low",
                        status="Human Approved",
                        deal_id=new_id,
                        user=current_user,
                    )
                    st.success(f"Deal #{new_id} approved and stored in SQLite database!")
            with col_b2:
                if st.button("DISCARD DRAFT", use_container_width=True):
                    st.session_state.current_deal = None
                    audit_log_event("Deal Discarded", "User discarded quotation draft", "Low", "Discarded", user=current_user)
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# =============================================================================
# TAB 2: DOCUMENTS (EXPORT PACKING LIST & CEPA CHECKLIST, 10MB LIMIT)
# =============================================================================
with tab_docs:
    st.markdown(
        """
        <div class="monad-card">
            <div class="serif-card-title">Export Document Agent</div>
            <p style="color: #797776; font-size: 14px;">
                Compile export packing lists, carton specifications, and mandatory UAE CEPA customs clearance checklists.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    doc_c1, doc_c2 = st.columns([1, 1], gap="large")
    with doc_c1:
        st.markdown("<div class=\"serif-card-title\" style=\"font-size: 20px;\">Consignment Specifications</div>", unsafe_allow_html=True)
        doc_item = st.text_input("Product Name / Description", value="100% Combed Cotton T-Shirts")
        doc_qty = st.number_input("Consignment Quantity (Units / Pieces)", min_value=1.0, value=500.0, step=50.0)
        doc_price = st.number_input("Unit Price in INR", min_value=1.0, value=350.0, step=10.0)

        # Optional Invoice Document Upload (10 MB Limit, PDF/Images)
        doc_upload = st.file_uploader(
            "Upload Existing Proforma Invoice (Optional, Max 10 MB)",
            type=["pdf", "png", "jpg", "jpeg"],
        )
        if doc_upload is not None:
            if doc_upload.size > MAX_FILE_SIZE_BYTES:
                st.error("⚠️ Document exceeds the maximum 10 MB limit.")
            else:
                st.success(f"Attached invoice document: {doc_upload.name} ({doc_upload.size / 1024:.1f} KB)")

        if st.button("GENERATE SHIPMENT PAPERS ▸", type="primary", use_container_width=True):
            clean_item = html.escape(doc_item.strip())
            st.session_state["doc_output"] = generate_packing_list_and_compliance(clean_item, doc_qty, doc_price)
            audit_log_event(
                action="Document Generation",
                reason=f"Generated export packing list and CEPA checklist for {clean_item}",
                risk_level="Low",
                status="Generated",
                user=current_user,
            )

    with doc_c2:
        if "doc_output" in st.session_state:
            d_out = st.session_state["doc_output"]
            pkl = d_out["packing_list"]

            st.markdown(
                f"""
                <div class="monad-card" style="padding: 30px;">
                    <div class="serif-card-title" style="font-size: 20px;">Packing Specification</div>
                    <table style="margin-top: 12px; width: 100%;">
                        <tr><td>Item</td><td>{html.escape(str(pkl['item']))} (HS Code: <code>{html.escape(str(pkl['hs_code']))}</code>)</td></tr>
                        <tr><td>Packages</td><td>{html.escape(str(pkl['total_packages']))}</td></tr>
                        <tr><td>Packaging Type</td><td>{html.escape(str(pkl['package_type']))}</td></tr>
                        <tr><td>Weight</td><td>Net: {html.escape(str(pkl['net_weight']))} | Gross: {html.escape(str(pkl['gross_weight']))}</td></tr>
                        <tr><td>Carton Dimensions</td><td>{html.escape(str(pkl['dimensions']))}</td></tr>
                        <tr><td>Shipping Marks</td><td><code>{html.escape(str(pkl['marks_and_numbers']))}</code></td></tr>
                    </table>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("<div class=\"serif-card-title\" style=\"font-size: 20px; margin-top: 1.5rem;\">UAE CEPA Import Compliance Checklist</div>", unsafe_allow_html=True)
            df_comp = pd.DataFrame(d_out["compliance_checklist"])
            st.dataframe(df_comp, use_container_width=True)
        else:
            st.info("Enter consignment details and click 'Generate Shipment Papers' to produce packing and compliance documents.")

# =============================================================================
# TAB 3: RISK AUDITOR ("REASONS NOT TO ACCEPT THIS DEAL")
# =============================================================================
with tab_risk:
    st.markdown(
        """
        <div class="monad-card">
            <div class="serif-card-title">Adversarial Risk Auditor</div>
            <p style="color: #797776; font-size: 14px;">
                Adversarial scrutiny of trade offers. Identifies payment default hazards, uncollateralized credit terms, and tells you why you should NOT accept risky deals.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    r_col1, r_col2 = st.columns([1, 1], gap="large")

    with r_col1:
        st.markdown("<div class=\"serif-card-title\" style=\"font-size: 20px;\">Audit Deal Terms</div>", unsafe_allow_html=True)
        deal_terms_input = st.text_area(
            "Enter deal proposal to audit:",
            value="The buyer wants 100% payment after delivery and is a new customer ordering 2000 units.",
            height=100,
        )

        st.markdown("<p style='font-size: 12px; color: #797776; text-transform: uppercase;'>Quick Test Proposals:</p>", unsafe_allow_html=True)
        t_col1, t_col2 = st.columns(2)
        with t_col1:
            if st.button("⚠️ TEST 100% AFTER DELIVERY", use_container_width=True):
                deal_terms_input = "The buyer wants 100% payment after delivery at Dubai port for a new customer."
        with t_col2:
            if st.button("✅ TEST 50% LC ADVANCE", use_container_width=True):
                deal_terms_input = "The buyer pays 50% advance via Letter of Credit and has ordered 3 times before."

        if st.button("AUDIT DEAL RISK ▸", type="primary", use_container_width=True):
            clean_terms = html.escape(deal_terms_input.strip())
            st.session_state["auditor_verdict"] = audit_risk_assessment(clean_terms)
            v = st.session_state["auditor_verdict"]
            audit_log_event(
                action="Deal Risk Audited",
                reason=f"Risk assessment returned tier: {v['risk_level']}",
                risk_level=v["risk_level"],
                status="Audited",
                user=current_user,
            )

    with r_col2:
        if "auditor_verdict" in st.session_state:
            v = st.session_state["auditor_verdict"]
            lvl = v["risk_level"]
            pill_class = "pill-high" if lvl == "High" else ("pill-med" if lvl == "Medium" else "pill-low")

            st.markdown(
                f"""
                <div class="monad-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div class="serif-card-title" style="margin: 0;">Risk Auditor Verdict</div>
                        <span class="pill-badge {pill_class}">Risk: {lvl.upper()}</span>
                    </div>
                    <div style="font-size: 18px; color: {'#991b1b' if lvl=='High' else '#1b633e'}; margin-top: 10px; font-weight: 500;">
                        {html.escape(v['recommendation'])}
                    </div>
                    <div style="margin-top: 1.5rem;">
                        <div style="font-size: 13px; text-transform: uppercase; color: #797776; margin-bottom: 8px;">Reasons NOT to Accept This Deal:</div>
                        <ul style="font-size: 14px; color: #242424; line-height: 1.6; padding-left: 1.2rem;">
                            {''.join(f'<li>{html.escape(r)}</li>' for r in v['reasons'])}
                        </ul>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.info("Click 'Audit Deal Risk' to view the adversarial analysis.")

# =============================================================================
# TAB 4: AUDIT LOG (FedAI CONTROL TOWER — FIXED COLGROUP ALIGNMENT + RBAC)
# =============================================================================
with tab_tower:
    st.markdown(
        """
        <div class="monad-card">
            <div class="serif-card-title">FedAI Control Tower & Audit Log</div>
            <p style="color: #797776; font-size: 14px;">
                UAE Federal AI Governance Layer. Every agent decision, rationale, risk tier, and user is logged immutably.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Role-Based Log Retrieval: Exporters see only their own logs; Admins see full log
    filter_user = None if is_admin else current_user

    if is_admin:
        admin_c1, admin_c2 = st.columns([2, 1])
        with admin_c1:
            st.markdown(
                f"<div style='font-size: 13px; color: #797776;'>Showing <strong>Full Audit Log</strong> (Administrator Access).</div>",
                unsafe_allow_html=True,
            )
        with admin_c2:
            view_filter = st.selectbox("Filter by User:", ["All Users", "admin", "exporter"])
            if view_filter != "All Users":
                filter_user = view_filter
    else:
        st.markdown(
            f"<div style='font-size: 13px; color: #797776; margin-bottom: 12px;'>Showing audit logs for <strong>@{html.escape(current_user)}</strong>.</div>",
            unsafe_allow_html=True,
        )

    logs = get_audit_logs(limit=50, user=filter_user)

    if logs:
        # Build ONE unified HTML table with table-layout: fixed and <colgroup>
        rows_html = []
        for entry in logs:
            r_lvl = entry.get("risk_level", "Low")
            pill_c = "pill-high" if r_lvl == "High" else ("pill-med" if r_lvl == "Medium" else "pill-low")
            t_str = html.escape(str(entry.get("timestamp", ""))[:19].replace("T", " "))
            act_str = html.escape(str(entry.get("action", "")))
            rea_str = html.escape(str(entry.get("reason", "")))
            stat_str = html.escape(str(entry.get("governance_status", "")))
            u_str = html.escape(str(entry.get("user", "system")))

            rows_html.append(
                f'<tr>'
                f'<td style="font-size: 11px; color: #797776;">{t_str}</td>'
                f'<td style="font-weight: 500;">{act_str}</td>'
                f'<td style="color: #4e4d4d;">{rea_str}</td>'
                f'<td><span class="pill-badge {pill_c}">{r_lvl}</span></td>'
                f'<td style="font-size: 11px;">{stat_str}</td>'
                f'<td><code>{u_str}</code></td>'
                f'</tr>'
            )

        full_table = (
            '<div class="audit-table-wrapper">'
            '<table class="audit-table">'
            '<colgroup>'
            '<col class="col-time">'
            '<col class="col-act">'
            '<col class="col-rat">'
            '<col class="col-risk">'
            '<col class="col-stat">'
            '<col class="col-user">'
            '</colgroup>'
            '<thead>'
            '<tr>'
            '<th>Timestamp (UTC)</th>'
            '<th>Action</th>'
            '<th>Governance Rationale</th>'
            '<th>Risk Tier</th>'
            '<th>Status</th>'
            '<th>User</th>'
            '</tr>'
            '</thead>'
            '<tbody>'
            + "".join(rows_html)
            + '</tbody>'
            '</table>'
            '</div>'
        )

        # Render complete fixed table in ONE block (unindented to prevent markdown code block trigger)
        st.markdown(full_table, unsafe_allow_html=True)

        # Admin High-Risk Action Approval / Rejection Controls
        if is_admin:
            pending_high_risks = [
                l for l in logs
                if l.get("risk_level") in ["High", "Medium"]
                and "Pending" in l.get("governance_status", "")
            ]
            if pending_high_risks:
                with st.expander("🛡️ ADMIN GOVERNANCE: APPROVE / REJECT PENDING ACTIONS", expanded=True):
                    st.markdown("<p style='font-size: 13px; color: #4e4d4d;'>As FedAI Administrator, you have authority to approve or reject high-risk deal actions.</p>", unsafe_allow_html=True)
                    target_log = st.selectbox(
                        "Select Pending Action:",
                        options=pending_high_risks,
                        format_func=lambda x: f"ID #{x['id']}: [{x['action']}] - {x['reason'][:50]}... ({x['risk_level']} Risk)",
                    )
                    c_adm1, c_adm2 = st.columns(2)
                    with c_adm1:
                        if st.button("✅ APPROVE HIGH-RISK ACTION", type="primary", use_container_width=True):
                            update_audit_log_status(target_log["id"], "Approved by Administrator", current_user)
                            st.success(f"Action #{target_log['id']} officially approved!")
                            st.rerun()
                    with c_adm2:
                        if st.button("❌ REJECT HIGH-RISK ACTION", use_container_width=True):
                            update_audit_log_status(target_log["id"], "Rejected by Administrator", current_user)
                            st.warning(f"Action #{target_log['id']} officially rejected.")
                            st.rerun()

        # CSV Download Button
        df_logs = pd.DataFrame(logs)
        csv_logs = io.StringIO()
        df_logs.to_csv(csv_logs, index=False)
        st.markdown("<div style='margin-top: 1.5rem;'>", unsafe_allow_html=True)
        st.download_button(
            "DOWNLOAD AUDIT LOG CSV ▸",
            data=csv_logs.getvalue(),
            file_name=f"control_tower_audit_{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No audit events recorded yet for this user. Agent actions will appear here in real time.")

# =============================================================================
# TAB 5: COST & ROUTE (CORRIDOR FREIGHT ESTIMATOR)
# =============================================================================
with tab_route:
    st.markdown(
        """
        <div class="monad-card">
            <div class="serif-card-title">Corridor Freight & Transit Estimator</div>
            <p style="color: #797776; font-size: 14px;">
                Direct benchmarks for maritime container corridors and air freight lanes between Indian hubs and Dubai/Jebel Ali.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_f1, col_f2 = st.columns([1, 1], gap="large")

    with col_f1:
        st.markdown("<div class=\"serif-card-title\" style=\"font-size: 20px;\">Route Parameters</div>", unsafe_allow_html=True)
        origin_hub = st.selectbox(
            "Origin Hub (India)",
            [
                "Nhava Sheva / JNPT (Mumbai)",
                "Chennai Port (Tamil Nadu)",
                "Mundra Port (Gujarat)",
                "Cochin Port (Kerala)",
                "IGI Cargo Terminal (Delhi - Air)",
            ],
        )
        dest_hub = "Jebel Ali Port / DXB (Dubai, UAE)"
        cargo_weight = st.number_input("Consignment Weight (KG)", min_value=10.0, value=500.0, step=50.0)

        if st.button("CALCULATE ROUTE BENCHMARKS ▸", type="primary", use_container_width=True):
            st.session_state["route_result"] = estimate_corridor_freight(origin_hub, dest_hub, cargo_weight)
            audit_log_event(
                action="Corridor Freight Estimator",
                reason=f"Calculated transit benchmarks: {origin_hub} -> {dest_hub} ({cargo_weight} kg)",
                risk_level="Low",
                status="Estimated",
                user=current_user,
            )

    with col_f2:
        if "route_result" in st.session_state:
            rr = st.session_state["route_result"]
            sea = rr["sea_freight"]
            air = rr["air_freight"]

            st.markdown(
                f"""
                <div class="monad-card" style="padding: 30px; margin-bottom: 1.5rem;">
                    <div style="font-size: 11px; text-transform: uppercase; color: #2b59d1; letter-spacing: 0.05em;">{html.escape(sea['mode'])}</div>
                    <div style="font-size: 24px; font-weight: 500; color: #242424; margin-top: 4px;">{html.escape(sea['cost_aed'])} <span style="font-size: 14px; color: #797776;">({html.escape(sea['cost_inr'])})</span></div>
                    <div style="font-size: 13px; color: #4e4d4d; margin-top: 8px;">
                        ⏱️ <strong>Transit Window:</strong> {html.escape(sea['transit_time'])}<br>
                        💡 <strong>Application:</strong> {html.escape(sea['recommended_for'])}
                    </div>
                </div>

                <div class="monad-card" style="padding: 30px;">
                    <div style="font-size: 11px; text-transform: uppercase; color: #92400e; letter-spacing: 0.05em;">{html.escape(air['mode'])}</div>
                    <div style="font-size: 24px; font-weight: 500; color: #242424; margin-top: 4px;">{html.escape(air['cost_aed'])} <span style="font-size: 14px; color: #797776;">({html.escape(air['cost_inr'])})</span></div>
                    <div style="font-size: 13px; color: #4e4d4d; margin-top: 8px;">
                        ⏱️ <strong>Transit Window:</strong> {html.escape(air['transit_time'])}<br>
                        💡 <strong>Application:</strong> {html.escape(air['recommended_for'])}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.info("Select an origin port and click 'Calculate Route Benchmarks' to see transit options.")
