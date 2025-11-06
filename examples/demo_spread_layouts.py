#!/usr/bin/env python
"""Demo: Spread layouts (deck → spread → reading → JSON).

Demonstrates Milestone 2 functionality with configuration system:
- Config-driven deck loading
- Spread layouts with position meanings
- Baseline interpretation generation (no AI)
- Complete reading flow
"""

from tarotcli.deck import TarotDeck
from tarotcli.spreads import get_spread
from tarotcli.models import FocusArea
import json


def test_spread_operations():
    """Demonstrate full reading generation with spread layouts."""

    # Load and shuffle deck using config system
    deck = TarotDeck.load_default()
    deck.shuffle()
    print(f"✅ Loaded and shuffled {len(deck.cards)} cards")

    # Get spread layout
    spread = get_spread("three")
    print(f"✅ Using {spread.display_name} ({spread.card_count()} cards)")

    # Draw cards
    drawn = deck.draw(spread.card_count())
    print(f"✅ Drew {len(drawn)} cards")

    # Create reading with baseline interpretation
    reading = spread.create_reading(
        cards=drawn,
        focus_area=FocusArea.CAREER,
        question="Should I pursue freelance work?",
    )
    print(f"✅ Generated reading with baseline interpretation")

    # Output as JSON
    print("\nJSON Output:")
    print(json.dumps(reading.model_dump(), indent=2))

    # Also show formatted baseline interpretation
    print("\n" + "=" * 60)
    print("BASELINE INTERPRETATION")
    print("=" * 60)
    print(reading.baseline_interpretation)
    print("=" * 60)


if __name__ == "__main__":
    test_spread_operations()
