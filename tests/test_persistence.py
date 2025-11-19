"""Tests for reading persistence functionality.

Tests JSONL storage, retrieval, and graceful error handling for reading history.
All tests use temporary directories to avoid polluting user data.
"""

import json
from pathlib import Path
import pytest
from datetime import datetime

from tarotcli.persistence import ReadingPersistence
from tarotcli.models import Reading, DrawnCard, FocusArea
from tarotcli.deck import TarotDeck
from tarotcli.spreads import get_spread


@pytest.fixture
def deck():
    """Load actual deck for testing."""
    return TarotDeck.load_default()


@pytest.fixture
def sample_reading(deck):
    """Create a sample reading for testing using real cards."""
    deck.shuffle(seed=42)  # Reproducible shuffle
    spread = get_spread("single")
    drawn = deck.draw(1)

    return spread.create_reading(
        cards=drawn,
        focus_area=FocusArea.GENERAL,
        question="Test question",
    )


@pytest.fixture
def temp_persistence(tmp_path):
    """Create persistence instance with temporary path."""
    return ReadingPersistence(config_override=tmp_path / "readings.jsonl")


def test_save_reading_creates_file(temp_persistence, sample_reading):
    """Test that saving a reading creates the JSONL file."""
    assert not temp_persistence.readings_path.exists()

    success = temp_persistence.save(sample_reading)

    assert success is True
    assert temp_persistence.readings_path.exists()


def test_save_reading_creates_parent_directory(tmp_path, sample_reading):
    """Test that save creates parent directory if it doesn't exist."""
    nested_path = tmp_path / "nested" / "deep" / "readings.jsonl"
    persistence = ReadingPersistence(config_override=nested_path)

    assert not nested_path.parent.exists()

    success = persistence.save(sample_reading)

    assert success is True
    assert nested_path.exists()
    assert nested_path.parent.exists()


def test_save_reading_appends_to_existing_file(temp_persistence, sample_reading):
    """Test that multiple saves append to the same file."""
    temp_persistence.save(sample_reading)
    temp_persistence.save(sample_reading)
    temp_persistence.save(sample_reading)

    # Read file and count lines
    with open(temp_persistence.readings_path, "r") as f:
        lines = f.readlines()

    assert len(lines) == 3
    # Each line should be valid JSON
    for line in lines:
        data = json.loads(line)
        assert data["spread_type"] == "single_card"


def test_load_all_empty_file(temp_persistence):
    """Test loading from non-existent file returns empty list."""
    readings = temp_persistence.load_all()
    assert readings == []


def test_load_all_returns_readings(temp_persistence, sample_reading):
    """Test loading all readings from file."""
    # Save multiple readings
    temp_persistence.save(sample_reading)
    temp_persistence.save(sample_reading)

    readings = temp_persistence.load_all()

    assert len(readings) == 2
    assert all(isinstance(r, Reading) for r in readings)
    assert readings[0].spread_type == "single_card"


def test_load_all_skips_malformed_lines(temp_persistence, sample_reading):
    """Test that load_all gracefully skips malformed JSON lines."""
    # Save valid reading
    temp_persistence.save(sample_reading)

    # Manually append malformed JSON
    with open(temp_persistence.readings_path, "a") as f:
        f.write("invalid json line\n")
        f.write('{"incomplete": "object"\n')  # Invalid JSON

    # Save another valid reading
    temp_persistence.save(sample_reading)

    readings = temp_persistence.load_all()

    # Should load only the 2 valid readings
    assert len(readings) == 2


def test_load_all_handles_empty_lines(temp_persistence, sample_reading):
    """Test that load_all skips empty lines."""
    temp_persistence.save(sample_reading)

    # Add empty lines
    with open(temp_persistence.readings_path, "a") as f:
        f.write("\n")
        f.write("   \n")  # Whitespace only

    temp_persistence.save(sample_reading)

    readings = temp_persistence.load_all()
    assert len(readings) == 2


def test_load_last_n_readings(temp_persistence, sample_reading):
    """Test loading last N readings."""
    # Save 10 readings
    for _ in range(10):
        temp_persistence.save(sample_reading)

    # Load last 3
    recent = temp_persistence.load_last(3)

    assert len(recent) == 3
    assert all(isinstance(r, Reading) for r in recent)


def test_load_last_when_fewer_than_n(temp_persistence, sample_reading):
    """Test load_last when file has fewer readings than requested."""
    # Save only 2 readings
    temp_persistence.save(sample_reading)
    temp_persistence.save(sample_reading)

    # Request last 10
    recent = temp_persistence.load_last(10)

    assert len(recent) == 2


def test_load_last_empty_file(temp_persistence):
    """Test load_last on non-existent file."""
    recent = temp_persistence.load_last(5)
    assert recent == []


def test_clear_all_deletes_file(temp_persistence, sample_reading):
    """Test that clear_all removes the readings file."""
    temp_persistence.save(sample_reading)
    assert temp_persistence.readings_path.exists()

    success = temp_persistence.clear_all()

    assert success is True
    assert not temp_persistence.readings_path.exists()


def test_clear_all_on_nonexistent_file(temp_persistence):
    """Test that clear_all succeeds even if file doesn't exist."""
    assert not temp_persistence.readings_path.exists()

    success = temp_persistence.clear_all()

    assert success is True


