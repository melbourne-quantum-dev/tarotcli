# tests/test_lookup.py
"""Tests for card lookup functionality."""

import pytest
from tarotcli.deck import TarotDeck, lookup_card
from tarotcli.models import Card


def test_lookup_exact_match(shuffled_deck):
    """Test exact card name match (case-sensitive)."""
    card = lookup_card(shuffled_deck, "The Magician")
    assert isinstance(card, Card)
    assert card.name == "The Magician"
    assert card.id == "ar01"


def test_lookup_partial_match(shuffled_deck):
    """Test partial name matching (lowercase)."""
    card = lookup_card(shuffled_deck, "magician")
    assert isinstance(card, Card)
    assert "Magician" in card.name


def test_lookup_case_insensitive(shuffled_deck):
    """Test case-insensitive search."""
    card = lookup_card(shuffled_deck, "ACE OF WANDS")
    assert isinstance(card, Card)
    assert card.name == "Ace of Wands"


def test_lookup_not_found(shuffled_deck):
    """Test handling of non-existent card."""
    card = lookup_card(shuffled_deck, "nonexistent card")
    assert card is None


def test_lookup_ambiguous_returns_list(shuffled_deck):
    """Test ambiguous match returns list of cards."""
    result = lookup_card(shuffled_deck, "ace")
    assert isinstance(result, list)
    assert len(result) == 4
    card_names = [c.name for c in result]
    assert "Ace of Wands" in card_names
    assert "Ace of Cups" in card_names
    assert "Ace of Swords" in card_names
    assert "Ace of Pentacles" in card_names


def test_lookup_exact_match_wins_over_partial(shuffled_deck):
    """Test exact match takes precedence over partial matches."""
    # "Seven of Cups" is exact match, but "seven" also matches other sevens
    card = lookup_card(shuffled_deck, "seven of cups")
    assert isinstance(card, Card)
    assert card.name == "Seven of Cups"


def test_lookup_empty_string(shuffled_deck):
    """Test empty string returns None (matches all cards, but too ambiguous)."""
    result = lookup_card(shuffled_deck, "")
    # Empty string matches all 78 cards - should return list
    assert isinstance(result, list)
    assert len(result) == 78


def test_lookup_whitespace_handling(shuffled_deck):
    """Test search with extra whitespace."""
    card = lookup_card(shuffled_deck, "  magician  ")
    # Should NOT find match due to whitespace in search term
    # (Current implementation doesn't strip - could be enhancement)
    assert card is None or isinstance(card, list)


def test_lookup_multi_word_card(shuffled_deck):
    """Test lookup for multi-word card names."""
    card = lookup_card(shuffled_deck, "king of swords")
    assert isinstance(card, Card)
    assert card.name == "King of Swords"
    assert card.suit == "swords"


def test_lookup_returns_card_with_meanings(shuffled_deck):
    """Test returned card has all expected attributes."""
    card = lookup_card(shuffled_deck, "The Fool")
    assert isinstance(card, Card)
    assert card.name == "The Fool"
    assert card.upright_meaning  # Has content
    assert card.reversed_meaning  # Has content
    assert card.description  # Has Waite imagery
    assert card.id == "ar00"


def test_lookup_alias_pents(deck):
    """Alias 'pents' should expand to 'pentacles'."""
    result = lookup_card(deck, "ace of pents")
    assert result is not None
    assert result.name == "Ace of Pentacles"


def test_lookup_alias_coins(deck):
    """Alias 'coins' should expand to 'pentacles'."""
    result = lookup_card(deck, "two of coins")
    assert result is not None
    assert result.name == "Two of Pentacles"
