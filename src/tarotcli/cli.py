"""Typer-based CLI commands and entry point for TarotCLI.

Implements complete tarot reading functionality through command-line interface.
Supports both interactive mode with questionary prompts and CLI argument mode.
Integrates with deck operations, spread layouts, AI interpretation, and configuration.

Commands:
    read: Perform tarot readings (interactive or CLI args)
    lookup: Look up meanings for specific cards (physical deck companion)
    history: View past readings from JSONL storage
    clear-history: Delete reading history (privacy/cleanup)
    version: Display current version
    list-spreads: Show available spread types
    config-info: Display current configuration

Features:
    - Multiple spread types (single, three, celtic)
    - AI provider override (claude, ollama, openai, openrouter)
    - JSON and markdown output formats
    - Card lookup with fuzzy matching and imagery descriptions
    - Graceful degradation to static interpretation
    - Progress indicators and error handling

Example:
    $ tarotcli read --spread three --focus career
    $ tarotcli lookup "ace of wands" --show-imagery
    $ tarotcli config-info
"""

import typer
from pathlib import Path
from typing import Optional
from tarotcli.config import get_config
from tarotcli.deck import TarotDeck, lookup_card
from tarotcli.spreads import get_spread
from tarotcli.models import FocusArea
from tarotcli.ai import interpret_reading_sync
from tarotcli.ui import gather_reading_inputs, display_reading, console
from tarotcli.persistence import ReadingPersistence
import questionary

app = typer.Typer(
    name="tarotcli", help="Minimalist tarot reading CLI with optional AI interpretation"
)


