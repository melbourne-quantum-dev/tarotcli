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
    >>> deck = TarotDeck(Path("data/tarot_cards_RW.jsonl"))
    >>> deck.shuffle()
    >>> drawn = deck.draw(3)
    >>> print(f"Drew {len(drawn)} cards, {len(deck.remaining)} remain")
    Drew 3 cards, 75 remain
"""

from pathlib import Path
from typing import List
import json
import random
from tarotcli.models import Card, DrawnCard

class TarotDeck:
    """Manages the 78-card tarot deck."""
    
    def __init__(self, data_path: Path):
        """Load cards from JSONL file."""
        if not data_path.exists():
            raise FileNotFoundError(f"Card data not found at {data_path}")
        
        self.cards: List[Card] = []
        with open(data_path, 'r') as f:
            for line in f:
                card_data = json.loads(line)
                card = Card(**card_data)
                self.cards.append(card)
        
        if len(self.cards) != 78:
            raise ValueError(f"Expected 78 cards, found {len(self.cards)}")
        
        self.cards.sort(key=lambda c: c.value_int)
        self.remaining = self.cards.copy()
    
    def shuffle(self) -> None:
        """Shuffle deck, reset to all 78 cards."""
        self.remaining = self.cards.copy()
        random.shuffle(self.remaining)
    
    def draw(self, count: int) -> List[DrawnCard]:
        """Draw N cards with randomised reversals."""
        if count > len(self.remaining):
            raise ValueError(
                f"Cannot draw {count} cards, only {len(self.remaining)} remaining"
            )
        
        drawn = []
        for i in range(count):
            card = self.remaining.pop(0)
            is_reversed = random.choice([True, False])
            
            drawn_card = DrawnCard(
                card=card,
                reversed=is_reversed,
                position=i
            )
            drawn.append(drawn_card)
        
        return drawn