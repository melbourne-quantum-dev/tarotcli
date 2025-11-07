"""
Tests for AI interpretation integration (LiteLLM/Claude API).

All tests use mocked API responses - no real API calls required.
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from tarotcli.ai import (
    interpret_reading,
    interpret_reading_sync,
    _build_interpretation_prompt,
    FOCUS_CONTEXTS,
)
from tarotcli.models import FocusArea


@pytest.mark.asyncio
async def test_interpret_reading_returns_baseline_without_api_key(
    sample_reading, mock_config
):
    """When no API key present, immediately return baseline interpretation."""
    
    # Ensure default provider is claude and API key returns None
    mock_config.get.return_value = "claude"
    
    def mock_get_api_key_side_effect(provider=None):
        # Debug: Return None for claude specifically
        if provider == "claude" or provider is None:
            return None
        return f"test-{provider}-key-123"
    
    mock_config.get_api_key.side_effect = mock_get_api_key_side_effect

    with patch("tarotcli.ai.get_config", return_value=mock_config):
        result = await interpret_reading(sample_reading)

        assert result == sample_reading.baseline_interpretation


@pytest.mark.asyncio
async def test_interpret_reading_calls_api_with_key(sample_reading, mock_config):
    """With API key present, should attempt API call."""

    # Mock successful API response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="AI interpretation here"))
    ]

    with patch("tarotcli.ai.get_config", return_value=mock_config), \
         patch("tarotcli.ai.acompletion", return_value=mock_response) as mock_call:
        
        result = await interpret_reading(sample_reading)

        assert result == "AI interpretation here"
        assert mock_call.called
        assert mock_call.call_args[1]["model"] == "claude-sonnet-4-20250514"
        assert mock_call.call_args[1]["temperature"] == 0.7
        assert mock_call.call_args[1]["stream"] is False


@pytest.mark.asyncio
async def test_interpret_reading_handles_timeout(sample_reading, mock_config):
    """On API timeout, should return baseline gracefully."""

    with patch("tarotcli.ai.get_config", return_value=mock_config), \
         patch("tarotcli.ai.acompletion", side_effect=asyncio.TimeoutError):
        
        result = await interpret_reading(sample_reading)

        assert result == sample_reading.baseline_interpretation


@pytest.mark.asyncio
async def test_interpret_reading_handles_api_error(sample_reading, mock_config):
    """On generic API error, should return baseline gracefully."""

    with patch("tarotcli.ai.get_config", return_value=mock_config), \
         patch("tarotcli.ai.acompletion", side_effect=Exception("API Error")):
        
        result = await interpret_reading(sample_reading)

        assert result == sample_reading.baseline_interpretation


@pytest.mark.asyncio
async def test_interpret_reading_handles_none_content(sample_reading, mock_config):
    """When API returns None content, should fallback to baseline."""

    # Mock response with None content
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=None))]

    with patch("tarotcli.ai.get_config", return_value=mock_config), \
         patch("tarotcli.ai.acompletion", return_value=mock_response):
        
        result = await interpret_reading(sample_reading)

        assert result == sample_reading.baseline_interpretation


@pytest.mark.asyncio
async def test_interpret_reading_respects_custom_timeout(sample_reading, mock_config):
    """Custom timeout parameter should be passed to API call."""

    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Test"))]

    with patch("tarotcli.ai.get_config", return_value=mock_config), \
         patch("tarotcli.ai.acompletion", return_value=mock_response) as mock_call:
        
        await interpret_reading(sample_reading, timeout=60)

        assert mock_call.call_args[1]["timeout"] == 60


@pytest.mark.asyncio
async def test_interpret_reading_respects_custom_provider(sample_reading, mock_config):
    """Custom provider parameter should be passed to API call."""

    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Test"))]

    with patch("tarotcli.ai.get_config", return_value=mock_config), \
         patch("tarotcli.ai.acompletion", return_value=mock_response) as mock_call:
        
        await interpret_reading(sample_reading, provider="openai")

        assert mock_call.call_args[1]["model"] == "gpt-4"


def test_build_interpretation_prompt_includes_spread_type(sample_reading):
    """Prompt should include spread type."""
    prompt = _build_interpretation_prompt(sample_reading)

    assert "Three Card" in prompt or "three card" in prompt.lower()


def test_build_interpretation_prompt_includes_focus_context(sample_reading):
    """Prompt should include focus area context."""
    prompt = _build_interpretation_prompt(sample_reading)

    focus_context = FOCUS_CONTEXTS[sample_reading.focus_area]
    assert focus_context in prompt


def test_build_interpretation_prompt_includes_question(sample_reading):
    """Prompt should include user's question if provided."""
    prompt = _build_interpretation_prompt(sample_reading)

    assert sample_reading.question in prompt
    assert "Should I freelance?" in prompt


