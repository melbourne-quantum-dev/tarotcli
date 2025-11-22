"""Interactive user interface for tarot reading parameter collection.

Provides questionary-based prompts for interactive mode when tarotcli is run
without CLI arguments. Handles spread type selection, focus area choice,
and optional question input. Also includes formatted reading display functions
for terminal output using Rich for proper text wrapping and styling.

Main Functions:
- prompt_spread_selection(): Choose from available spreads
- prompt_focus_area(): Select reading focus area
- prompt_question(): Optional specific question
- prompt_use_ai_interpretation(): Choose AI vs static interpretation
- gather_reading_inputs(): Complete interactive flow
- display_reading(): Formatted terminal output with Rich

All interactive functions include progress indicators, help text, and
appropriate default values for smooth user experience.
"""

import sys
import questionary
from typing import Tuple, Optional
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.theme import Theme
from rich.align import Align

# Mystical theme for tarot reading
mystical_theme = Theme(
    {
        "markdown.h1": "bold #AF00FF",  # Deep Purple
        "markdown.h2": "bold #A8B5BF",  # Tundra (replaced cyan)
        "markdown.h3": "bold #FFD700",  # Gold
        "markdown.strong": "bold #FFD700",  # Gold for emphasis
        "panel.border": "#AF00FF",  # Deep Purple borders
        "box.border": "#A8B5BF",  # Tundra box borders
        "table.header": "bold #FFD700",  # Gold table headers
        "tundra": "#A8B5BF",  # Tundra metallic grey
    }
)
from tarotcli.config import get_config
from tarotcli.models import FocusArea, Reading
from tarotcli.spreads import SPREADS
from rich import box

# Rich console for formatted output with custom theme
console = Console(theme=mystical_theme)


def _is_terminal() -> bool:
    """Check if stdout is connected to a terminal (TTY)."""
    return sys.stdout.isatty()


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

    return question.strip() if question else None


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


def prompt_show_imagery() -> bool:
    """
    Ask if user wants to include Waite's imagery descriptions.

    Only prompts if config doesn't have a preference set.

    Returns:
        True to show imagery, False otherwise.
    """
    return questionary.confirm(
        "Include Waite's imagery descriptions?", default=False
    ).ask()


def prompt_show_static() -> bool:
    """
    Ask if user wants to show card meanings alongside AI interpretation.

    Only prompts if config doesn't have a preference set.

    Returns:
        True to show static meanings in table column, False otherwise.
    """
    return questionary.confirm("Show card meanings in table?", default=True).ask()


def gather_reading_inputs() -> Optional[
    Tuple[str, FocusArea, Optional[str], bool, bool, bool]
]:
    """
    Complete interactive flow to gather all reading parameters.

    Guides user through all prompts in sequence, returns all selections.
    Returns None if user cancels at any required prompt.

    Returns:
        Tuple of (spread_name, focus_area, question, use_ai, show_imagery, show_static)
        or None if user cancelled.

    Example:
        >>> result = gather_reading_inputs()
        >>> if result:
        ...     spread, focus, question, use_ai, show_imagery, show_static = result
    """
    console.print()
    console.rule(
        "[bold #AF00FF]🔮 TarotCLI - Interactive Reading[/bold #AF00FF]",
        style="#AF00FF",
    )
    console.print()

    spread_name = prompt_spread_selection()
    if spread_name is None:
        return None  # User cancelled

    focus_area = prompt_focus_area()
    if focus_area is None:
        return None  # User cancelled

    question = prompt_question()
    # question can be None (skipped), that's fine

    use_ai = prompt_use_ai_interpretation()
    if use_ai is None:
        return None  # User cancelled

    # Check if config has display preferences, else prompt
    config = get_config()

    if config.get("display.show_imagery") is not None:
        show_imagery = config.get("display.show_imagery", False)
    else:
        show_imagery = prompt_show_imagery()
        if show_imagery is None:
            return None  # User cancelled

    if config.get("display.show_static") is not None:
        show_static = config.get("display.show_static", True)
    else:
        show_static = prompt_show_static()
        if show_static is None:
            return None  # User cancelled

    return spread_name, focus_area, question, use_ai, show_imagery, show_static