@app.callback(invoke_without_command=True)
def main_menu(ctx: typer.Context):
    """Interactive menu when no subcommand is provided."""
    if ctx.invoked_subcommand is not None:
        return  # Subcommand will handle it

    console.print()
    console.rule("[bold magenta]🔮 TarotCLI[/bold magenta]", style="magenta")
    console.print()

    action = questionary.select(
        "What is your intention?",
        choices=[
            {"name": "🔮 New Reading", "value": "read"},
            {"name": "🔍 Card Lookup", "value": "lookup"},
            {"name": "📚 View History", "value": "history"},
            {"name": "📋 List Spreads", "value": "list_spreads"},
            {"name": "⚙️  Config Info", "value": "config_info"},
            {"name": "❌ Exit", "value": "exit"},
        ],
    ).ask()

    if action is None or action == "exit":
        console.print("\n👋 Goodbye!\n")
        raise typer.Exit(0)

    # Handle lookup specially (needs card name input)
    if action == "lookup":
        card_name = questionary.text("Enter card name to look up:").ask()
        if card_name is None or not card_name.strip():
            console.print("\n👋 Lookup cancelled.\n")
            raise typer.Exit(0)
        ctx.invoke(lookup, card_name=card_name.strip())
    else:
        ctx.invoke(globals()[action])


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
        help="Use static interpretation only (card meanings from dataset, NO AI required).",
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
    show_imagery: bool = typer.Option(
        False, "--show-imagery", help="Include Waite's 1911 imagery descriptions"
    ),
):
    """Perform a tarot reading.

    Supports both interactive and CLI argument modes. Uses configured AI
    provider from config.yaml unless provider override is specified.
    Gracefully degrades to static interpretation if AI unavailable.

    Args:
        spread: Spread type (single, three, celtic). Interactive if not provided.
        focus: Focus area (career, relationships, personal_growth, spiritual, general).
        question: Specific question for the reading. Optional.
        no_ai: Use static interpretation only, skipping AI completely.
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
        result = gather_reading_inputs()
        if result is None:
            # User cancelled interactive prompts
            typer.echo("\n👋 Reading cancelled.\n")
            raise typer.Exit(0)
        spread_name, focus_area, user_question, use_ai, interactive_imagery = result
    else:
        # CLI mode - handle provider override
        spread_name = spread
        focus_area = FocusArea(focus)
        user_question = question  # Use the CLI question parameter
        use_ai = not no_ai
        interactive_imagery = None  # Will use CLI flag or config

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
                f"📖 Using static interpretation instead.\n"
                f"💡 Check your config.yaml or API keys if unexpected.\n",
                err=True,
            )

    # Auto-save reading if enabled
    config = get_config()
    if config.get("output.save_readings", False):
        persistence = ReadingPersistence()
        persistence.save(reading)  # Gracefully fails if error occurs

    # Output
    if json_output:
        print(reading.model_dump_json(indent=2))
    else:
        # Determine imagery: interactive choice > CLI flag > config
        if interactive_imagery is not None:
            display_imagery = interactive_imagery
        else:
            display_imagery = show_imagery or config.get("display.show_imagery", False)
        display_reading(reading, show_imagery=display_imagery)


@app.command()
def lookup(
    card_name: str = typer.Argument(..., help="Card name to look up"),
    show_imagery: bool = typer.Option(
        False, "--show-imagery", help="Include Waite's imagery descriptions"
    ),
):
    """Look up meanings for a specific tarot card.

    Displays both upright and reversed interpretations from Waite's 1911
    'Pictorial Key to the Tarot'. Use for physical deck readings or learning.

    Examples:
        tarotcli lookup "ace of wands"
        tarotcli lookup "magician" --show-imagery
    """
    try:
        deck = TarotDeck.load_default()
        card = lookup_card(deck, card_name)

        if card is None:
            print(f"❌ Card not found: '{card_name}'")
            print("\nTry:")
            print("  - Full name: 'Ace of Wands'")
            print("  - Partial match: 'magician'")
            raise typer.Exit(1)

        if isinstance(card, list):
            print(f"\nMultiple cards matched '{card_name}':")
            for c in card:
                print(f"  - {c.name}")
            print("\nPlease refine your search with a more specific card name.")
            raise typer.Exit(1)

        # Display card meanings using Rich
        from rich.panel import Panel

        console.print()
        console.rule(f"[bold cyan]{card.name}[/bold cyan]", style="cyan")

        console.print("\n[bold green]↑ UPRIGHT[/bold green]")
        console.rule(style="dim")
        console.print(card.upright_meaning)

        console.print("\n[bold red]↓ REVERSED[/bold red]")
        console.rule(style="dim")
        console.print(card.reversed_meaning)

        if show_imagery:
            console.print()
            console.print(
                Panel(
                    card.description,
                    title="[bold yellow]🖼️  IMAGERY (Waite 1911)[/bold yellow]",
                    border_style="yellow",
                )
            )

        console.print()
        console.rule(style="cyan")

    except Exception as e:
        print(f"❌ Error: {e}")
        raise typer.Exit(1)


@app.command()
def history(
    last: int = typer.Option(
        10, "--last", "-n", help="Number of recent readings to show (default: 10)"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output as JSON array instead of markdown"
    ),
):
    """View reading history.

    Displays past readings from JSONL storage. Requires output.save_readings
    to be enabled in config.yaml.

    Args:
        last: Number of recent readings to show. Default 10.
        json_output: Output as JSON array instead of markdown.

    Example:
        tarotcli history --last 5
        tarotcli history --json
    """
    config = get_config()

    # Check if persistence is enabled
    if not config.get("output.save_readings", False):
        typer.echo(
            "📖 Reading persistence is disabled.\n"
            "💡 Enable it in config.yaml: output.save_readings: true\n",
            err=True,
        )
        raise typer.Exit(1)

    # Load readings
    persistence = ReadingPersistence()
    readings = persistence.load_last(last)

    if not readings:
        typer.echo("📭 No readings found in history.\n")
        typer.echo("💡 Perform readings with save_readings enabled to build history.\n")
        return

    # Output
    if json_output:
        # Export as JSON array
        import json

        json_data = [r.model_dump() for r in readings]
        print(json.dumps(json_data, indent=2, default=str))
    else:
        # Display each reading using Rich formatting
        console.print(f"\n[bold]📚 Showing last {len(readings)} reading(s):[/bold]\n")
        for i, reading in enumerate(readings, start=1):
            # timestamp is ISO string from JSONL, not datetime object
            timestamp_str = reading.timestamp[:16].replace("T", " ") if reading.timestamp else "Unknown"
            console.print(f"[dim]Reading {i} - {timestamp_str}[/dim]")
            display_reading(reading)
            if i < len(readings):
                console.print()


@app.command()
def clear_history(
    last: int = typer.Option(
        None, "--last", "-n", help="Delete last N readings (leave empty for all)"
    ),
    all: bool = typer.Option(
        False, "--all", help="Delete all readings (requires confirmation)"
    ),
):
    """Delete reading history (privacy/cleanup).

    Provides granular control over deletion:
    - Delete last N readings: --last N
    - Delete all readings: --all

    All operations require confirmation to prevent accidental deletion.

    Args:
        last: Number of recent readings to delete. If None and not --all, prompts user.
        all: Delete all readings (requires confirmation).

    Example:
        tarotcli clear-history --last 5    # Delete last 5 readings
        tarotcli clear-history --all       # Delete all readings
    """
    config = get_config()

    # Check if persistence is enabled
    if not config.get("output.save_readings", False):
        typer.echo(
            "📖 Reading persistence is disabled.\n"
            "💡 No history to delete (save_readings: false in config).\n",
            err=True,
        )
        raise typer.Exit(0)

    persistence = ReadingPersistence()
    readings = persistence.load_all()

    if not readings:
        typer.echo("📭 No readings found in history. Nothing to delete.\n")
        return

    # Determine deletion scope
    if all:
        # Delete all readings
        typer.echo(f"\n⚠️  You are about to delete ALL {len(readings)} reading(s).\n")
        confirm = typer.confirm("This action cannot be undone. Continue?", default=False)

        if not confirm:
            typer.echo("❌ Deletion cancelled.\n")
            return

        success = persistence.clear_all()
        if success:
            typer.echo(f"✅ Deleted all {len(readings)} reading(s).\n")
        else:
            typer.echo("❌ Failed to delete readings. Check error messages above.\n")
            raise typer.Exit(1)

    elif last is not None:
        # Delete last N readings
        if last <= 0:
            typer.echo("❌ Error: --last must be a positive number.\n", err=True)
            raise typer.Exit(1)

        actual_delete = min(last, len(readings))
        typer.echo(
            f"\n⚠️  You are about to delete the last {actual_delete} reading(s).\n"
        )
        confirm = typer.confirm("This action cannot be undone. Continue?", default=False)

        if not confirm:
            typer.echo("❌ Deletion cancelled.\n")
            return

        success = persistence.delete_last(last)
        if success:
            typer.echo(f"✅ Deleted last {actual_delete} reading(s).\n")
        else:
            typer.echo("❌ Failed to delete readings. Check error messages above.\n")
            raise typer.Exit(1)

    else:
        # No option specified - show usage
        typer.echo(
            "❌ Error: Specify deletion scope:\n"
            "  - Delete last N readings: --last N\n"
            "  - Delete all readings: --all\n\n"
            "Example:\n"
            "  tarotcli clear-history --last 5\n"
            "  tarotcli clear-history --all\n",
            err=True,
        )
        raise typer.Exit(1)


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
    from platformdirs import user_config_dir

    config = get_config()
    provider = config.get("models.default_provider", "claude")
    model = config.get(f"models.providers.{provider}.model", "not configured")
    config_path = Path(user_config_dir("tarotcli", appauthor=False)) / "config.yaml"

    typer.echo("\n🔮 TarotCLI Configuration\n")
    typer.echo(f"  Default Provider: {provider}")
    typer.echo(f"  Model: {model}")
    typer.echo(f"  Data Path: {config.get_data_path('tarot_cards_RW.jsonl')}")
    typer.echo(f"\n💡 Edit {config_path} to customize\n")


def main():
    """Entry point for CLI."""
    app()


if __name__ == "__main__":
    main()
