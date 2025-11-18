import asyncio
from typing import Optional
from litellm import acompletion
from tarotcli.models import Reading, FocusArea
from tarotcli.config import get_config

# Focus area context templates
FOCUS_CONTEXTS = {
    FocusArea.CAREER: (
        "This reading relates to professional development, career decisions, "
        "work situations, and vocational path. Provide practical guidance "
        "for professional growth and decision-making."
    ),
    FocusArea.RELATIONSHIPS: (
        "This reading relates to interpersonal connections, romantic partnerships, "
        "friendships, and social dynamics. Offer insight into relationship patterns "
        "and emotional connections."
    ),
    FocusArea.PERSONAL_GROWTH: (
        "This reading relates to self-development, inner work, personal transformation, "
        "and spiritual evolution. Focus on insights for personal development and "
        "self-understanding."
    ),
    FocusArea.SPIRITUAL: (
        "This reading relates to spiritual practices, consciousness exploration, "
        "higher purpose, and metaphysical understanding. Provide guidance for "
        "spiritual development."
    ),
    FocusArea.GENERAL: (
        "This reading provides general life guidance across multiple areas. "
        "Offer holistic perspective on the querent's current situation."
    ),
}


async def interpret_reading(
    reading: Reading, provider: Optional[str] = None, timeout: int = 30
) -> str:
    """Generate AI interpretation of tarot reading with graceful degradation.

    Integrates with LiteLLM to support multiple model providers (Claude, Ollama).
    Configuration-driven: Provider settings (model, temperature, etc.) come from
    config system, not hardcoded values.

    Graceful degradation: ALWAYS returns valid interpretation. On any error
    (missing API key, timeout, API failure), falls back to reading.static_interpretation.
    This ensures readings never fail.

    Provider resolution: If no provider specified, uses configured default from
    config.get("models.default_provider"). Allows switching providers by changing
    one config value.

    Args:
        reading: Complete reading with cards, spread type, focus area.
        provider: Model provider name (claude, ollama). If None, uses config default.
        timeout: API call timeout in seconds. Default 30s.

    Returns:
        str: AI-generated interpretation or static interpretation on error.
             NEVER raises exceptions - always returns valid text.

    Example:
        >>> reading = perform_reading(deck, "three_card", FocusArea.CAREER)
        >>> interpretation = await interpret_reading(reading, provider="claude")

        >>> # With default provider from config
        >>> interpretation = await interpret_reading(reading)

    Why async:
        Future-proofed for web API integration. Current CLI usage wraps with
        interpret_reading_sync(). Over-engineered for v1.0 but architecturally
        sound for planned web trajectory.
    """
    config = get_config()

    # Resolve provider to concrete name (handles None → default from config)
    resolved_provider = (
        provider
        if provider is not None
        else config.get("models.default_provider", "claude")
    )

    # Get model config (includes model, temperature, max_tokens, api_base)
    model_config = config.get_model_config(resolved_provider)
    api_key = config.get_api_key(resolved_provider)

    # Check API key requirement (Ollama doesn't need one, others do)
    if not api_key and resolved_provider != "ollama":
        print(
            f"❌ No API key found for provider '{resolved_provider}', using static interpretation"
        )
        return reading.static_interpretation

    try:
        prompt = _build_interpretation_prompt(reading)

        response = await acompletion(
            model=model_config["model"],  # From config
            messages=[{"role": "user", "content": prompt}],
            timeout=timeout,
            temperature=model_config.get("temperature", 0.7),
            max_tokens=model_config.get("max_tokens", 2000),  # From config
            api_base=model_config.get("api_base"),  # From config
            stream=False,  # Disable streaming for synchronous response
        )

        # Extract content from response, with fallback to baseline
        # type: ignore - LiteLLM doesn't properly type streaming vs non-streaming responses
        interpretation = response.choices[0].message.content  # type: ignore[union-attr]
        if interpretation is None:
            return reading.static_interpretation

        return interpretation

    except asyncio.TimeoutError:
        print(f"API timeout after {timeout}s, using static interpretation")
        return reading.static_interpretation

    except Exception as e:
        print(f"API error ({type(e).__name__}), using static interpretation")
        return reading.static_interpretation


def _build_interpretation_prompt(reading: Reading) -> str:
    """
    Construct prompt for Claude API with full reading context.

    Builds structured prompt including:
    - Focus area framing
    - User's specific question (if provided)
    - All drawn cards with positions and meanings
    - Interpretation guidelines

    Args:
        reading: Complete reading to interpret

    Returns:
        Formatted prompt string for LLM

    Note:
        This is internal implementation. Prompt engineering kept simple
        for v1.0 - avoid over-engineering with complex prompt templates.
    """
    focus_context = FOCUS_CONTEXTS[reading.focus_area]

    # Build cards section
    cards_section = []
    for card in reading.cards:
        orientation = "Reversed" if card.reversed else "Upright"
        meaning = card.effective_meaning
        imagery = card.card.description

        cards_section.append(
            f"**{card.position_meaning}**: {card.card.name} ({orientation})\n"
            f"Imagery: {imagery}\n"
            f"Traditional Meaning: {meaning}\n"
        )

    cards_text = "\n".join(cards_section)

    # Build full prompt
    prompt_parts = [
        "Provide a tarot reading interpretation for the following spread.\n",
        f"**Spread Type**: {reading.spread_type.replace('_', ' ').title()}",
        f"**Focus Area**: {focus_context}\n",
    ]

    if reading.question:
        prompt_parts.append(f"**Querent's Question**: {reading.question}\n")

    prompt_parts.extend(
        [
            "**Cards Drawn**:",
            cards_text,
            "\nPlease provide a cohesive interpretation that:",
            "1. Addresses the focus area and question (if provided)",
            "2. Integrates the cards' positions and traditional meanings",
            "3. References specific symbolic elements from the imagery descriptions",
            "   (serpents, robes, objects, colors, positioning)",
            "4. Offers practical, grounded insight for the querent's situation",
            "5. Maintains respect for traditional tarot symbolism",
            "\nKeep the interpretation concise (200-300 words) and actionable.",
        ]
    )

    return "\n".join(prompt_parts)


def interpret_reading_sync(reading: Reading, **kwargs) -> str:
    """
    Synchronous wrapper for interpret_reading().

    Convenience function for non-async contexts. Creates event loop,
    runs async interpret_reading(), returns result.

    Args:
        reading: Reading to interpret
        **kwargs: Passed to interpret_reading()

    Returns:
        Interpretation string

    Example:
        >>> interpretation = interpret_reading_sync(reading)
    """
    return asyncio.run(interpret_reading(reading, **kwargs))
