"""Monad Editorial Design System for ExportPilot.

Warm parchment palette (#f6f3f1), Newsreader serif headings (weight 400 only, never bold),
JetBrains Mono body & UI, 40px bordered cards, 100px pill buttons, and zero drop shadows.
"""

from __future__ import annotations

import streamlit as st

MONAD_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=Newsreader:ital,opsz,wght@0,6..72,400;1,6..72,400&display=swap');

/* ==========================================================================
   GLOBAL CANVAS & RESET (NEVER PURE WHITE)
   ========================================================================== */
html, body, .stApp, [data-testid="stAppViewContainer"], .main, .block-container {
    background-color: #f6f3f1 !important;
    color: #242424 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 15px !important;
    line-height: 1.6 !important;
}

/* Max content width ~1200px centered */
.block-container {
    max-width: 1200px !important;
    padding-top: 1.5rem !important;
    padding-bottom: 4rem !important;
    margin: 0 auto !important;
}

/* ==========================================================================
   TYPOGRAPHY
   - Headings: Newsreader Serif, weight 400 ONLY (never bold), letter-spacing -0.02em
   - UI / Body: JetBrains Mono, uppercase on buttons/tabs/badges
   ========================================================================== */
h1, h2, h3, h4, h5, h6,
.serif-hero, .serif-section, .serif-card-title,
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
    font-family: 'Newsreader', Georgia, serif !important;
    font-weight: 400 !important;
    letter-spacing: -0.02em !important;
    line-height: 1.15 !important;
    color: #242424 !important;
    text-transform: none !important;
}

.serif-hero {
    font-size: 64px !important;
    margin-bottom: 1rem !important;
}

.serif-section {
    font-size: 40px !important;
    margin-top: 2.5rem !important;
    margin-bottom: 1.25rem !important;
}

.serif-card-title {
    font-size: 24px !important;
    margin-bottom: 0.75rem !important;
}

p, span, div, label, li, .stMarkdown p, .stMarkdown span {
    font-family: 'JetBrains Mono', monospace !important;
    color: #4e4d4d !important;
}

/* ==========================================================================
   TOP ANNOUNCEMENT BAR
   ========================================================================== */
.announcement-bar {
    background-color: #000000 !important;
    color: #f6f3f1 !important;
    padding: 10px 24px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13px !important;
    letter-spacing: 0.04em !important;
    text-transform: uppercase !important;
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    border-radius: 8px !important;
    margin-bottom: 2rem !important;
}

.announcement-bar span {
    color: #f6f3f1 !important;
}

/* ==========================================================================
   HERO CONTAINER WITH SOFT BLURRED WASH
   ========================================================================== */
.hero-wrapper {
    position: relative !important;
    padding: 3rem 2.5rem 3rem 2.5rem !important;
    margin-bottom: 3.5rem !important;
    overflow: hidden !important;
}

.hero-wash {
    position: absolute !important;
    top: -20px !important;
    left: -20px !important;
    width: 380px !important;
    height: 220px !important;
    background: radial-gradient(circle, rgba(255, 148, 115, 0.28) 0%, rgba(160, 181, 235, 0.22) 65%, transparent 100%) !important;
    filter: blur(60px) !important;
    z-index: 0 !important;
    pointer-events: none !important;
}

.hero-content {
    position: relative !important;
    z-index: 1 !important;
}

.hero-subtitle {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 16px !important;
    color: #4e4d4d !important;
    max-width: 680px !important;
    margin-bottom: 2rem !important;
    line-height: 1.6 !important;
}

/* ==========================================================================
   CARDS (PARCHMENT, 1PX ASH BORDER, 40PX RADIUS, NO SHADOWS)
   ========================================================================== */
.monad-card {
    background-color: #f6f3f1 !important;
    border: 1px solid #cecac8 !important;
    border-radius: 40px !important;
    padding: 40px !important;
    margin-bottom: 2rem !important;
    box-shadow: none !important;
}

/* Highlight card surface (Periwinkle Mist) for one hero card */
.monad-card-highlight {
    background-color: #cfdaf5 !important;
    border: 1px solid #cecac8 !important;
    border-radius: 40px !important;
    padding: 40px !important;
    margin-bottom: 2rem !important;
    box-shadow: none !important;
}

.monad-card-highlight * {
    color: #242424 !important;
}

/* ==========================================================================
   BUTTONS (PILL SHAPE 100PX, PADDING 16PX 32PX, UPPERCASE)
   ========================================================================== */
/* Default / Secondary button */
.stButton > button {
    background-color: #242424 !important;
    color: #ffffff !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: -0.02em !important;
    border-radius: 100px !important;
    padding: 14px 28px !important;
    border: 1px solid #242424 !important;
    box-shadow: none !important;
    transition: all 0.15s ease !important;
}

