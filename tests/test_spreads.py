import pytest
from tarotcli.spreads import SpreadLayout, get_spread, THREE_CARD, CELTIC_CROSS
from tarotcli.models import FocusArea


def test_spread_layout_card_count():
    """Spread layout reports correct card count."""
    assert THREE_CARD.card_count() == 3
    assert CELTIC_CROSS.card_count() == 10


def test_get_spread_returns_correct_layout():
    """get_spread() retrieves correct spread by name."""
    spread = get_spread("three")
    assert spread.name == "three_card"
    assert len(spread.positions) == 3


def test_get_spread_raises_on_unknown():
    """Unknown spread name raises ValueError."""
    with pytest.raises(ValueError, match="Unknown spread"):
        get_spread("nonexistent")


def test_create_reading_assigns_positions(shuffled_deck):
    """create_reading() assigns position meanings to cards."""
    spread = get_spread("three")
    drawn = shuffled_deck.draw(3)

    reading = spread.create_reading(cards=drawn, focus_area=FocusArea.CAREER)

    assert reading.cards[0].position_meaning == "Past"
    assert reading.cards[1].position_meaning == "Present"
    assert reading.cards[2].position_meaning == "Future"


def test_create_reading_generates_baseline(shuffled_deck):
    """Baseline interpretation includes all cards."""
    spread = get_spread("three")
    drawn = shuffled_deck.draw(3)

    reading = spread.create_reading(
        cards=drawn,
        focus_area=FocusArea.RELATIONSHIPS,
        question="Will this relationship work?",
    )

    assert "Three Card Spread" in reading.baseline_interpretation
    assert "Question" in reading.baseline_interpretation
    # All drawn cards should appear in baseline
    assert all(dc.card.name in reading.baseline_interpretation for dc in drawn)


def test_create_reading_raises_on_wrong_count(shuffled_deck):
    """Mismatched card count raises ValueError."""
    spread = get_spread("celtic")  # Needs 10 cards
    drawn = shuffled_deck.draw(3)  # Only draw 3

    with pytest.raises(ValueError, match="requires 10 cards"):
        spread.create_reading(cards=drawn, focus_area=FocusArea.GENERAL)


def test_baseline_includes_focus_area(shuffled_deck):
    """Baseline interpretation mentions focus area."""
    spread = get_spread("three")
    drawn = shuffled_deck.draw(3)

    reading = spread.create_reading(cards=drawn, focus_area=FocusArea.SPIRITUAL)

    assert "Spiritual" in reading.baseline_interpretation


def test_reading_has_timestamp(shuffled_deck):
    """Reading includes ISO 8601 timestamp."""
    spread = get_spread("three")
    drawn = shuffled_deck.draw(3)

    reading = spread.create_reading(cards=drawn, focus_area=FocusArea.CAREER)

    assert reading.timestamp
    assert "T" in reading.timestamp  # ISO 8601 format
    # Check for timezone indicator (either Z or +/-)
    assert (
        reading.timestamp.endswith("Z")
        or "+" in reading.timestamp
        or reading.timestamp.count("-") >= 2
    )


def test_spread_names_in_registry():
    """All expected spreads exist in registry."""
    from tarotcli.spreads import SPREADS

    assert "single" in SPREADS
    assert "three" in SPREADS
    assert "celtic" in SPREADS


def test_celtic_cross_full_flow(shuffled_deck):
    """Celtic Cross spread works with 10 cards."""
    spread = get_spread("celtic")
    drawn = shuffled_deck.draw(10)

    reading = spread.create_reading(
        cards=drawn,
        focus_area=FocusArea.PERSONAL_GROWTH,
        question="What should I focus on?",
    )

    # Verify all 10 positions assigned
    assert len(reading.cards) == 10
    assert reading.cards[0].position_meaning == "Present Situation"
    assert reading.cards[9].position_meaning == "Outcome"

    # Verify baseline includes all positions
    for card in drawn:
        assert card.card.name in reading.baseline_interpretation
