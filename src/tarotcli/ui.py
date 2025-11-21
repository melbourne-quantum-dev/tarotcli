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

# Custom theme for markdown rendering
custom_theme = Theme({
    "markdown.h1": "bold magenta",
    "markdown.h2": "bold cyan",
    "markdown.h3": "bold blue",
    "markdown.strong": "bold magenta",  # **bold** text
})
from tarotcli.config import get_config
from tarotcli.models import FocusArea, Reading
from tarotcli.spreads import SPREADS

# Rich console for formatted output with custom theme
console = Console(theme=custom_theme)


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


def gather_reading_inputs() -> Tuple[str, FocusArea, Optional[str], bool, bool]:
    """
    Complete interactive flow to gather all reading parameters.

    Guides user through all prompts in sequence, returns all selections.

    Returns:
        Tuple of (spread_name, focus_area, question, use_ai, show_imagery)

    Example:
        >>> spread, focus, question, use_ai, show_imagery = gather_reading_inputs()
        >>> # User has selected all parameters, ready to perform reading
    """
    console.print()
    console.rule("[bold magenta]🔮 TarotCLI - Interactive Reading[/bold magenta]", style="magenta")
    console.print()

    spread_name = prompt_spread_selection()
    focus_area = prompt_focus_area()
    question = prompt_question()
    use_ai = prompt_use_ai_interpretation()

    # Check if config has imagery preference, else prompt
    config = get_config()
    if config.get("display.show_imagery") is not None:
        show_imagery = config.get("display.show_imagery", False)
    else:
        show_imagery = prompt_show_imagery()

    return spread_name, focus_area, question, use_ai, show_imagery


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
    console.rule(f"[bold cyan]{title}[/bold cyan]", style="cyan")

    if reading.question:
        console.print(f"\n[bold]❓ Question:[/bold] {reading.question}")

    console.print("\n[bold]Cards Drawn:[/bold]\n")
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Position", style="dim")
    table.add_column("Card")
    table.add_column("Orientation")

    for card in reading.cards:
        orientation = (
            "[red]↓ Reversed[/red]" if card.reversed else "[green]↑ Upright[/green]"
        )
        table.add_row(card.position_meaning + ":", card.card.name, orientation)

    console.print(table)

    if show_imagery:
        console.print()
        console.rule("[bold yellow]Imagery (Waite 1911)[/bold yellow]", style="yellow")
        for card in reading.cards:
            console.print(
                Panel(
                    card.card.description,
                    title=f"[bold]{card.card.name}[/bold]",
                    border_style="yellow",
                )
            )

    console.print()
    console.rule("[bold green]Interpretation[/bold green]", style="green")
    console.print()

    if reading.interpretation:
        console.print(Markdown(reading.interpretation))
        if show_static:
            console.print()
            console.rule(
                "[bold dim]Static Interpretation[/bold dim]", style="dim"
            )
            console.print()
            console.print(Markdown(reading.static_interpretation))
    else:
        console.print(Markdown(reading.static_interpretation))

    console.print()
    console.rule(style="cyan")


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
