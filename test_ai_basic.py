#!/usr/bin/env python
"""AI interpretation demonstration: reading → Claude API → synthesis.

Validates Milestone 3 functionality:
- Claude API integration via LiteLLM
- Waite imagery descriptions in prompt
- Graceful degradation to baseline
- Complete AI interpretation flow

Requires: ANTHROPIC_API_KEY environment variable
"""

import os
from pathlib import Path
from tarotcli.deck import TarotDeck
from tarotcli.spreads import get_spread
from tarotcli.models import FocusArea
from tarotcli.ai import interpret_reading_sync


def test_ai_interpretation():
    """Demonstrate AI interpretation with authentic Waite symbolism."""

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY not set - will use baseline only")
        print("   Run: export ANTHROPIC_API_KEY='sk-ant-...'")
        print()
    else:
        print("✅ ANTHROPIC_API_KEY found")

    # Load and shuffle deck
    deck = TarotDeck(Path("data/tarot_cards_RW.jsonl"))
    deck.shuffle()
    print(f"✅ Loaded and shuffled {len(deck.cards)} cards")

    # Get spread layout
    spread = get_spread("three")
    print(f"✅ Using {spread.display_name} ({spread.card_count()} cards)")

    # Draw cards
    drawn = deck.draw(spread.card_count())
    print(f"✅ Drew {len(drawn)} cards:")
    for card in drawn:
        orientation = "↓ Reversed" if card.reversed else "↑ Upright"
        print(f"   {card.position_meaning}: {card.card.name} {orientation}")

    # Create reading with baseline interpretation
    reading = spread.create_reading(
        cards=drawn,
        focus_area=FocusArea.CAREER,
        question="How should I break out of this cycle of unemployment? Should I consider freelancing with my technical skills or pursue a legal career with my law degree?",
    )
    print(f"✅ Generated reading with baseline interpretation")

    # Optional: Show actual prompt sent to AI (debug mode)
    if os.getenv("DEBUG_PROMPT"):
        from tarotcli.ai import _build_interpretation_prompt

        print("\n" + "=" * 70)
        print("DEBUG: ACTUAL PROMPT SENT TO AI")
        print("=" * 70)
        prompt = _build_interpretation_prompt(reading)
        print(prompt)
        print("=" * 70)
        print(f"Prompt length: {len(prompt)} characters\n")

    # Add AI interpretation (or fallback to baseline)
    print("\n🤖 Calling Claude API for interpretation...")
    print("   (Using Waite's 1911 imagery descriptions as context)")
    reading.interpretation = interpret_reading_sync(reading)
    print("✅ AI interpretation complete")

    # Show cards drawn
    print("\n" + "=" * 70)
    print("CARDS DRAWN")
    print("=" * 70)
    for card in reading.cards:
        orientation = "Reversed" if card.reversed else "Upright"
        print(f"\n{card.position_meaning}: {card.card.name} ({orientation})")
        print(f"Effective meaning: {card.effective_meaning[:100]}...")

    # Show baseline interpretation
    print("\n" + "=" * 70)
    print("BASELINE INTERPRETATION (Non-AI)")
    print("=" * 70)
    print(reading.baseline_interpretation)

    # Show AI interpretation
    print("\n" + "=" * 70)
    print("AI INTERPRETATION (Claude + Waite Imagery)")
    print("=" * 70)
    if reading.interpretation != reading.baseline_interpretation:
        print(reading.interpretation)
        print(
            "\n✅ AI interpretation differs from baseline (API call succeeded)"
        )
    else:
        print(reading.interpretation)
        print(
            "\n⚠️  AI interpretation same as baseline (graceful degradation)"
        )

    print("=" * 70)


if __name__ == "__main__":
    test_ai_interpretation()
