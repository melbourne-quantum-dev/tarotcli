"""Spread layouts and position meanings.

This module defines tarot spread templates (number of cards, position meanings)
and creates readings with baseline interpretation (no AI).
"""

from dataclasses import dataclass
from typing import List
from tarotcli.models import DrawnCard, Reading, FocusArea
from datetime import datetime, timezone


@dataclass
class SpreadLayout:
    """Template for a tarot spread defining positions and their meanings."""
    name: str
    display_name: str
    positions: List[str]
    description: str
    
    def card_count(self) -> int:
        """Return number of cards needed for this spread."""
        return len(self.positions)
    
    def create_reading(
        self,
        cards: List[DrawnCard],
        focus_area: FocusArea,
        question: str | None = None
    ) -> Reading:
        """
        Create a Reading from drawn cards by assigning position meanings.
        
        Takes raw drawn cards and enriches them with position context from
        this spread layout. Generates baseline interpretation (no LLM).
        
        Args:
            cards: Drawn cards from deck (must match position count)
            focus_area: Reading focus for context
            question: Optional specific question from user
            
        Returns:
            Complete Reading object with positioned cards and baseline interpretation
            
        Raises:
            ValueError: If card count doesn't match spread position count
        """
        if len(cards) != len(self.positions):
            raise ValueError(
                f"Spread '{self.name}' requires {len(self.positions)} cards, "
                f"got {len(cards)}"
            )
        
        # Assign position meanings to drawn cards
        for card, position_name in zip(cards, self.positions):
            card.position_meaning = position_name
        
        # Generate baseline interpretation (non-LLM)
        baseline = self._generate_baseline(cards, focus_area, question)
        
        return Reading(
            spread_type=self.name,
            focus_area=focus_area,
            question=question,
            cards=cards,
            interpretation=None,  # AI interpretation added in Milestone 3
            baseline_interpretation=baseline,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    def _generate_baseline(
        self,
        cards: List[DrawnCard],
        focus_area: FocusArea,
        question: str | None
    ) -> str:
        """
        Generate non-LLM interpretation from card meanings.
        
        Provides fallback interpretation when LLM unavailable. Simply presents
        each card's position and traditional meaning from dataset.
        
        Foundation note: This ensures readings ALWAYS complete successfully,
        regardless of API availability. Built to degrade gracefully.
        """
        parts = [f"# {self.display_name}"]
        
        if question:
            parts.append(f"\n**Question**: {question}")
        
        parts.append(f"**Focus**: {focus_area.value.replace('_', ' ').title()}")
        parts.append("")
        
        for card in cards:
            orientation = "Reversed" if card.reversed else "Upright"
            parts.append(
                f"## {card.position_meaning}: {card.card.name} ({orientation})\n"
                f"{card.effective_meaning}"
            )
        
        return "\n".join(parts)


# Spread definitions
SINGLE_CARD = SpreadLayout(
    name="single_card",
    display_name="Single Card",
    positions=["Present"],
    description="One card for immediate guidance or daily draw"
)

THREE_CARD = SpreadLayout(
    name="three_card",
    display_name="Three Card Spread",
    positions=["Past", "Present", "Future"],
    description="Classic three-card timeline spread"
)

CELTIC_CROSS = SpreadLayout(
    name="celtic_cross",
    display_name="Celtic Cross",
    positions=[
        "Present Situation",
        "Challenge/Crossing",
        "Distant Past/Foundation",
        "Recent Past",
        "Possible Future",
        "Near Future",
        "Self Perception",
        "External Influences",
        "Hopes and Fears",
        "Outcome"
    ],
    description="Comprehensive 10-card spread for deep inquiry"
)

# Registry of available spreads
SPREADS = {
    "single": SINGLE_CARD,
    "three": THREE_CARD,
    "celtic": CELTIC_CROSS
}


def get_spread(name: str) -> SpreadLayout:
    """
    Retrieve spread layout by name.
    
    Args:
        name: Spread identifier (e.g. "three", "celtic")
        
    Returns:
        SpreadLayout for the requested spread
        
    Raises:
        ValueError: If spread name not recognized
    """
    if name not in SPREADS:
        available = ", ".join(SPREADS.keys())
        raise ValueError(
            f"Unknown spread '{name}'. Available: {available}"
        )
    return SPREADS[name]