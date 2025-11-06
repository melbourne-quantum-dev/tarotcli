"""CLI commands and interface.

Placeholder until Milestone 4 implementation.
"""

import typer

app = typer.Typer(
    name="tarotcli", help="Minimalist tarot reading CLI (under development)"
)


def main():
    """Entry point for CLI - placeholder implementation."""
    print("\n" + "=" * 60)
    print("TarotCLI - Under Development")
    print("=" * 60)
    print("\n✅ Deck operations implemented")
    print("\nCurrent functionality:")
    print("  • Run test_deck_basic.py to see deck operations")
    print("  • Load/shuffle/draw with 78-card Rider-Waite deck")
    print("\nFull CLI coming in Milestone 4 (spreads + AI interpretation)")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
