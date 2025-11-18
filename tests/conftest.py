"""
Pytest configuration and fixtures for TarotCLI tests.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from tarotcli.deck import TarotDeck
from tarotcli.models import FocusArea
from tarotcli.spreads import get_spread


@pytest.fixture
def deck_path():
    """Path to actual tarot dataset."""
    return Path("data/tarot_cards_RW.jsonl")


@pytest.fixture
def deck(deck_path):
    """Loaded deck ready for testing."""
    return TarotDeck(deck_path)


@pytest.fixture
def shuffled_deck(deck):
    """Shuffled deck ready for drawing."""
    deck.shuffle()
    return deck


@pytest.fixture
def sample_reading(shuffled_deck):
    """Complete reading for AI interpretation testing."""
    spread = get_spread("three")
    drawn = shuffled_deck.draw(3)

    reading = spread.create_reading(
        cards=drawn, focus_area=FocusArea.CAREER, question="Should I freelance?"
    )

    return reading


@pytest.fixture
def mock_config():
    """Mock configuration for testing AI functions in isolation.

    Provides predictable, test-configurable values instead of reading
    user's actual config.yaml files which would cause test interference.

    Returns:
        MagicMock: Mock config instance with predefined responses:
            - default_provider: "claude"
            - get_model_config: Returns provider-specific configs
            - get_api_key: Returns test API keys
    """
    config = MagicMock()

    # Default provider
    config.get.return_value = "claude"

    # Model configs for different providers
    def mock_get_model_config(provider=None):
        if provider is None:
            provider = "claude"

        configs = {
            "claude": {
                "model": "claude-sonnet-4-20250514",
                "temperature": 0.7,
                "max_tokens": 2000,
            },
            "ollama": {
                "model": "ollama_chat/deepseek-r1:8b",
                "api_base": "http://localhost:11434",
                "temperature": 0.8,
                "max_tokens": 1500,
            },
            "openai": {
                "model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 2000,
            },
        }
        return configs.get(provider, {})

    config.get_model_config.side_effect = mock_get_model_config

    # API key responses
    def mock_get_api_key(provider=None):
        if provider is None:
            provider = "claude"

        # Only Ollama doesn't need API key
        if provider == "ollama":
            return None
        return f"test-{provider}-key-123"

    config.get_api_key.side_effect = mock_get_api_key

    return config
