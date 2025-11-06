#!/usr/bin/env python
"""AI interpretation comparison: Claude (cloud) vs Ollama (local).

Demonstrates provider-agnostic architecture by sending identical reading
to both cloud (Claude) and local (Ollama) providers for side-by-side comparison.

This validates that the configuration system and interpret_reading() function
work seamlessly with different LLM backends without code changes.

Requirements:
- Claude: ANTHROPIC_API_KEY in environment
- Ollama: Local server running (ollama serve) with model pulled

Usage:
    python test_ai_cloud_vs_local.py

Environment:
    ANTHROPIC_API_KEY=sk-ant-...  # For Claude
    # Ollama: No API key needed, runs locally
"""

from tarotcli.ai import interpret_reading_sync
from tarotcli.config import get_config
from tarotcli.deck import TarotDeck
from tarotcli.models import FocusArea
from tarotcli.spreads import get_spread


def test_cloud_vs_local_comparison():
    """Compare Claude (cloud) vs Ollama (local) interpretations."""

    config = get_config()

    print("=" * 70)
    print("AI INTERPRETATION COMPARISON: CLOUD vs LOCAL")
    print("=" * 70)

    # Check provider configurations
    print("\n📋 Provider Configurations:")

    # Claude
    claude_config = config.get_model_config("claude")
    claude_key = config.get_api_key("claude")
    print(f"\n  [Claude - Cloud]")
    print(f"    Model: {claude_config.get('model')}")
    print(f"    Temperature: {claude_config.get('temperature')}")
    print(f"    Max tokens: {claude_config.get('max_tokens')}")
    print(
        f"    API key: {'✅ Found' if claude_key else '❌ Missing (set ANTHROPIC_API_KEY)'}"
    )

    # Ollama
    ollama_config = config.get_model_config("ollama")
    print(f"\n  [Ollama - Local]")
    print(f"    Model: {ollama_config.get('model')}")
    print(f"    API base: {ollama_config.get('api_base')}")
    print(f"    Temperature: {ollama_config.get('temperature')}")
    print(f"    Max tokens: {ollama_config.get('max_tokens')}")
    print(
        f"    Status: {'✅ No API key needed (local inference)' if not config.get_api_key('ollama') else '⚠️  Unexpected API key'}"
    )

    # Create deterministic reading (fixed seed for reproducibility)
    print("\n" + "=" * 70)
    print("CREATING READING (Fixed seed for reproducibility)")
    print("=" * 70)

    deck = TarotDeck.load_default()
    deck.shuffle(seed=42)  # Fixed seed ensures same cards every run
    print(f"✅ Loaded and shuffled {len(deck.cards)} cards (seed=42)")

    # Use three-card spread for quick comparison
    spread = get_spread("three")
    print(f"✅ Using {spread.display_name} ({spread.card_count()} cards)")

    # Draw cards
    drawn = deck.draw(spread.card_count())
    print(f"✅ Drew {len(drawn)} cards:")
    for card in drawn:
        orientation = "↓ Reversed" if card.reversed else "↑ Upright"
        print(f"   {card.position_meaning}: {card.card.name} {orientation}")

    # Create reading
    reading = spread.create_reading(
        cards=drawn,
        focus_area=FocusArea.CAREER,
        question="Should I pursue a new job opportunity in the tech industry?",
    )
    print("✅ Generated reading")

    # Show cards and baseline
    print("\n" + "=" * 70)
    print("CARDS DRAWN (Shared input for both providers)")
    print("=" * 70)
    for card in reading.cards:
        orientation = "Reversed" if card.reversed else "Upright"
        print(f"\n{card.position_meaning}: {card.card.name} ({orientation})")
        print(f"Meaning: {card.effective_meaning[:120]}...")

    print("\n" + "=" * 70)
    print("BASELINE INTERPRETATION (No AI)")
    print("=" * 70)
    print(reading.baseline_interpretation)

    # Get Claude interpretation
    print("\n" + "=" * 70)
    print("CLAUDE INTERPRETATION (Cloud)")
    print("=" * 70)
    print("🤖 Calling Claude API...")

    claude_interpretation = interpret_reading_sync(reading, provider="claude")

    if claude_interpretation == reading.baseline_interpretation:
        print("\n⚠️  Claude API call failed (graceful degradation to baseline)")
        print("   Check: ANTHROPIC_API_KEY environment variable")
    else:
        print("\n✅ Claude interpretation:")

    print("\n" + claude_interpretation)

    # Get Ollama interpretation
    print("\n" + "=" * 70)
    print("OLLAMA INTERPRETATION (Local)")
    print("=" * 70)
    print("🤖 Calling Ollama local server...")

    ollama_interpretation = interpret_reading_sync(reading, provider="ollama")

    if ollama_interpretation == reading.baseline_interpretation:
        print("\n⚠️  Ollama API call failed (graceful degradation to baseline)")
        print("   Check: 1) ollama serve is running")
        print("          2) Model is pulled: ollama pull deepseek-r1:8b")
        print("          3) config.yaml has correct ollama configuration")
    else:
        print("\n✅ Ollama interpretation:")

    print("\n" + ollama_interpretation)

    # Summary comparison
    print("\n" + "=" * 70)
    print("COMPARISON SUMMARY")
    print("=" * 70)

    claude_worked = claude_interpretation != reading.baseline_interpretation
    ollama_worked = ollama_interpretation != reading.baseline_interpretation

    print(
        f"\nClaude (cloud):  {'✅ Success' if claude_worked else '❌ Failed (used baseline)'}"
    )
    print(
        f"Ollama (local):  {'✅ Success' if ollama_worked else '❌ Failed (used baseline)'}"
    )

    if claude_worked and ollama_worked:
        print("\n✨ Both providers working! Compare interpretations above.")
        print("   Note: Interpretations will differ due to different models/training.")
    elif not claude_worked and not ollama_worked:
        print("\n⚠️  Both providers failed. Check configurations above.")
    else:
        working = "Claude" if claude_worked else "Ollama"
        print(f"\n✅ {working} working, but not the other. See checks above.")

    print("=" * 70)


if __name__ == "__main__":
    test_cloud_vs_local_comparison()
