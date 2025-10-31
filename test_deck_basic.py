#!/usr/bin/env python
"""Tarot deck operations: loading, shuffling, and drawing cards.

This module implements the core deck mechanics:
- Load 78 cards from JSONL with validation
- Shuffle deck with proper randomization
- Draw cards with 50% reversal probability
- Track remaining cards in current shuffle

The TarotDeck class maintains state of the current shuffle and ensures
cards are drawn without replacement until shuffle() is called again.

Example:
    >>> from pathlib import Path
    >>> deck = TarotDeck(Path("data/tarot_cards_clean.jsonl"))
    >>> deck.shuffle()
    >>> drawn = deck.draw(3)
    >>> print(f"Drew {len(drawn)} cards, {len(deck.remaining)} remain")
    Drew 3 cards, 75 remain
"""

from pathlib import Path
from tarotcli.deck import TarotDeck
import json

def test_basic_deck_operations():
    """Prove deck loading and drawing works."""
    
    # Load deck
    deck = TarotDeck(Path("data/tarot_cards_RW.jsonl"))
    print(f"✅ Loaded {len(deck.cards)} cards")
    
    # Shuffle
    deck.shuffle()
    print(f"✅ Shuffled deck, {len(deck.remaining)} cards ready")
    
    # Draw 3 cards
    drawn = deck.draw(3)
    print(f"✅ Drew {len(drawn)} cards")
    
    # Output as JSON
    output = {
        "cards": [
            {
                "name": dc.card.name,
                "position": dc.position,
                "reversed": dc.reversed,
                "meaning": dc.effective_meaning,
                "keywords": dc.card.keywords
            }
            for dc in drawn
        ]
    }
    
    print("\nJSON Output:")
    print(json.dumps(output, indent=2))
    
    print(f"\n✅ Remaining in deck: {len(deck.remaining)}")

if __name__ == "__main__":
    test_basic_deck_operations()