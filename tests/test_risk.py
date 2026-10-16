"""Unit tests for trade news and risk assessment."""

from __future__ import annotations

import pytest
from agent.tools import get_trade_news


def test_trade_news_uae_fields():
    """Verify UAE trade news contains required fields and valid articles."""
    news = get_trade_news("UAE")
    assert news["country"] == "UAE"
    assert "source" in news
    assert "articles" in news
    assert len(news["articles"]) >= 1
    for article in news["articles"]:
        assert "title" in article
        assert "source" in article
        assert "summary" in article
        assert "risk_impact" in article
