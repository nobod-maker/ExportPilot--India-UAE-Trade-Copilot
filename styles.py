"""Stripe Design System — Indigo-Ink Ledger on Frosted Glass.

Strict financial-instrument design language:
- Pure white canvas (#ffffff) with cool mist (#f8fafd) surfaces and hairline borders (#e5edf5).
- Single vivid indigo (#533afd) for primary actions, active states, and focus rings.
- Weight 300 whisper headlines with tight tracking and tabular numerals.
- 4px radius on buttons, inputs, and cards. No shadows anywhere.
"""

STRIPE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  /* Colors */
  --color-indigo-ink: #533afd;
  --color-indigo-hover: #7389ff;
  --color-midnight-ink: #061b31;
  --color-slate: #64748d;
  --color-steel: #50617a;
  --color-smoke: #839bc8;
  --color-pure-white: #ffffff;
  --color-mist: #f8fafd;
  --color-frost: #e5edf5;
  --color-lavender-border: #b9b9f9;
  --color-lilac-border: #d6d9fc;
  --color-periwinkle-wash: #e8e9ff;
  --color-deep-violet: #182659;
  --color-amethyst-edge: #7f71e6;

  /* Typography */
  --font-stripe: 'sohne-var', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", sans-serif;
  --font-mono: "JetBrains Mono", ui-monospace, monospace;
}

/* Global Reset & Base Styling */
html, body, [data-testid="stAppViewContainer"] {
  background-color: var(--color-pure-white) !important;
  color: var(--color-midnight-ink) !important;
  font-family: var(--font-stripe) !important;
  font-feature-settings: "ss01" on, "tnum" on !important;
  -webkit-font-smoothing: antialiased;
}

[data-testid="stHeader"] {
  background-color: var(--color-pure-white) !important;
  border-bottom: 1px solid var(--color-frost) !important;
}

.stMainBlockContainer {
  max-width: 1320px !important;
  padding-top: 1.5rem !important;
  padding-left: 2rem !important;
  padding-right: 2rem !important;
  padding-bottom: 4rem !important;
}

/* Zero shadows enforcement */
*, *::before, *::after {
  box-shadow: none !important;
  text-shadow: none !important;
}

/* Top Announcement / Wordmark Bar */
.announcement-bar, .stripe-navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background-color: var(--color-mist) !important;
  border: 1px solid var(--color-frost);
  border-radius: 4px;
  margin-bottom: 24px;
  font-size: 13px;
  font-weight: 400;
  color: var(--color-steel);
}

.stripe-brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stripe-wordmark {
  font-size: 20px;
  font-weight: 500;
  color: var(--color-midnight-ink);
  letter-spacing: -0.4px;
}

.stripe-badge {
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  background-color: var(--color-periwinkle-wash);
  color: var(--color-indigo-ink);
  padding: 4px 8px;
  border-radius: 9999px;
}

/* Hero Section */
.hero-wrapper {
  margin-bottom: 32px;
}

.serif-hero, .stripe-display {
  font-family: var(--font-stripe) !important;
  font-size: 52px !important;
  font-weight: 300 !important;
  line-height: 1.05 !important;
  letter-spacing: -1.4px !important;
  color: var(--color-midnight-ink) !important;
  margin: 0 0 16px 0 !important;
}

.hero-subtitle, .stripe-lead {
  font-size: 18px !important;
  line-height: 1.5 !important;
  color: var(--color-slate) !important;
  font-weight: 300 !important;
  max-width: 820px;
  margin-bottom: 24px !important;
}

/* Headings */
h1, h2, h3, .serif-card-title, .stripe-heading-lg {
  font-family: var(--font-stripe) !important;
  font-weight: 300 !important;
  color: var(--color-midnight-ink) !important;
}

h1 {
  font-size: 40px !important;
  letter-spacing: -0.96px !important;
}

h2, .stripe-heading-lg {
  font-size: 28px !important;
  letter-spacing: -0.64px !important;
}

h3, .serif-card-title {
  font-size: 20px !important;
  letter-spacing: -0.3px !important;
  margin-bottom: 12px !important;
}

p, .stripe-body {
  font-size: 14px !important;
  line-height: 1.55 !important;
  color: var(--color-steel) !important;
  font-weight: 400 !important;
}

/* Cards & Surfaces: 4px radius, no shadow, hairline border */
.monad-card, .stripe-card {
  background-color: var(--color-pure-white) !important;
  border: 1px solid var(--color-frost) !important;
  border-radius: 4px !important;
  padding: 24px !important;
  margin-bottom: 16px !important;
}

.stripe-card-mist {
  background-color: var(--color-mist) !important;
  border: 1px solid var(--color-frost) !important;
  border-radius: 4px !important;
  padding: 24px !important;
  margin-bottom: 16px !important;
}

.stripe-card-highlight {
  background-color: var(--color-periwinkle-wash) !important;
  border: 1px solid var(--color-lilac-border) !important;
  border-radius: 4px !important;
  padding: 24px !important;
  margin-bottom: 16px !important;
}

/* Metric / Stat Blocks: Whisper-weight display with tabular numerals */
.stripe-metric-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stripe-metric-card {
  background-color: var(--color-pure-white);
  border: 1px solid var(--color-frost);
  border-radius: 4px;
  padding: 20px;
}

