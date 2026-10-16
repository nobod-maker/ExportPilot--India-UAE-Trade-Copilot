"""Unit tests for voice processing and benchmark dataset in ExportPilot."""

from __future__ import annotations

import pytest
from agent.voice import (
    SAMPLE_VERNACULAR_QUERIES,
    transcribe_and_translate_audio,
)


def test_benchmark_dataset_structure():
    """Verify 10 Tamil, 10 Hindi, and 10 English sample queries exist with translations."""
    assert "ta" in SAMPLE_VERNACULAR_QUERIES
    assert "hi" in SAMPLE_VERNACULAR_QUERIES
    assert "en" in SAMPLE_VERNACULAR_QUERIES

    assert len(SAMPLE_VERNACULAR_QUERIES["ta"]) == 10
    assert len(SAMPLE_VERNACULAR_QUERIES["hi"]) == 10
    assert len(SAMPLE_VERNACULAR_QUERIES["en"]) == 10

    # Test that each item has non-empty transcript and english translation
    for lang, items in SAMPLE_VERNACULAR_QUERIES.items():
        for item in items:
            assert len(item["transcript"].strip()) > 0
            assert len(item["english"].strip()) > 0


def test_voice_fallback():
    """Verify audio handler handles dummy bytes cleanly without throwing unhandled exceptions."""
    dummy_audio = b"RIFF....WAVEfmt ...."
    result = transcribe_and_translate_audio(dummy_audio, mime_type="audio/wav")
    assert isinstance(result, dict)
    assert "language" in result
    assert "transcript" in result
    assert "english" in result
