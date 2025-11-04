import pytest
from pathlib import Path
from tarotcli.deck import TarotDeck
from collections import Counter


def test_deck_loads_78_cards(deck_path):
    """Verify deck loads exactly 78 cards from JSONL."""
    deck = TarotDeck(deck_path)
    assert len(deck.cards) == 78
    assert len(deck.remaining) == 78


def test_deck_shuffle_maintains_card_count(deck_path):
    """Shuffling should reset to 78 cards."""
    deck = TarotDeck(deck_path)
    deck.draw(10)
    assert len(deck.remaining) == 68
    deck.shuffle()
    assert len(deck.remaining) == 78


def test_reset_without_shuffling(deck_path):
    """Reset returns to 78 cards without randomizing order."""
    deck = TarotDeck(deck_path)
    original_order = [c.id for c in deck.remaining]

    deck.draw(10)
    assert len(deck.remaining) == 68

    deck.reset()
    assert len(deck.remaining) == 78
    # Order should be original (sorted by value_int)
    assert [c.id for c in deck.remaining] == original_order


def test_draw_returns_correct_count(deck_path):
    """Drawing N cards returns exactly N cards."""
    deck = TarotDeck(deck_path)
    deck.shuffle()
    drawn = deck.draw(5)
    assert len(drawn) == 5
    assert all(isinstance(dc.card.name, str) for dc in drawn)


def test_draw_assigns_sequential_positions(deck_path):
    """Cards should have positions 0, 1, 2, etc."""
    deck = TarotDeck(deck_path)
    deck.shuffle()
    drawn = deck.draw(3)
    assert drawn[0].position == 0
    assert drawn[1].position == 1
    assert drawn[2].position == 2


def test_draw_depletes_deck(deck_path):
    """Drawing cards removes them from remaining (Celtic Cross scenario)."""
    deck = TarotDeck(deck_path)
    deck.shuffle()

    # Draw 10 cards (Celtic Cross)
    drawn = deck.draw(10)
    assert len(drawn) == 10
    assert len(deck.remaining) == 68

    # Verify drawn cards not in remaining
    drawn_ids = {dc.card.id for dc in drawn}
    remaining_ids = {c.id for c in deck.remaining}
    assert len(drawn_ids & remaining_ids) == 0  # No overlap


def test_reversal_distribution_over_500_draws(deck_path):
    """Over 500 draws, reversals should approximate 50% (±10%)."""
    deck = TarotDeck(deck_path)

    total_reversed = 0
    total_upright = 0

    # Draw 500 cards across multiple shuffles
    for _ in range(7):  # 7 shuffles × 70 cards = 490 draws
        deck.shuffle()
        drawn = deck.draw(70)
        total_reversed += sum(1 for dc in drawn if dc.reversed)
        total_upright += sum(1 for dc in drawn if not dc.reversed)

    total = total_reversed + total_upright
    reversal_rate = total_reversed / total

    # Allow 40-60% range (statistical variation expected)
    assert 0.40 <= reversal_rate <= 0.60, (
        f"Reversal rate {reversal_rate:.2%} outside expected 40-60% range"
    )


def test_card_distribution_over_500_draws(deck_path):
    """Each card should appear roughly equally over 500 draws."""
    deck = TarotDeck(deck_path)

    card_counts = Counter()

    # Draw 546 cards (7 full decks)
    for _ in range(7):
        deck.shuffle()
        drawn = deck.draw(78)
        for dc in drawn:
            card_counts[dc.card.id] += 1

    # Each card should appear exactly 7 times in 7 full deck draws
    for card_id, count in card_counts.items():
        assert count == 7, f"Card {card_id} appeared {count} times (expected 7)"


def test_draw_raises_on_insufficient_cards(deck_path):
    """Cannot draw more cards than remaining."""
    deck = TarotDeck(deck_path)
    deck.shuffle()
    deck.draw(70)  # 8 remaining

    with pytest.raises(ValueError, match="only 8 remaining"):
        deck.draw(10)


def test_deck_rejects_invalid_jsonl(tmp_path):
    """Invalid JSONL should raise ValueError with line number."""
    bad_file = tmp_path / "bad.jsonl"
    bad_file.write_text("not valid json\n")

    with pytest.raises(
        ValueError, match="Invalid JSON at line 1"
    ):  # Expecting line 1 for the error
        TarotDeck(bad_file)


def test_deck_rejects_incomplete_cards(tmp_path):
    """JSONL with missing fields should raise validation error."""
    bad_file = tmp_path / "incomplete.jsonl"
    # Missing required fields
    bad_file.write_text('{"id": "ar01", "name": "The Magician"}\n')

    with pytest.raises(Exception):  # Pydantic ValidationError
        TarotDeck(bad_file)