.stButton > button:hover {
    background-color: #000000 !important;
    border-color: #000000 !important;
    color: #ffffff !important;
}

/* Primary Action Button: Lake Blue #2b59d1 */
.stButton > button[kind="primary"] {
    background-color: #2b59d1 !important;
    border-color: #2b59d1 !important;
    color: #ffffff !important;
}

.stButton > button[kind="primary"]:hover {
    background-color: #1e42a3 !important;
    border-color: #1e42a3 !important;
}

/* Ghost Pill Button */
.btn-ghost {
    display: inline-block !important;
    background: transparent !important;
    color: #242424 !important;
    border: 1px solid #242424 !important;
    border-radius: 100px !important;
    padding: 12px 28px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13px !important;
    text-transform: uppercase !important;
    letter-spacing: -0.02em !important;
    text-decoration: none !important;
    text-align: center !important;
}

/* ==========================================================================
   TABS STYLED AS PILLS
   ========================================================================== */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px !important;
    background-color: transparent !important;
    padding: 8px 0 !important;
    border-bottom: 1px solid #cecac8 !important;
    margin-bottom: 2rem !important;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 100px !important;
    padding: 10px 22px !important;
    background-color: transparent !important;
    border: 1px solid #cecac8 !important;
    color: #4e4d4d !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 12px !important;
    text-transform: uppercase !important;
    letter-spacing: -0.02em !important;
}

.stTabs [aria-selected="true"] {
    background-color: #242424 !important;
    border-color: #242424 !important;
    color: #f6f3f1 !important;
}

/* ==========================================================================
   INPUTS & TEXTAREAS (PARCHMENT FILL, 1PX ASH BORDER, RADIUS 20PX)
   ========================================================================== */
input, textarea, [data-baseweb="input"], [data-baseweb="textarea"] {
    background-color: #f6f3f1 !important;
    border: 1px solid #cecac8 !important;
    border-radius: 20px !important;
    color: #242424 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 14px !important;
}

input:focus, textarea:focus,
[data-baseweb="input"]:focus-within, [data-baseweb="textarea"]:focus-within {
    border-color: #242424 !important;
    box-shadow: none !important;
}

[data-baseweb="select"] {
    border-radius: 20px !important;
    border: 1px solid #cecac8 !important;
    background-color: #f6f3f1 !important;
}

/* ==========================================================================
   TAGS / BADGES (FULL PILL 100PX, 1PX ASH BORDER, UPPERCASE MONO)
   ========================================================================== */
.pill-badge {
    display: inline-block !important;
    border-radius: 100px !important;
    border: 1px solid #cecac8 !important;
    padding: 4px 14px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: -0.02em !important;
    font-weight: 500 !important;
}

.pill-low {
    background-color: #f6f3f1 !important;
    color: #1b633e !important;
    border-color: #a7fccd !important;
}

.pill-med {
    background-color: #f6f3f1 !important;
    color: #92400e !important;
    border-color: #ecda98 !important;
}

.pill-high {
    background-color: #f6f3f1 !important;
    color: #991b1b !important;
    border-color: #ff9473 !important;
}

/* ==========================================================================
   DIVIDERS & EXPANDERS
   ========================================================================== */
hr {
    border: none !important;
    border-top: 1px solid #cecac8 !important;
    margin: 3rem 0 !important;
}

/* Custom Expander */
[data-testid="stExpander"] {
    background-color: transparent !important;
    border: none !important;
    border-bottom: 1px solid #cecac8 !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    margin-bottom: 1.5rem !important;
}

[data-testid="stExpander"] details summary p {
    font-family: 'Newsreader', Georgia, serif !important;
    font-size: 22px !important;
    font-weight: 400 !important;
    color: #242424 !important;
}

/* Tables */
table {
    width: 100% !important;
    border-collapse: collapse !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13px !important;
}

table th {
    text-align: left !important;
    padding: 12px 14px !important;
    border-bottom: 1px solid #cecac8 !important;
    color: #797776 !important;
    text-transform: uppercase !important;
    font-size: 11px !important;
}

table td {
    padding: 12px 14px !important;
    border-bottom: 1px solid #cecac8 !important;
    color: #242424 !important;
}

/* Hide default streamlit clutter */
#MainMenu {visibility: hidden !important;}
footer {visibility: hidden !important;}
header {visibility: hidden !important;}
</style>
"""


def load_monad_styles() -> None:
    """Inject Monad Editorial design styles into the Streamlit app."""
    st.markdown(MONAD_CSS, unsafe_allow_html=True)
