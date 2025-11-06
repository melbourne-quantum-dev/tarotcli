#!/usr/bin/env python
"""AI interpretation demonstration: reading → Claude API → synthesis.

Validates Milestone 3 functionality with configuration system:
- Config-driven model provider selection
- Claude API integration via LiteLLM
- Waite imagery descriptions in prompt
- Graceful degradation to baseline
- Complete AI interpretation flow

Requires: ANTHROPIC_API_KEY in .env file or environment variable
"""

from tarotcli.deck import TarotDeck
from tarotcli.spreads import get_spread
from tarotcli.models import FocusArea
from tarotcli.ai import interpret_reading_sync
from tarotcli.config import get_config


def test_ai_interpretation():
    """Demonstrate AI interpretation with authentic Waite symbolism."""

    # Show configuration
    config = get_config()
    provider = config.get("models.default_provider")
    model_config = config.get_model_config()

    print(f"📋 Configuration:")
    print(f"   Provider: {provider}")
    print(f"   Model: {model_config.get('model')}")
    print(f"   Temperature: {model_config.get('temperature')}")
    print(f"   Max tokens: {model_config.get('max_tokens')}")

    # Check for API key via config system
    api_key = config.get_api_key(provider)
    if not api_key and provider != "ollama":
        print(f"\n❌ No API key found for provider '{provider}'")
        print("   Add to .env file: ANTHROPIC_API_KEY=sk-ant-...")
        print("   Will use baseline interpretation only\n")
    else:
        status = "✅" if api_key else "🔧"
        key_msg = "API key found" if api_key else "Local inference (no key needed)"
        print(f"{status} {key_msg}\n")

    # Load and shuffle deck using convenience method
    deck = TarotDeck.load_default()
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
        question="Should I pursue a new job opportunity in the tech industry?",
    )
    print(f"✅ Generated reading with baseline interpretation")

    # Optional: Show actual prompt sent to AI (debug mode)
    debug_mode = config.get("DEBUG_PROMPT", False) or config.get(
        "debug.show_prompt", False
    )
    if debug_mode:
        from tarotcli.ai import _build_interpretation_prompt

        print("\n" + "=" * 70)
        print("DEBUG: ACTUAL PROMPT SENT TO AI")
        print("=" * 70)
        prompt = _build_interpretation_prompt(reading)
        print(prompt)
        print("=" * 70)
        print(f"Prompt length: {len(prompt)} characters\n")

    # Add AI interpretation (or fallback to baseline)
    print(f"\n🤖 Calling {provider} API for interpretation...")
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
        print("\n✅ AI interpretation differs from baseline (API call succeeded)")
    else:
        print(reading.interpretation)
        print("\n⚠️  AI interpretation same as baseline (graceful degradation)")

    print("=" * 70)


if __name__ == "__main__":
    test_ai_interpretation()
