"""Typer-based CLI commands and entry point for TarotCLI.

Implements complete tarot reading functionality through command-line interface.
Supports both interactive mode with questionary prompts and CLI argument mode.
Integrates with deck operations, spread layouts, AI interpretation, and configuration
system.

Commands:
- read: Perform tarot readings (interactive or CLI args)
- version: Display current version
- list-spreads: Show available spread types
- config-info: Display current configuration

Features:
- Multiple spread types (single, three, celtic)
- AI provider override (claude, ollama, openai, openrouter)
- JSON and markdown output formats
- Graceful degradation to baseline interpretation
- Progress indicators and error handling
"""

import typer
from typing import Optional
from tarotcli.config import get_config
from tarotcli.deck import TarotDeck
from tarotcli.spreads import get_spread
from tarotcli.models import FocusArea
from tarotcli.ai import interpret_reading_sync
from tarotcli.ui import gather_reading_inputs, display_reading

app = typer.Typer(
    name="tarotcli", help="Minimalist tarot reading CLI with optional AI interpretation"
)


@app.command()
def read(
    spread: Optional[str] = typer.Option(
        None,
        "--spread",
        "-s",
        help="Spread type (single, three, celtic). Interactive if not provided.",
    ),
    focus: Optional[str] = typer.Option(
        None,
        "--focus",
        "-f",
        help="Focus area (career, relationships, personal_growth, spiritual, general).",
    ),
    question: Optional[str] = typer.Option(
        None, "--question", "-q", help="Your specific question for the reading."
    ),
    no_ai: bool = typer.Option(
        False,
        "--no-ai",
        help="Use baseline interpretation only (static meanings, NO AI required).",
    ),
    provider: Optional[str] = typer.Option(
        None,
        "--provider",
        "-p",
        help="Override default AI provider (claude, ollama, openai, openrouter)",
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output as JSON instead of markdown formatted text."
    ),
):
    """Perform a tarot reading.

    Supports both interactive and CLI argument modes. Uses configured AI
    provider from config.yaml unless provider override is specified.
    Gracefully degrades to baseline interpretation if AI unavailable.

    Args:
        spread: Spread type (single, three, celtic). Interactive if not provided.
        focus: Focus area (career, relationships, personal_growth, spiritual, general).
        question: Specific question for the reading. Optional.
        no_ai: Use baseline interpretation only, skipping AI completely.
        provider: Override default AI provider (claude, ollama, openai, openrouter).
        json_output: Output as JSON instead of markdown formatted text.

    Returns:
        None. Prints reading to stdout or stderr in case of errors.

    Raises:
        typer.Exit: If required parameters are invalid or reading fails.

    Example:
        >>> # CLI argument mode
        >>> tarotcli read --spread three --focus career --no-ai
        >>> # Interactive mode (prompts for missing parameters)
        >>> tarotcli read
    """

    # Load deck using config system
    deck = TarotDeck.load_default()  # Uses config.get_data_path()

    # Gather parameters (interactive or CLI)
    if not all([spread, focus]):
        spread_name, focus_area, user_question, use_ai = gather_reading_inputs()
    else:
        # CLI mode - handle provider override
        spread_name = spread
        focus_area = FocusArea(focus)
        user_question = question  # Use the CLI question parameter
        use_ai = not no_ai

    # Validate spread_name is not None (should always be set from above logic)
    if spread_name is None:
        typer.echo("Error: Spread name is required", err=True)
        raise typer.Exit(1)

    # Perform reading
    deck.shuffle()
    spread_layout = get_spread(spread_name)
    drawn = deck.draw(spread_layout.card_count())
    reading = spread_layout.create_reading(
        cards=drawn, focus_area=focus_area, question=user_question
    )

    # Add AI interpretation if requested
    if use_ai:
        try:
            # Provider override via CLI or config default
            reading.interpretation = interpret_reading_sync(
                reading,
                provider=provider,  # None uses config default
            )
        except Exception as e:
            # Graceful degradation with helpful message
            typer.echo(
                f"⚠️  AI interpretation failed: {e}\n"
                f"📖 Using baseline interpretation instead.\n"
                f"💡 Check your config.yaml or API keys if unexpected.\n",
                err=True,
            )

    # Output
    if json_output:
        print(reading.model_dump_json(indent=2))
    else:
        display_reading(reading)


@app.command()
def version():
    """Display TarotCLI version."""
    from tarotcli import __version__

    typer.echo(f"TarotCLI version {__version__}")


@app.command()
def list_spreads():
    """List all available spread types."""
    from tarotcli.spreads import SPREADS

    typer.echo("\nAvailable Spreads:\n")
    for name, spread in SPREADS.items():
        typer.echo(f"  {name:12} - {spread.display_name} ({spread.card_count()} cards)")
        typer.echo(f"               {spread.description}\n")


@app.command()
def config_info():
    """Show current configuration summary.

    Displays current provider, model, and data path for debugging
    and configuration verification.
    """
    config = get_config()
    provider = config.get("models.default_provider", "claude")
    model = config.get(f"models.providers.{provider}.model", "not configured")

    typer.echo("\n🔮 TarotCLI Configuration\n")
    typer.echo(f"  Default Provider: {provider}")
    typer.echo(f"  Model: {model}")
    typer.echo(f"  Data Path: {config.get_data_path('tarot_cards_RW.jsonl')}")
    typer.echo("\n💡 Edit ~/.config/tarotcli/config.yaml to customize\n")


def main():
    """Entry point for CLI."""
    app()


if __name__ == "__main__":
    main()
