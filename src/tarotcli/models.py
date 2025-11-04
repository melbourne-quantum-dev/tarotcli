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

from typing import Literal
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class FocusArea(str, Enum):
    """Reading focus areas for LLM context."""

    CAREER = "career"
    RELATIONSHIPS = "relationships"
    PERSONAL_GROWTH = "personal_growth"
    SPIRITUAL = "spiritual"
    GENERAL = "general"


class Card(BaseModel):
    """Single tarot card from dataset."""

    id: str = Field(
        ..., description="Unique card identifier (e.g. 'ar01' for Major Arcana 1)"
    )
    name: str = Field(..., description="Card name (e.g. 'The Magician')")
    type: Literal["major", "minor"] = Field(
        ..., description="Arcana type - major for trumps, minor for suits"
    )
    suit: str | None = Field(
        None,
        description=(
            "Suit for minor arcana (wands, cups, swords, pentacles). Null for major arcana."
        ),
    )
    value: str = Field(
        ..., description="Card value as string (e.g. '1', 'queen', 'knight')"
    )
    value_int: int = Field(
        ..., description="Numeric value for sorting (0-21 major, 1-14 minor)"
    )
    upright_meaning: str = Field(
        ...,
        description=(
            "Traditional upright interpretation from Waite's Pictorial Key to the Tarot (1911)"
        ),
    )
    reversed_meaning: str = Field(
        ...,
        description=(
            "Traditional reversed interpretation from Waite's Pictorial Key to the Tarot (1911)"
        ),
    )
    description: str = Field(
        ...,
        description=(
            "Card imagery description from Waite's original text. "
            "Used for AI interpretation context."
        ),
    )


class DrawnCard(BaseModel):
    """Card as drawn with orientation and position in spread."""

    card: Card = Field(..., description="The card object from deck")
    reversed: bool = Field(..., description="True if drawn reversed, False if upright")
    position: int = Field(..., description="Position in spread (0-indexed)")
    position_meaning: str = Field(
        default="",
        description=(
            "Position significance in spread (e.g. 'Past', 'Present', 'Future'). "
            "Assigned by spread layout during reading creation."
        ),
    )

    @property
    def effective_meaning(self) -> str:
        """
        Returns appropriate meaning based on orientation.

        Foundation note: Property ensures you always get correct meaning
        for card's current orientation without manual if/else checks.
        """
        return (
            self.card.reversed_meaning if self.reversed else self.card.upright_meaning
        )


class Reading(BaseModel):
    """Complete reading with cards and optional interpretation."""

    spread_type: str = Field(..., description="Name of spread used")
    focus_area: FocusArea = Field(..., description="Reading focus")
    question: str | None = Field(None, description="User's specific question")
    cards: list[DrawnCard] = Field(..., description="Cards drawn in order")
    interpretation: str | None = Field(None, description="AI-generated interpretation")
    baseline_interpretation: str = Field(
        ..., description="Non-AI fallback interpretation"
    )
    timestamp: str = Field(..., description="ISO 8601 timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "spread_type": "three_card",
                "focus_area": "career",
                "question": "Should I pursue freelance work?",
                "interpretation": "Based on the three cards...",
                "timestamp": "2025-11-04T14:30:00Z",
            }
        }
    )
