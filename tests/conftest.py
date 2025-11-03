"""
Pytest configuration and fixtures for TarotCLI tests.
"""
import pytest
from pathlib import Path

@pytest.fixture
def deck_path():
    """Path to actual tarot dataset."""
    return Path("data/tarot_cards_RW.jsonl")