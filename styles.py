"""ExportPilot — Monad Editorial Design System Stylesheet.

Aesthetic Guidelines:
- Parchment Warm White (#f6f3f1) page canvas with crisp white cards (#ffffff)
- Typography: Newsreader serif (weight 400 only, never bold) for hero and display headings
- Body & Data: JetBrains Mono monospace font for precision, tabular numerals, and data tables
- Controls: 100px rounded pill buttons (#2b59d1 Lake Blue), 40px rounded cards
- Zero Drop Shadows: Pure flat editorial feel with hairline borders (#e5e1db)
- Fixed Layout Table: Set column widths, wrapped text, vertically centered cells
"""

MONAD_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:ital,wght@0,300;0,400;0,500;0,600;1,400&family=Newsreader:ital,opsz,wght@0,6..72,300;0,6..72,400;1,6..72,300;1,6..72,400&display=swap');

:root {
  --bg-parchment: #f6f3f1;
  --surface-card: #ffffff;
  --border-hairline: #e5e1db;
  --text-primary: #242424;
  --text-muted: #797776;
  --text-body: #4e4d4d;
  --accent-blue: #2b59d1;
  --accent-blue-hover: #1e429f;
  --accent-highlight: #e9eefb;
  --radius-card: 40px;
  --radius-pill: 100px;
  --font-serif: 'Newsreader', Georgia, serif;
  --font-mono: 'JetBrains Mono', monospace;
}

/* Global Reset & Base Styling */
html, body, [data-testid="stAppViewContainer"] {
  background-color: var(--bg-parchment) !important;
  color: var(--text-primary) !important;
  font-family: var(--font-mono) !important;
  font-size: 14px;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}

[data-testid="stHeader"] {
  background-color: var(--bg-parchment) !important;
}

.stMainBlockContainer {
  max-width: 1320px !important;
  padding-top: 1rem !important;
  padding-left: 2.5rem !important;
  padding-right: 2.5rem !important;
  padding-bottom: 5rem !important;
}

/* Zero shadows enforcement */
*, *::before, *::after {
  box-shadow: none !important;
  text-shadow: none !important;
}

/* Top Announcement Bar */
.announcement-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #111111;
  color: #ffffff;
  padding: 10px 24px;
  border-radius: var(--radius-pill);
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: 0.04em;
  margin-bottom: 2rem;
}

/* Hero Section */
.hero-wrapper {
  position: relative;
  padding: 3rem 0 2rem 0;
  margin-bottom: 2rem;
}

.serif-hero {
  font-family: var(--font-serif) !important;
  font-size: 58px !important;
  font-weight: 400 !important;
  line-height: 1.08 !important;
  letter-spacing: -0.02em !important;
  color: var(--text-primary) !important;
  margin-bottom: 1rem !important;
}

.hero-subtitle {
  font-family: var(--font-mono);
  font-size: 15px;
  color: var(--text-body);
  max-width: 780px;
  line-height: 1.65;
  margin-bottom: 1.5rem;
}

/* Cards & Containers: 40px rounded corners on cards */
.monad-card {
  background-color: var(--surface-card) !important;
  border: 1px solid var(--border-hairline) !important;
  border-radius: var(--radius-card) !important;
  padding: 32px 36px !important;
  margin-bottom: 1.5rem !important;
}

.monad-card-highlight {
  background-color: var(--accent-highlight) !important;
  border: 1px solid #c7d7f7 !important;
  border-radius: var(--radius-card) !important;
  padding: 32px 36px !important;
  margin-bottom: 1.5rem !important;
}

/* Headings: Newsreader weight 400 */
.serif-card-title {
  font-family: var(--font-serif) !important;
  font-size: 26px !important;
  font-weight: 400 !important;
  line-height: 1.2 !important;
  color: var(--text-primary) !important;
  margin-bottom: 0.75rem !important;
}

.serif-section {
  font-family: var(--font-serif) !important;
  font-size: 34px !important;
  font-weight: 400 !important;
  color: var(--text-primary) !important;
  margin-top: 2rem !important;
  margin-bottom: 1rem !important;
}

/* Buttons: 100px rounded pills */
.stButton > button {
  font-family: var(--font-mono) !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  letter-spacing: 0.04em !important;
  border-radius: var(--radius-pill) !important;
  padding: 10px 24px !important;
  border: 1px solid var(--border-hairline) !important;
  background-color: var(--surface-card) !important;
  color: var(--text-primary) !important;
  transition: all 0.15s ease-in-out !important;
}

.stButton > button:hover {
  background-color: #ebe7e1 !important;
  color: var(--text-primary) !important;
  border-color: #cecac3 !important;
}

.stButton > button[kind="primary"] {
  background-color: var(--accent-blue) !important;
  color: #ffffff !important;
  border: 1px solid var(--accent-blue) !important;
}

.stButton > button[kind="primary"]:hover {
  background-color: var(--accent-blue-hover) !important;
  border-color: var(--accent-blue-hover) !important;
  color: #ffffff !important;
}

/* Distinct Black Outline for All Text Boxes & Inputs */
div[data-baseweb="base-input"],
div[data-baseweb="input"],
div[data-baseweb="textarea"],
.stTextInput > div > div,
.stTextArea > div > div,
.stNumberInput > div > div,
.stSelectbox > div > div,
.stSelectbox [data-baseweb="select"] > div {
  border: 1.5px solid #111111 !important;
  border-radius: 12px !important;
  background-color: #ffffff !important;
  color: #111111 !important;
  transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
}

