"""Tarot deck operations: loading, shuffling, drawing, and card lookup.

This module implements the core deck mechanics:
- Load 78 cards from JSONL with validation
- Shuffle deck with proper randomisation
- Draw cards with 50% reversal probability
- Track remaining cards in current shuffle
- Lookup individual cards by name (fuzzy matching)

The TarotDeck class maintains state of the current shuffle and ensures
cards are drawn without replacement until shuffle() is called again.

The lookup_card() function provides card reference functionality for
physical deck readings and tarot learning.

Example:
    >>> from pathlib import Path
    >>> deck = TarotDeck(Path("data/tarot_cards_RW.jsonl"))
    >>> deck.shuffle()
    >>> drawn = deck.draw(3)
    >>> print(f"Drew {len(drawn)} cards, {len(deck.remaining)} remain")
    Drew 3 cards, 75 remain

    >>> # Card lookup for physical readings
    >>> deck = TarotDeck.load_default()
    >>> card = lookup_card(deck, "ace of wands")
    >>> print(f"{card.name}: {card.upright_meaning}")
"""

from pathlib import Path
from typing import List
import json
import random
from tarotcli.models import Card, DrawnCard
from tarotcli.config import get_config


class TarotDeck:
    """
    Manages the 78-card Rider-Waite tarot deck.

    Handles loading cards from JSONL dataset, shuffling, and drawing with
    randomised orientations (upright/reversed). Maintains state of remaining
    cards in current shuffle.

    Attributes:
        cards (List[Card]): Complete 78-card deck
        remaining (List[Card]): Cards not yet drawn in current shuffle

    Example:
        >>> deck = TarotDeck(Path("data/tarot_cards_RW.jsonl"))
        >>> deck.shuffle()
        >>> drawn = deck.draw(3)  # Draw 3 cards
        >>> print(f"Drew {len(drawn)} cards, {len(deck.remaining)} remain")

        >>> # Or use convenience method with config system:
        >>> deck = TarotDeck.load_default()
        >>> deck.shuffle()
    """

    @classmethod
    def load_default(cls) -> "TarotDeck":
        """Load deck from default location using config system.

        Convenience factory method that uses config.get_data_path() to locate
        the standard Rider-Waite deck. Eliminates need for manual path handling
        in application code.

        Why this pattern:
            - Config system handles path resolution (dev vs installed)
            - Users can override via TAROTCLI_DATA_DIR environment variable
            - Cleaner API: TarotDeck.load_default() vs TarotDeck(Path(...))

        Returns:
            TarotDeck: Initialized deck ready for shuffling and drawing.

        Raises:
            FileNotFoundError: If default deck file not found.
            ValueError: If deck data is invalid.

        Example:
            >>> deck = TarotDeck.load_default()
            >>> deck.shuffle()
            >>> cards = deck.draw(3)
        """
        config = get_config()
        deck_path = config.get_data_path("tarot_cards_RW.jsonl")
        return cls(deck_path)

    def __init__(self, data_path: Path):
        """
        Initialise deck by loading cards from JSONL file.

        Args:
            data_path: Path to tarot_cards_RW.jsonl file

        Raises:
            FileNotFoundError: If data_path doesn't exist
            ValueError: If JSONL contains invalid card data

        Note:
            Each line in JSONL must be valid JSON matching Card schema.
            File should contain exactly 78 cards (22 major + 56 minor).
        """
        if not data_path.exists():
            raise FileNotFoundError(f"Card data not found at {data_path}")

        self.cards: List[Card] = []
        with open(data_path, "r") as f:
            for line_num, line in enumerate(f, 1):
                try:
                    card_data = json.loads(line)
                    card = Card(**card_data)
                    self.cards.append(card)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON at line {line_num}: {e}") from e

        if len(self.cards) != 78:
            raise ValueError(f"Expected 78 cards, found {len(self.cards)}")

        self.cards.sort(key=lambda c: c.value_int)
        self.remaining = self.cards.copy()

    def shuffle(self, seed: int | None = None) -> None:
        """
        Reset to full 78-card deck with randomised order.

        **Call this ONCE per reading** (before drawing cards for a spread).
        Calling shuffle() again will reset the deck and invalidate any
        previously drawn cards.

        Physical analogy: Thoroughly mixing the deck before starting a reading.
        Card orientations (upright/reversed) are determined at draw time,
        not during shuffle.

        Args:
            seed: Optional random seed for reproducible shuffles. Use for testing
                  or comparing interpretations with identical card draws. If None,
                  uses system randomness (default behavior).

        Example:
            >>> deck.shuffle()        # Random shuffle (normal usage)
            >>> deck.shuffle(seed=42) # Reproducible shuffle (testing/comparison)

        Note:
            Do NOT call shuffle() between draws for the same reading.
            Use reset() only for testing with predictable order.
        """
        if seed is not None:
            random.seed(seed)

        self.remaining = self.cards.copy()
        random.shuffle(self.remaining)

    def draw(self, count: int) -> List[DrawnCard]:
        """
        Draw specified number of cards with randomised orientations.

        Each card has 50% chance of being reversed. Cards are removed from
        remaining deck (no replacement until shuffle() called).

        **Orientation determined at draw time**, not during shuffle. This is
        a design choice for simplicity - the end result (50% reversal rate)
        matches physical practice even if the mechanism differs.

        Args:
            count: Number of cards to draw

        Returns:
            List of DrawnCard objects with card, orientation, and position

        Raises:
            ValueError: If count > remaining cards in deck

        Physical analogy: Drawing cards from top of shuffled deck and
        placing them in spread positions.

        Example:
            >>> deck.shuffle()  # Once per reading
            >>> cards = deck.draw(10)  # Celtic Cross
            >>> # Now 68 cards remaining
            >>> # DO NOT shuffle() again until next reading
        """
        if count > len(self.remaining):
            raise ValueError(
                f"Cannot draw {count} cards, only {len(self.remaining)} remaining"
            )

        drawn = []
        for i in range(count):
            card = self.remaining.pop(0)
            is_reversed = random.choice([True, False])

            drawn_card = DrawnCard(card=card, reversed=is_reversed, position=i)
            drawn.append(drawn_card)

        return drawn

    def reset(self) -> None:
        """
        Return to full 78-card deck in original sorted order (by value_int).

        **For testing only** - provides predictable card order without
        randomisation. In production, use shuffle() instead.

        Physical analogy: Putting cards back in original box order
        (sorted by suit and value).
        """
        self.remaining = self.cards.copy()


