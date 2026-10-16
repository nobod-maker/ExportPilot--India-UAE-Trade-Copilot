# PRD: ExportPilot — India–UAE Trade Copilot

**Tagline**: Speak your deal. ExportPilot quotes it, checks the risk, and drafts the buyer message.  
**Category**: Best Business AI Agent (Dubai Create AI Agents Championship)  
**Demo**: Streamlit | Voice: Tamil, Hindi, English | Cost: ₹0 (Zero-Cost Free Tier)  
**Target Users**: Small Indian MSME exporters quoting deals to international buyers (primary focus: India to UAE).

---

## 1. Problem Statement
Small Indian exporters (garments, spices, leather, engineering goods, chemicals) face three friction points when dealing with UAE/Gulf buyers:
1. **Currency & Margin Uncertainty**: INR/AED conversions fluctuate. Exporters fail to factor in FX margins or currency buffers, causing lost profits.
2. **Cultural & Norm Nuances**: UAE trade practices (Friday prayer times / Sunday-Thursday vs Monday-Friday, formal English greeting norms, LC / advance deposit terms, Islamic calendar holidays like Eid/Ramadan) are often missed, weakening negotiation stature.
3. **Language Barrier & Friction**: Exporters naturally think and speak in Indian vernaculars (Tamil, Hindi, English), but need structured quotes and professional international trade English drafts instantly.
4. **Regulatory & Trade Risk**: Frequent changes in DGFT notifications, tariff adjustments under CEPA (India-UAE Comprehensive Economic Partnership Agreement), or Gulf import standards.

---

## 2. Product Objectives & Non-Goals
### Core Objectives
- **Zero-Cost Operation**: Run entirely on free tier APIs (`open.er-api.com` for FX, Gemini free tier for LLM/multimodal voice, RSS feeds for news, local SQLite for persistence).
- **Vernacular Voice-to-Deal**: Support voice notes in Tamil, Hindi, and English, returning immediate translation, structured deal extraction, live FX conversion, buyer norms, and drafted communications.
- **Strict Human-in-the-Loop (HITL)**: Agent ACTS (calculates, extracts, drafts), but NEVER finalizes or sends quotes without explicit user approval.
- **Measurable Business Impact**: Display time-to-quote acceleration (from ~45 mins manual to <30 secs) and estimated FX volatility loss avoided.

### Non-Goals
- Real money settlement / payment gateway integration.
- Direct live email/WhatsApp sending without user approval.
- Paid proprietary FX or market intelligence feeds.

---

## 3. Architecture & Tech Stack
- **Frontend / UI**: Streamlit with custom executive styling (Taste Skill: Swiss typographic clarity, dark/light balanced theme, zero AI clichés).
- **Agent Orchestration**: Minimal LangGraph / StateGraph agent loop (`agent/graph.py`).
- **LLM & Multimodal Voice**: `google-genai` (Gemini Flash) with graceful fallback/mock for environments awaiting API keys.
- **Data Persistence**: SQLite (`data/exportpilot.db`).
- **External Feeds**: Open Exchange Rates (`open.er-api.com/v6/latest/INR` - free, no key required), RSS feeds (`feedparser` for DGFT/Gulf business feeds).
- **Test Framework**: `pytest` with unit tests for each tool and end-to-end Playwright evaluation.

---

## 4. Reordered Atomic Execution Milestones (User-Optimized Priority)

### Phase 1: Core Agent Working End-to-End (M1 + M2)
- [ ] Requirements and dependencies configured (`streamlit`, `langgraph`, `google-genai`, `requests`, `feedparser`, `python-dotenv`, `pytest`).
- [ ] `data/buyer_norms.json` with comprehensive UAE trade norms (working week Mon-Fri with Fri midday break, LC / advance terms, formal English greeting style, Ramadan/Eid sensitivity, negotiation practices).
- [ ] `agent/tools.py` with `get_fx(base, quote)` (using `open.er-api.com/v6/latest/INR` with fallback cache) and `get_buyer_norms(country)`.
- [ ] `agent/prompts.py` for structured quote extraction and executive buyer email drafting.
- [ ] `agent/graph.py` LangGraph agent flow integrating state, FX, norms, quote calculations, and drafting with robust offline/mock fallback when `GEMINI_API_KEY` is not present.
- [ ] Core Streamlit baseline in `app.py` taking query (e.g. "Quote 500 cotton shirts to a Dubai buyer"), running agent flow, displaying live INR/AED and structured draft.
- [ ] `pytest tests/test_tools.py` and `tests/test_graph.py` passing green.

### Phase 2: Vernacular Voice Processing (Voice moved up)
- [ ] `agent/voice.py` handling audio input with Gemini multimodal transcription and translation (Tamil, Hindi, English).
- [ ] Streamlit `st.audio_input` integrated alongside persistent typed fallback box.
- [ ] UI shows detected language badge, raw transcript, and clean English translation fed directly into the agent.
- [ ] Pre-tested with vernacular sample queries.

### Phase 3: Human Approval Gate & Deal Storage (M5)
- [ ] Strict Human-in-the-Loop approval gate: App displays preview, requires explicit "Approve & Save Deal" button.
- [ ] `save_deal(...)` in SQLite (`data/exportpilot.db`). Nothing saved or finalized without explicit human click.
- [ ] Deals history table in `app.py` with export and status view.
- [ ] `pytest tests/test_db.py` verifying persistence and status guarantees.

### Phase 4: Trade News & Risk Assessment (M3 with Cached Fallback)
- [ ] `get_trade_news(country)` with live RSS feeds (DGFT, Gulf business, PIB) plus bundled local cached trade headlines fallback so the demo never fails.
- [ ] Risk scoring engine returning risk level (`Low`, `Medium`, `High`) with clear policy reasons.
- [ ] `pytest tests/test_risk.py` passing.

### Phase 5: UI Polish, Estimated Impact Panel & Deployment (M6)
- [ ] Taste Skill styling: bespoke executive workbench aesthetic, intentional typography, no generic purple gradients or AI clichés.
- [ ] Estimated Impact panel with transparent formulas:
  - *Time to Quote Saved*: (e.g., 45 min manual benchmark vs real-time seconds).
  - *Estimated FX Volatility Buffer Protected*: Explicitly labeled as "Estimated" showing formula `Total AED * Current Rate * Buffer % (e.g. 2.5%)`.
- [ ] Comprehensive `README.md` with architecture diagram, local run instructions, and Hugging Face Spaces deployment guide.