.stripe-metric-value {
  font-family: var(--font-stripe);
  font-size: 44px;
  font-weight: 300;
  letter-spacing: -1.0px;
  line-height: 1.0;
  color: var(--color-midnight-ink);
  font-feature-settings: "tnum" on;
  margin-bottom: 6px;
}

.stripe-metric-label {
  font-size: 13px;
  color: var(--color-slate);
  font-weight: 400;
}

/* Tab Navigation Styling */
.stTabs [data-baseweb="tab-list"] {
  background-color: transparent !important;
  border-bottom: 1px solid var(--color-frost) !important;
  gap: 8px !important;
  padding-bottom: 0 !important;
  margin-bottom: 24px !important;
}

.stTabs [data-baseweb="tab"] {
  background-color: transparent !important;
  color: var(--color-slate) !important;
  font-size: 14px !important;
  font-weight: 400 !important;
  padding: 10px 16px !important;
  border: none !important;
  border-bottom: 2px solid transparent !important;
  border-radius: 0 !important;
  transition: all 0.15s ease-in-out !important;
}

.stTabs [data-baseweb="tab"]:hover {
  color: var(--color-midnight-ink) !important;
  border-bottom-color: var(--color-lilac-border) !important;
}

.stTabs [data-baseweb="tab"][aria-selected="true"] {
  color: var(--color-indigo-ink) !important;
  font-weight: 500 !important;
  border-bottom-color: var(--color-indigo-ink) !important;
}

/* Buttons: 4px radius, no shadow */
.stButton > button {
  background-color: var(--color-pure-white) !important;
  color: var(--color-indigo-ink) !important;
  border: 1px solid var(--color-lavender-border) !important;
  border-radius: 4px !important;
  font-size: 14px !important;
  font-weight: 400 !important;
  padding: 10px 20px !important;
  transition: background-color 0.15s ease, border-color 0.15s ease !important;
}

.stButton > button:hover {
  background-color: var(--color-mist) !important;
  border-color: var(--color-indigo-ink) !important;
  color: var(--color-indigo-ink) !important;
}

.stButton > button[kind="primary"] {
  background-color: var(--color-indigo-ink) !important;
  color: var(--color-pure-white) !important;
  border: 1px solid var(--color-indigo-ink) !important;
}

.stButton > button[kind="primary"]:hover {
  background-color: var(--color-indigo-hover) !important;
  border-color: var(--color-indigo-hover) !important;
  color: var(--color-pure-white) !important;
}

/* Inputs & Text Areas: 4px radius, hairline border */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
  background-color: var(--color-pure-white) !important;
  color: var(--color-midnight-ink) !important;
  border: 1px solid var(--color-frost) !important;
  border-radius: 4px !important;
  font-size: 14px !important;
  font-family: var(--font-stripe) !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
  border-color: var(--color-indigo-ink) !important;
}

/* Tables & Dataframes: Ledger format */
table, .stDataFrame {
  border-collapse: collapse !important;
  width: 100% !important;
  border: 1px solid var(--color-frost) !important;
  border-radius: 4px !important;
  background-color: var(--color-pure-white) !important;
}

th {
  background-color: var(--color-mist) !important;
  color: var(--color-steel) !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.5px !important;
  border-bottom: 1px solid var(--color-frost) !important;
  padding: 12px 16px !important;
  text-align: left !important;
}

td {
  color: var(--color-midnight-ink) !important;
  font-size: 14px !important;
  border-bottom: 1px solid var(--color-frost) !important;
  padding: 12px 16px !important;
}

/* Status Badges: Clean tag pills */
.pill-badge, .badge-indigo {
  display: inline-block;
  background-color: var(--color-periwinkle-wash);
  color: var(--color-indigo-ink);
  border: 1px solid var(--color-lilac-border);
  padding: 3px 10px;
  font-size: 11px;
  font-weight: 500;
  border-radius: 9999px;
}

.pill-low, .badge-low {
  background-color: #ecfdf5 !important;
  color: #065f46 !important;
  border-color: #a7f3d0 !important;
}

.pill-med, .badge-med {
  background-color: #fffbeb !important;
  color: #92400e !important;
  border-color: #fde68a !important;
}

.pill-high, .badge-high {
  background-color: #fef2f2 !important;
  color: #991b1b !important;
  border-color: #fecaca !important;
}

/* Monospace code / calculation preview */
.stripe-code, pre, code {
  font-family: var(--font-mono) !important;
  font-size: 13px !important;
  color: var(--color-deep-violet) !important;
  background-color: var(--color-mist) !important;
  border: 1px solid var(--color-frost) !important;
  border-radius: 4px !important;
}

/* Divider */
hr, .stripe-divider {
  border: none !important;
  border-top: 1px solid var(--color-frost) !important;
  margin: 32px 0 !important;
}
</style>
"""


def load_monad_styles() -> None:
    """Inject Stripe Financial Ledger design CSS into Streamlit page."""
    import streamlit as st
    st.markdown(STRIPE_CSS, unsafe_allow_html=True)


def inject_stripe_styles() -> None:
    """Alias for load_monad_styles."""
    load_monad_styles()