def test_reading_roundtrip(temp_persistence, sample_reading):
    """Test that readings can be saved and loaded without data loss."""
    original_question = "What should I focus on today?"
    sample_reading.question = original_question
    sample_reading.focus_area = FocusArea.CAREER

    temp_persistence.save(sample_reading)
    loaded_readings = temp_persistence.load_all()

    assert len(loaded_readings) == 1
    loaded = loaded_readings[0]

    assert loaded.spread_type == sample_reading.spread_type
    assert loaded.focus_area == sample_reading.focus_area
    assert loaded.question == original_question
    assert len(loaded.cards) == len(sample_reading.cards)
    assert loaded.static_interpretation == sample_reading.static_interpretation


def test_timestamp_preserved(temp_persistence, sample_reading):
    """Test that timestamp is preserved during save/load."""
    temp_persistence.save(sample_reading)
    loaded = temp_persistence.load_all()[0]

    # Timestamp should be preserved (Pydantic preserves as string in JSON serialization)
    assert loaded.timestamp is not None
    # After deserialization, Pydantic may keep it as string
    assert (
        loaded.timestamp == str(sample_reading.timestamp)
        or loaded.timestamp == sample_reading.timestamp
    )


def test_multiple_different_readings(temp_persistence, sample_reading, deck):
    """Test saving and loading different reading types."""
    # Create different reading types
    single = sample_reading  # Already single card

    # Create three card reading using real deck
    deck.shuffle(seed=99)
    spread = get_spread("three")
    drawn_three = deck.draw(3)
    three_card = spread.create_reading(
        cards=drawn_three,
        focus_area=FocusArea.RELATIONSHIPS,
        question=None,
    )

    temp_persistence.save(single)
    temp_persistence.save(three_card)

    loaded = temp_persistence.load_all()

    assert len(loaded) == 2
    assert loaded[0].spread_type == "single_card"
    assert loaded[1].spread_type == "three_card"
    assert len(loaded[1].cards) == 3


def test_save_handles_write_errors_gracefully(tmp_path, sample_reading):
    """Test that save fails gracefully when directory is read-only."""
    # Create a read-only directory (on Unix systems)
    readonly_dir = tmp_path / "readonly"
    readonly_dir.mkdir()
    readonly_path = readonly_dir / "readings.jsonl"

    persistence = ReadingPersistence(config_override=readonly_path)

    # Make directory read-only
    readonly_dir.chmod(0o444)

    try:
        success = persistence.save(sample_reading)
        # Should return False due to permission error
        assert success is False
    finally:
        # Restore permissions for cleanup
        readonly_dir.chmod(0o755)


def test_config_override_parameter(tmp_path, sample_reading):
    """Test that config_override parameter works."""
    custom_path = tmp_path / "custom_location.jsonl"
    persistence = ReadingPersistence(config_override=custom_path)

    assert persistence.readings_path == custom_path

    persistence.save(sample_reading)
    assert custom_path.exists()


def test_delete_last_removes_n_readings(temp_persistence, sample_reading):
    """Test that delete_last removes the specified number of readings."""
    # Save 10 readings
    for _ in range(10):
        temp_persistence.save(sample_reading)

    # Delete last 3
    success = temp_persistence.delete_last(3)

    assert success is True
    remaining = temp_persistence.load_all()
    assert len(remaining) == 7


def test_delete_last_removes_all_when_n_exceeds_total(temp_persistence, sample_reading):
    """Test that delete_last removes all readings when N >= total count."""
    # Save 5 readings
    for _ in range(5):
        temp_persistence.save(sample_reading)

    # Try to delete 10 (more than exist)
    success = temp_persistence.delete_last(10)

    assert success is True
    remaining = temp_persistence.load_all()
    assert len(remaining) == 0
    # File should be deleted when no readings remain
    assert not temp_persistence.readings_path.exists()


def test_delete_last_on_empty_file(temp_persistence):
    """Test that delete_last succeeds on empty/non-existent file."""
    success = temp_persistence.delete_last(5)
    assert success is True


def test_delete_last_preserves_older_readings(temp_persistence, sample_reading, deck):
    """Test that delete_last preserves older readings correctly."""
    # Create 3 different readings with distinguishable questions
    deck.shuffle(seed=1)
    reading1 = get_spread("single").create_reading(
        cards=deck.draw(1), focus_area=FocusArea.GENERAL, question="First question"
    )

    deck.shuffle(seed=2)
    reading2 = get_spread("single").create_reading(
        cards=deck.draw(1), focus_area=FocusArea.CAREER, question="Second question"
    )

    deck.shuffle(seed=3)
    reading3 = get_spread("single").create_reading(
        cards=deck.draw(1),
        focus_area=FocusArea.RELATIONSHIPS,
        question="Third question",
    )

    # Save in order
    temp_persistence.save(reading1)
    temp_persistence.save(reading2)
    temp_persistence.save(reading3)

    # Delete last 1 (should remove reading3)
    temp_persistence.delete_last(1)

    remaining = temp_persistence.load_all()
    assert len(remaining) == 2
    assert remaining[0].question == "First question"
    assert remaining[1].question == "Second question"


def test_delete_last_rewrites_file_correctly(temp_persistence, sample_reading):
    """Test that delete_last properly rewrites the JSONL file."""
    # Save 5 readings
    for _ in range(5):
        temp_persistence.save(sample_reading)

    # Delete last 2
    temp_persistence.delete_last(2)

    # Verify file integrity by reading it directly
    with open(temp_persistence.readings_path, "r") as f:
        lines = f.readlines()

    assert len(lines) == 3
    # Each line should be valid JSON
    for line in lines:
        data = json.loads(line)
        assert "spread_type" in data