def _display_reading_plain(
    reading: Reading, show_static: bool = False, show_imagery: bool = False
) -> None:
    """Plain text output for file redirection (non-TTY)."""
    title = (
        f"{reading.spread_type.replace('_', ' ').title()} - "
        f"{reading.focus_area.value.replace('_', ' ').title()}"
    )
    print(f"\n# {title}\n")

    if reading.question:
        print(f"**Question:** {reading.question}\n")

    print("## Cards Drawn\n")
    for card in reading.cards:
        orientation = "Reversed" if card.reversed else "Upright"
        print(f"- **{card.position_meaning}:** {card.card.name} ({orientation})")

    if show_imagery:
        print("\n## Imagery (Waite 1911)\n")
        for card in reading.cards:
            print(f"### {card.card.name}\n")
            print(f"{card.card.description}\n")

    print("\n## Interpretation\n")
    if reading.interpretation:
        print(reading.interpretation)
        if show_static:
            print("\n## Static Interpretation\n")
            print(reading.static_interpretation)
    else:
        print(reading.static_interpretation)


def _display_reading_rich(
    reading: Reading, show_static: bool = False, show_imagery: bool = False
) -> None:
    """Rich formatted output for terminal display."""
    title = (
        f"{reading.spread_type.replace('_', ' ').title()} - "
        f"{reading.focus_area.value.replace('_', ' ').title()}"
    )
    console.print()
    console.rule(f"[bold #AF00FF]🔮 {title} 🔮[/bold #AF00FF]", style="#AF00FF")
    console.print()

    if reading.question:
        console.print(
            Align.center(
                Panel(
                    f'[italic #A8B5BF]"{reading.question}"[/italic #A8B5BF]',  # Tundra italics
                    title="[bold white]❔ Your Question ❔[/bold white]",
                    border_style="#A8B5BF",  # Tundra border
                    box=box.DOUBLE,  # Elegant double-line border
                    padding=(1, 4),  # More spacious padding
                    expand=False,
                )
            )
        )
        console.print()

    # Cards Table
    # Add Meaning column when showing static interpretation (no AI or show_static=True)
    # Add Imagery column when show_imagery=True
    show_meaning_column = reading.interpretation is None or show_static

    table = Table(
        show_header=True,
        box=box.SIMPLE_HEAVY,  # Grid lines for better row separation
        padding=(1, 1),  # Vertical and horizontal padding (must be integers)
        header_style="bold #FFD700",
        border_style="#A8B5BF",  # Tundra - neutral structural element
        title="[bold white]Cards Drawn[/bold white]",
        title_style="bold white",
    )
    table.add_column("Position", style="tundra", justify="center")
    table.add_column("Card", style="bold white", justify="center")
    table.add_column("Orientation", justify="center")

    if show_meaning_column:
        table.add_column("Meaning (Waite 1911)", justify="full", no_wrap=False)

    if show_imagery:
        table.add_column(
            "Imagery (Waite 1911)", justify="full", no_wrap=False, style="#A8B5BF"
        )

    for card in reading.cards:
        orientation = (
            "[bold red]↓ Reversed[/bold red]"
            if card.reversed
            else "[bold green]↑ Upright[/bold green]"
        )

        # Build row based on which columns are enabled
        row_data = [card.position_meaning, card.card.name, orientation]

        if show_meaning_column:
            # Color-code meaning to match orientation (green for upright, red for reversed)
            meaning_color = "red" if card.reversed else "green"
            meaning_text = (
                f"[{meaning_color}]{card.effective_meaning}[/{meaning_color}]"
            )
            row_data.append(meaning_text)

        if show_imagery:
            row_data.append(card.card.description)

        table.add_row(*row_data)

    console.print(table, justify="center")
    console.print()

    # Interpretation Panel
    # Only show if AI interpretation exists (meanings already in table for static mode)
    if reading.interpretation:
        # console.rule("[bold #4682B4]Interpretation[/bold #4682B4]", style="#4682B4")
        # console.print()
        console.print(
            Panel(
                Markdown(reading.interpretation),
                title="[bold #AF00FF]🔮 AI Narrative Interpretation[/bold #AF00FF]",
                border_style="#AF00FF",
                padding=(1, 2),
            )
        )
        # Note: show_static parameter no longer shows redundant panel
        # Meanings appear in table's 4th column when show_static=True

    console.print()
    console.rule(style="#AF00FF")


def display_reading(
    reading: Reading, show_static: bool = False, show_imagery: bool = False
) -> None:
    """Display reading results, using Rich for terminal or plain text for files.

    Automatically detects if output is to a terminal (TTY) and uses Rich
    formatting with colors and panels. When redirected to a file, outputs
    clean markdown suitable for documentation.

    Args:
        reading: Complete reading object with cards and interpretations.
        show_static: If True, show static interpretation even when AI present.
        show_imagery: If True, include Waite's 1911 imagery descriptions.

    Returns:
        None. Prints formatted reading to stdout.
    """
    if _is_terminal():
        _display_reading_rich(reading, show_static, show_imagery)
    else:
        _display_reading_plain(reading, show_static, show_imagery)