/* Ensure inner input text and textarea fill container without double border */
div[data-baseweb="base-input"] input,
div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea,
.stTextInput input,
.stTextArea textarea,
.stNumberInput input,
.stForm input {
  border: none !important;
  outline: none !important;
  background-color: transparent !important;
  color: #111111 !important;
  font-family: var(--font-mono) !important;
  font-size: 13px !important;
}

/* Focused / active input state with bold black outline */
div[data-baseweb="base-input"]:focus-within,
div[data-baseweb="input"]:focus-within,
div[data-baseweb="textarea"]:focus-within,
.stTextInput > div > div:focus-within,
.stTextArea > div > div:focus-within,
.stNumberInput > div > div:focus-within,
.stSelectbox > div > div:focus-within,
.stSelectbox [data-baseweb="select"]:focus-within > div {
  border: 2px solid #000000 !important;
  box-shadow: 0 0 0 1px #000000 !important;
  background-color: #ffffff !important;
}

/* General fallback for any standalone input elements */
input[type="text"],
input[type="password"],
input[type="number"],
textarea {
  font-family: var(--font-mono) !important;
  color: #111111 !important;
}

/* Navigation Tabs styled as sleek Monad pills */
.stTabs [data-baseweb="tab-list"] {
  gap: 10px !important;
  background-color: transparent !important;
  border-bottom: none !important;
  margin-bottom: 2rem !important;
  padding: 4px 0 !important;
}

.stTabs [data-baseweb="tab"] {
  background-color: #eae6e1 !important;
  color: var(--text-muted) !important;
  font-family: var(--font-mono) !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  letter-spacing: 0.05em !important;
  padding: 10px 22px !important;
  border-radius: var(--radius-pill) !important;
  border: none !important;
  transition: all 0.15s ease !important;
}

.stTabs [data-baseweb="tab"]:hover {
  color: var(--text-primary) !important;
  background-color: #ded9d1 !important;
}

.stTabs [data-baseweb="tab"][aria-selected="true"] {
  background-color: var(--text-primary) !important;
  color: #ffffff !important;
}

/* Status Badges */
.pill-badge {
  display: inline-block;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.03em;
  padding: 4px 12px;
  border-radius: 9999px;
  border: 1px solid var(--border-hairline);
  background: #ffffff;
}

.pill-low {
  background-color: #edf7ed !important;
  color: #1b633e !important;
  border-color: #b7e1cd !important;
}

.pill-med {
  background-color: #fef7e0 !important;
  color: #b06000 !important;
  border-color: #fce8b2 !important;
}

.pill-high {
  background-color: #fce8e6 !important;
  color: #c5221f !important;
  border-color: #fad2cf !important;
}

/* ------------------------------------------------------------------------- */
/* 1. FIXED LAYOUT AUDIT LOG TABLE (FIX AUDIT LOG TABLE ALIGNMENT)            */
/* ------------------------------------------------------------------------- */
.audit-table-wrapper {
  width: 100% !important;
  overflow-x: auto !important;
  margin-top: 1rem !important;
  margin-bottom: 1.5rem !important;
  border: 1px solid var(--border-hairline) !important;
  border-radius: 20px !important;
  background-color: #ffffff !important;
}

.audit-table {
  width: 100% !important;
  table-layout: fixed !important;
  border-collapse: collapse !important;
  background-color: #ffffff !important;
  font-family: var(--font-mono) !important;
}

.audit-table col.col-time { width: 15% !important; }
.audit-table col.col-act  { width: 18% !important; }
.audit-table col.col-rat  { width: 37% !important; }
.audit-table col.col-risk { width: 10% !important; }
.audit-table col.col-stat { width: 12% !important; }
.audit-table col.col-user { width: 8% !important; }

.audit-table th {
  background-color: #f0ede8 !important;
  color: #555351 !important;
  font-family: var(--font-mono) !important;
  font-size: 11px !important;
  font-weight: 600 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
  padding: 14px 16px !important;
  border-bottom: 1px solid var(--border-hairline) !important;
  text-align: left !important;
  vertical-align: middle !important;
}

.audit-table td {
  padding: 14px 16px !important;
  border-bottom: 1px solid var(--border-hairline) !important;
  font-size: 12px !important;
  color: var(--text-primary) !important;
  vertical-align: middle !important;
  word-break: break-word !important;
  overflow-wrap: break-word !important;
  line-height: 1.5 !important;
}

.audit-table tr:last-child td {
  border-bottom: none !important;
}

.audit-table tr:hover {
  background-color: #faf8f5 !important;
}

/* User Session Badge */
.user-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background-color: #e5e1db;
  color: var(--text-primary);
  padding: 6px 14px;
  border-radius: var(--radius-pill);
  font-size: 12px;
  font-family: var(--font-mono);
}

.role-tag-admin {
  background-color: #111111;
  color: #ffffff;
  padding: 2px 8px;
  border-radius: 9999px;
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
}

.role-tag-exporter {
  background-color: var(--accent-blue);
  color: #ffffff;
  padding: 2px 8px;
  border-radius: 9999px;
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
}
</style>
"""


def load_monad_styles() -> None:
    """Inject Monad Editorial design CSS into Streamlit."""
    import streamlit as st
    st.markdown(MONAD_CSS, unsafe_allow_html=True)


def inject_stripe_styles() -> None:
    """Alias for backwards compatibility."""
    load_monad_styles()