def lookup_card(deck: TarotDeck, search_term: str) -> Card | list[Card] | None:
    """
    Find card by name using case-insensitive partial match.

    Supports fuzzy matching for user convenience: "ace wands", "Ace of Wands",
    "ACE OF WANDS" all match the same card. Returns single card for unique match,
    list of cards for ambiguous matches, or None if not found.

    Args:
        deck: TarotDeck instance with loaded cards.
        search_term: Card name or partial name to search.

    Returns:
        - Card: Single matching card
        - list[Card]: Multiple matches (ambiguous search)
        - None: No matches found

    Example:
        >>> deck = TarotDeck.load_default()
        >>> # Unique match
        >>> card = lookup_card(deck, "magician")
        >>> print(f"{card.name}: {card.upright_meaning}")

        >>> # Ambiguous match
        >>> result = lookup_card(deck, "ace")
        >>> if isinstance(result, list):
        ...     print(f"Found {len(result)} matches")

        >>> # Not found
        >>> card = lookup_card(deck, "nonexistent")
        >>> if card is None:
        ...     print("Card not found")
    """
    # Common abbreviations/aliases (longer aliases first to avoid partial replacement issues)
    aliases = [
        ("pents", "pentacles"),
        ("coins", "pentacles"),
    ]

    search_lower = search_term.lower()
    # Expand aliases (only replace once, skip if already expanded)
    for alias, full in aliases:
        if alias in search_lower and full not in search_lower:
            search_lower = search_lower.replace(alias, full)

    matches = [c for c in deck.cards if search_lower in c.name.lower()]

    if len(matches) == 0:
        return None
    elif len(matches) == 1:
        return matches[0]
    else:
        # Multiple matches - check for exact match first
        exact = [c for c in matches if c.name.lower() == search_lower]
        if exact:
            return exact[0]
        return matches  # Return all matches for ambiguous case