def test_build_interpretation_prompt_includes_all_cards(sample_reading):
    """Prompt should mention all drawn cards."""
    prompt = _build_interpretation_prompt(sample_reading)

    for card in sample_reading.cards:
        assert card.card.name in prompt
        assert card.position_meaning in prompt


def test_build_interpretation_prompt_includes_orientation(sample_reading):
    """Prompt should indicate upright/reversed for each card."""
    prompt = _build_interpretation_prompt(sample_reading)

    # Should contain "Upright" or "Reversed" for each card
    orientation_count = prompt.count("Upright") + prompt.count("Reversed")
    assert orientation_count == len(sample_reading.cards)


def test_build_interpretation_prompt_includes_traditional_meanings(sample_reading):
    """Prompt should include traditional card meanings."""
    prompt = _build_interpretation_prompt(sample_reading)

    for card in sample_reading.cards:
        # Each card's effective meaning should be in prompt
        assert card.effective_meaning in prompt


def test_build_interpretation_prompt_includes_imagery_description(sample_reading):
    """Prompt should include Waite's imagery descriptions (core differentiator)."""
    prompt = _build_interpretation_prompt(sample_reading)

    for card in sample_reading.cards:
        # Each card's imagery description should be in prompt
        assert card.card.description in prompt


def test_build_interpretation_prompt_includes_guidelines(sample_reading):
    """Prompt should include interpretation guidelines."""
    prompt = _build_interpretation_prompt(sample_reading)

    # Check for key guideline phrases
    assert "interpretation" in prompt.lower()
    assert "practical" in prompt.lower() or "actionable" in prompt.lower()


def test_interpret_reading_sync_wrapper(sample_reading, mock_config):
    """Sync wrapper should execute async function and return result."""
    
    # Ensure default provider is claude and API key returns None
    mock_config.get.return_value = "claude"
    
    def mock_get_api_key_side_effect(provider=None):
        # Debug: Return None for claude specifically
        if provider == "claude" or provider is None:
            return None
        return f"test-{provider}-key-123"
    
    mock_config.get_api_key.side_effect = mock_get_api_key_side_effect

    with patch("tarotcli.ai.get_config", return_value=mock_config):
        result = interpret_reading_sync(sample_reading)

        assert result == sample_reading.baseline_interpretation


def test_interpret_reading_sync_passes_kwargs(sample_reading, mock_config):
    """Sync wrapper should pass through kwargs to async function."""

    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Test result"))]

    with patch("tarotcli.ai.get_config", return_value=mock_config), \
         patch("tarotcli.ai.acompletion", return_value=mock_response):
        
        result = interpret_reading_sync(
            sample_reading, provider="ollama", timeout=45
        )

        assert result == "Test result"


def test_focus_contexts_complete():
    """All FocusArea enum values should have context templates."""
    for focus_area in FocusArea:
        assert focus_area in FOCUS_CONTEXTS
        assert isinstance(FOCUS_CONTEXTS[focus_area], str)
        assert len(FOCUS_CONTEXTS[focus_area]) > 0


def test_focus_context_career_mentions_professional():
    """Career context should reference professional development."""
    career_context = FOCUS_CONTEXTS[FocusArea.CAREER]
    assert (
        "professional" in career_context.lower() or "career" in career_context.lower()
    )


def test_focus_context_relationships_mentions_interpersonal():
    """Relationships context should reference connections."""
    relationships_context = FOCUS_CONTEXTS[FocusArea.RELATIONSHIPS]
    assert (
        "relationship" in relationships_context.lower()
        or "interpersonal" in relationships_context.lower()
    )
