"""
Pytest configuration and fixtures for TarotCLI tests.
"""
import pytest
from pathlib import Path

@pytest.fixture
def sample_card_data():
    """Sample card data for testing."""
    return {
        "id": "ar01",
        "name": "The Magician",
        "type": "major",
        "suit": None,
        "value": "1",
        "value_int": 1,
        "upright_meaning": "Skill, diplomacy, address, subtlety.",
        "reversed_meaning": "Physician, Magus, mental disease, disgrace.",
        "description": "A youthful figure in the robe of a magician...",
        "keywords": ["skill", "diplomacy", "address"],
        "arcana": "major",
        "dataset_version": "1.0.0"
    }

@pytest.fixture
def data_dir():
    """Path to data directory."""
    return Path(__file__).parent.parent / "data"
