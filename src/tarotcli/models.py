"""Data models for tarot cards and readings.

This module defines the core Pydantic models used throughout TarotCLI:
- Card: Represents a single tarot card from the 78-card Rider-Waite deck
- DrawnCard: A card as drawn in a reading, with orientation and position

All models provide automatic validation, JSON serialisation, and type safety.
The models are designed to work directly with the tarot_cards_RW.jsonl
dataset without requiring dataset modifications.

Example:
    >>> card = Card(id="ar01", name="The Magician", type="major", ...)
    >>> drawn = DrawnCard(card=card, reversed=False, position=0)
    >>> print(drawn.effective_meaning)
    "Skill, diplomacy, address, subtlety..."
"""

from pydantic import BaseModel, Field
from typing import Literal

class Card(BaseModel):
    """Single tarot card from dataset."""
    id: str
    name: str
    type: Literal["major", "minor"]
    suit: str | None
    value: str
    value_int: int
    upright_meaning: str
    reversed_meaning: str
    description: str
    
class DrawnCard(BaseModel):
    """Card as drawn with orientation."""
    card: Card
    reversed: bool
    position: int
    
    @property
    def effective_meaning(self) -> str:
        """Returns upright or reversed meaning based on orientation."""
        return self.card.reversed_meaning if self.reversed else self.card.upright_meaning