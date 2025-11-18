"""Interactive user interface for tarot reading parameter collection.

Provides questionary-based prompts for interactive mode when tarotcli is run
without CLI arguments. Handles spread type selection, focus area choice,
and optional question input. Also includes formatted reading display functions
for terminal output.

Main Functions:
- prompt_spread_selection(): Choose from available spreads
- prompt_focus_area(): Select reading focus area
- prompt_question(): Optional specific question
- prompt_use_ai_interpretation(): Choose AI vs static interpretation
- gather_reading_inputs(): Complete interactive flow
- display_reading(): Formatted terminal output

All interactive functions include progress indicators, help text, and
appropriate default values for smooth user experience.
"""

import questionary
from typing import Tuple, Optional
from tarotcli.config import get_config
from tarotcli.models import FocusArea, Reading
from tarotcli.spreads import SPREADS


def prompt_spread_selection() -> str:
    """
    Interactive prompt for spread type selection.

    Displays list of available spreads with descriptions, returns selected
    spread identifier.

    Returns:
        Spread name (e.g. "three", "celtic")

    Example:
        >>> spread_name = prompt_spread_selection()
        ┌─ Select Spread Type ───────────────────┐
        │ › Three Card Spread                    │
        │   Celtic Cross                         │
        │   Single Card                          │
        └────────────────────────────────────────┘
    """
    choices = [
        {"name": f"{spread.display_name} - {spread.description}", "value": name}
        for name, spread in SPREADS.items()
    ]

    return questionary.select("Select spread type:", choices=choices).ask()


def prompt_focus_area() -> FocusArea:
    """
    Interactive prompt for reading focus area.

    Returns:
        FocusArea enum value

    Example:
        >>> focus = prompt_focus_area()
        ┌─ Reading Focus ────────────────────────┐
        │ › Career                               │
        │   Relationships                        │
        │   Personal Growth                      │
        │   Spiritual                            │
        │   General Guidance                     │
        └────────────────────────────────────────┘
    """
    choices = [
        {"name": focus.value.replace("_", " ").title(), "value": focus}
        for focus in FocusArea
    ]

    return questionary.select(
        "What is the focus of this reading?", choices=choices
    ).ask()


def prompt_question() -> Optional[str]:
    """
    Interactive prompt for specific question (optional).

    Returns:
        User's question string, or None if skipped

    Example:
        >>> question = prompt_question()
        Specific question (press Enter to skip): Should I change jobs?
    """
    question = questionary.text(
        "Specific question (press Enter to skip):", default=""
    ).ask()

    return question if question.strip() else None


def prompt_use_ai_interpretation() -> bool:
    """
    Ask if user wants AI interpretation using configured provider.

    Checks config to show which provider will be used.

    Returns:
        True if user wants AI interpretation, False for static only
    """

    config = get_config()
    provider = config.get("models.default_provider", "claude")

    return questionary.confirm(
        f"Use AI interpretation? (provider: {provider})", default=True
    ).ask()


def gather_reading_inputs() -> Tuple[str, FocusArea, Optional[str], bool]:
    """
    Complete interactive flow to gather all reading parameters.

    Guides user through all prompts in sequence, returns all selections.

    Returns:
        Tuple of (spread_name, focus_area, question, use_ai)

    Example:
        >>> spread, focus, question, use_ai = gather_reading_inputs()
        >>> # User has selected all parameters, ready to perform reading
    """
    print("\n🔮 TarotCLI - Interactive Reading\n")

    spread_name = prompt_spread_selection()
    focus_area = prompt_focus_area()
    question = prompt_question()
    use_ai = prompt_use_ai_interpretation()

    return spread_name, focus_area, question, use_ai


def display_reading(reading: Reading, show_static: bool = False) -> None:
    # sourcery skip: extract-duplicate-method
    """Pretty-print reading results to console.

    Displays cards drawn, positions, and interpretation using ASCII formatting.
    Shows AI interpretation if available, otherwise displays static interpretation.

    Args:
        reading: Complete reading object with cards and interpretations.
        show_static: If True, show static interpretation even when AI interpretation present.

    Returns:
        None. Prints formatted reading to stdout.

    Example:
        >>> display_reading(reading)

        ═══════════════════════════════════════════
        Three Card Spread - Career
        ═══════════════════════════════════════════

        Past: The Magician (Upright)
        Present: Seven of Swords (Reversed)
        Future: Knight of Wands (Upright)

        ───────────────────────────────────────────
        INTERPRETATION
        ───────────────────────────────────────────
        [AI interpretation here]
    """
    print("\n" + "═" * 50)
    print(
        f"{reading.spread_type.replace('_', ' ').title()} - "
        f"{reading.focus_area.value.replace('_', ' ').title()}"
    )
    print("═" * 50)

    if reading.question:
        print(f"\n❓ Question: {reading.question}\n")

    print("Cards Drawn:\n")
    for card in reading.cards:
        orientation = "↓ Reversed" if card.reversed else "↑ Upright"
        print(f"  {card.position_meaning}: {card.card.name} {orientation}")

    print("\n" + "─" * 50)
    print("INTERPRETATION")
    print("─" * 50 + "\n")

    if reading.interpretation:
        print(reading.interpretation)
        if show_static:
            print("\n" + "─" * 50)
            print("STATIC INTERPRETATION")
            print("─" * 50 + "\n")
            print(reading.static_interpretation)
    else:
        print(reading.static_interpretation)

    print("\n" + "═" * 50 + "\n")
