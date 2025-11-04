import os
import asyncio
from litellm import acompletion
from tarotcli.models import Reading, FocusArea

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
    reading: Reading, model: str = "claude-sonnet-4-20250514", timeout: int = 30
) -> str:
    """
    Generate AI interpretation for a reading using Claude API.

    Sends reading context (cards, positions, focus, question) to Claude API
    and receives synthesized interpretation. Falls back to baseline interpretation
    if API unavailable or errors occur.

    This function implements graceful degradation: the reading is always usable
    even without AI enhancement. The LLM adds synthesis and contextual insight
    but is not required for core functionality.

    Args:
        reading: Complete reading object with drawn cards
        model: LiteLLM model identifier (default: Claude Sonnet 4)
        timeout: API request timeout in seconds

    Returns:
        AI-generated interpretation or baseline if API fails

    Example:
        >>> reading = spread.create_reading(cards, FocusArea.CAREER)
        >>> interpretation = await interpret_reading(reading)
        >>> reading.interpretation = interpretation

    Note:
        Requires ANTHROPIC_API_KEY environment variable. If not set,
        immediately returns baseline interpretation without API call.

    Environmental Requirements:
        - ANTHROPIC_API_KEY: Anthropic API key for Claude access

    Error Handling:
        All exceptions caught and logged. Function never raises, ensuring
        readings always complete successfully (core principle: reliability
        over feature completeness).
    """
    # Check for API key before attempting call
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("No ANTHROPIC_API_KEY found, using baseline interpretation")
        return reading.baseline_interpretation

    try:
        prompt = _build_interpretation_prompt(reading)

        response = await acompletion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            timeout=timeout,
            temperature=0.7,  # Balanced creativity/consistency
            stream=False,  # Disable streaming for synchronous response
        )

        # Extract content from response, with fallback to baseline
        # type: ignore - LiteLLM doesn't properly type streaming vs non-streaming responses
        interpretation = response.choices[0].message.content  # type: ignore[union-attr]
        if interpretation is None:
            return reading.baseline_interpretation

        return interpretation

    except asyncio.TimeoutError:
        print(f"API timeout after {timeout}s, using baseline interpretation")
        return reading.baseline_interpretation

    except Exception as e:
        print(f"API error ({type(e).__name__}), using baseline interpretation")
        return reading.baseline_interpretation


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

        cards_section.append(
            f"**{card.position_meaning}**: {card.card.name} ({orientation})\n"
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
            "2. Synthesizes the cards' positions and traditional meanings",
            "3. Offers practical, grounded insight",
            "4. Maintains respect for traditional tarot symbolism",
            "5. Avoids overly mystical or vague language",
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
