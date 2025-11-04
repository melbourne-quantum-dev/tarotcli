"""
Pytest configuration and fixtures for TarotCLI tests.
"""
import pytest
from pathlib import Path
from tarotcli.deck import TarotDeck


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