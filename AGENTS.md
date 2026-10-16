PROJECT: ExportPilot, an AI agent that helps small Indian exporters quote and manage deals with buyers (focus: India to UAE).

HARD RULES
- Zero cost: only free tiers and open-source libraries. No paid APIs.
- Stack: Python 3.11+, Streamlit (UI), LangGraph (agent flow), SQLite (storage), google-genai (Gemini), requests, feedparser.
- Original code only. Do not copy existing repositories.
- Secrets only in .env. Never hardcode keys. Never commit .env.
- The agent must ACT (create quote, save record, draft message) but must NEVER send or finalize anything without an explicit human approval click.
- Use synthetic/demo data only. No real customer data.
- Every tool function gets a unit test. Run tests before saying a task is done.
- Keep files small and clear. Add short docstrings.
- All UI text, README and docs in English (voice input also accepts Tamil/Hindi).
- If a free-tier limit is hit, fail gracefully with a clear message.

WORKFLOW
- Plan first, list steps, then build. Work one milestone at a time.
- After each milestone: run the app/tests, report what works and what does not.
