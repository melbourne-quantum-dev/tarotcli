"""
Pytest configuration and fixtures for TarotCLI tests.
"""

import pytest
from pathlib import Path
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
