"""Test suite for CLI commands using typer.testing."""

import pytest
import json
from typer.testing import CliRunner
from unittest.mock import Mock, patch

from tarotcli.cli import app
from tarotcli.models import FocusArea

runner = CliRunner()


@pytest.fixture(autouse=True)
def disable_persistence():
    """Prevent tests from writing to real persistence storage."""
    with patch("tarotcli.cli.ReadingPersistence"):
        yield


def test_version_command():
    """Version command should display version."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "TarotCLI version" in result.stdout


def test_list_spreads_command():
    """List spreads should show all available spreads."""
    result = runner.invoke(app, ["list-spreads"])
    assert result.exit_code == 0
    assert "Three Card Spread" in result.stdout
    assert "Celtic Cross" in result.stdout
    assert "Single Card" in result.stdout


def test_config_info_command():
    """Config info should display current configuration."""
    result = runner.invoke(app, ["config-info"])
    assert result.exit_code == 0
    assert "Default Provider:" in result.stdout
    assert "Model:" in result.stdout
    assert "Data Path:" in result.stdout
    # Should show some model name, not the exact one
    assert (
        "claude" in result.stdout or "gpt" in result.stdout or "ollama" in result.stdout
    )


def test_read_command_no_ai_json_output():
    """Read command with --json and --no-ai should output valid JSON."""
    mock_deck = Mock()
    mock_deck.load_default.return_value = mock_deck

    # Mock card data
    mock_card = Mock()
    mock_card.name = "The Magician"
    mock_card.upright_meaning = "Skill, diplomacy"
    mock_card.reversed_meaning = "Trickery, manipulation"

    mock_drawn_card = Mock()
    mock_drawn_card.card = mock_card
    mock_drawn_card.reversed = False
    mock_drawn_card.position_meaning = "Present"
    mock_drawn_card.effective_meaning = "Skill, diplomacy"

    mock_deck.draw.return_value = [mock_drawn_card]

    # Mock spread
    mock_spread = Mock()
    mock_spread.card_count.return_value = 1

    mock_reading = Mock()
    mock_reading.model_dump_json.return_value = json.dumps(
        {
            "spread_type": "single",
            "focus_area": "general",
            "cards": [{"name": "The Magician", "reversed": False}],
            "interpretation": None,
            "static_interpretation": "Single Card Reading\n\nFocus: General\n\n## Present: The Magician (Upright)\nSkill, diplomacy",
        }
    )

    mock_spread.create_reading.return_value = mock_reading

    with (
        patch("tarotcli.cli.TarotDeck.load_default", return_value=mock_deck),
        patch("tarotcli.cli.get_spread", return_value=mock_spread),
    ):
        result = runner.invoke(
            app,
            ["read", "--spread", "single", "--focus", "general", "--no-ai", "--json"],
        )

        assert result.exit_code == 0

        # Parse JSON to validate structure
        reading_data = json.loads(result.stdout)
        assert "spread_type" in reading_data
        assert "cards" in reading_data
        assert "static_interpretation" in reading_data
        assert reading_data["spread_type"] == "single"
        assert reading_data["focus_area"] == "general"


def test_read_command_missing_spread_prompt_interactive():
    """Should prompt for spread when not provided via CLI."""
    # Test with mocked interactive prompts
    with patch("tarotcli.cli.gather_reading_inputs") as mock_gather:
        mock_gather.return_value = ("single", FocusArea.GENERAL, None, False, False)

        mock_deck = Mock()
        mock_deck.load_default.return_value = mock_deck
        mock_deck.draw.return_value = [Mock()]  # Need at least one mock card

        mock_spread = Mock()
        mock_spread.card_count.return_value = 1
        mock_reading = Mock(
            interpretation=None,
            question=None,
            cards=[Mock()],
            spread_type="single",
            focus_area=FocusArea.GENERAL,
        )
        mock_spread.create_reading.return_value = mock_reading

        with (
            patch("tarotcli.cli.TarotDeck.load_default", return_value=mock_deck),
            patch("tarotcli.cli.get_spread", return_value=mock_spread),
            patch("tarotcli.cli.display_reading"),
        ):
            result = runner.invoke(app, ["read"])
            assert result.exit_code == 0
            mock_gather.assert_called_once()


def test_read_command_invalid_focus_area():
    """Should handle invalid focus area gracefully."""
    result = runner.invoke(
        app, ["read", "--spread", "single", "--focus", "invalid_focus"]
    )

    assert result.exit_code != 0
    # Since typer handles errors well, just check that it failed properly
    assert "invalid_focus" in str(result.exception) or result.exit_code != 0


def test_read_command_provider_override():
    """Should allow AI provider override via CLI."""
    mock_deck = Mock()
    mock_deck.load_default.return_value = mock_deck
    mock_deck.draw.return_value = [Mock()]  # Provide mock cards

    mock_spread = Mock()
    mock_spread.card_count.return_value = 1
    mock_reading = Mock(
        interpretation="AI interpretation",
        question=None,
        cards=[Mock()],
        spread_type="single",
        focus_area=FocusArea.GENERAL,
    )
    mock_spread.create_reading.return_value = mock_reading

    with (
        patch("tarotcli.cli.TarotDeck.load_default", return_value=mock_deck),
        patch("tarotcli.cli.get_spread", return_value=mock_spread),
        patch("tarotcli.cli.interpret_reading_sync") as mock_ai,
        patch("tarotcli.cli.display_reading"),
    ):
        mock_ai.return_value = "Mock AI interpretation"

        result = runner.invoke(
            app,
            [
                "read",
                "--spread",
                "single",
                "--focus",
                "general",
                "--provider",
                "ollama",
            ],
        )

        assert result.exit_code == 0
        mock_ai.assert_called_once()
        # Check that provider override was passed
        call_args = mock_ai.call_args
        assert call_args.kwargs.get("provider") == "ollama"


def test_read_command_ai_error_graceful_degradation():
    """Should fall back to static interpretation when AI interpretation fails."""
    mock_deck = Mock()
    mock_deck.load_default.return_value = mock_deck
    mock_deck.draw.return_value = [Mock()]  # Provide mock cards

    mock_spread = Mock()
    mock_spread.card_count.return_value = 1
    mock_reading = Mock()
    mock_reading.interpretation = None
    mock_reading.static_interpretation = "Static interpretation"
    mock_reading.question = None
    mock_reading.cards = [Mock()]
    mock_reading.spread_type = "single"
    mock_reading.focus_area = FocusArea.GENERAL

    mock_spread.create_reading.return_value = mock_reading

    mock_config = Mock()
    mock_config.get.return_value = False  # display.show_imagery = False

    with (
        patch("tarotcli.cli.TarotDeck.load_default", return_value=mock_deck),
        patch("tarotcli.cli.get_spread", return_value=mock_spread),
        patch("tarotcli.cli.interpret_reading_sync") as mock_ai,
        patch("tarotcli.cli.display_reading") as mock_display,
        patch("tarotcli.cli.get_config", return_value=mock_config),
    ):
        # Make AI raise an exception
        mock_ai.side_effect = Exception("API error")

        result = runner.invoke(
            app, ["read", "--spread", "single", "--focus", "general"]
        )

        assert result.exit_code == 0
        mock_display.assert_called_once_with(
            mock_reading, show_imagery=False
        )  # Called with reading object and show_imagery default
        # AI error message is printed via typer.echo(err=True) which goes to stderr
        assert (
            "AI interpretation failed" in result.stdout
            or "AI interpretation failed" in result.stderr
        )


def test_cli_main_function_exists():
    """Main function should be callable."""
    from tarotcli.cli import main

    assert callable(main)


@pytest.mark.parametrize("spread_type", ["single", "three", "celtic"])
def test_read_command_all_spreads(spread_type):
    """Should accept all valid spread types."""
    mock_deck = Mock()
    mock_deck.load_default.return_value = mock_deck
    mock_deck.draw.return_value = [Mock()]  # Provide mock cards

    mock_spread = Mock()
    mock_spread.card_count.return_value = 1
    mock_reading = Mock(
        interpretation=None,
        question=None,
        cards=[Mock()],
        spread_type=spread_type,
        focus_area=FocusArea.GENERAL,
    )
    mock_spread.create_reading.return_value = mock_reading

    with (
        patch("tarotcli.cli.TarotDeck.load_default", return_value=mock_deck),
        patch("tarotcli.cli.get_spread", return_value=mock_spread),
        patch("tarotcli.cli.display_reading"),
    ):
        result = runner.invoke(
            app, ["read", "--spread", spread_type, "--focus", "general", "--no-ai"]
        )

        assert result.exit_code == 0


# ============================================================================
# Lookup Command Tests
# ============================================================================


def test_lookup_command_exact_match():
    """Should display card meanings for exact match."""
    mock_deck = Mock()
    mock_card = Mock()
    mock_card.name = "The Magician"
    mock_card.upright_meaning = "Skill, diplomacy, address, subtlety"
    mock_card.reversed_meaning = "Physician, Magus, mental disease"
    mock_card.description = "A youthful figure in the robe of a magician..."

    with (
        patch("tarotcli.cli.TarotDeck.load_default", return_value=mock_deck),
        patch("tarotcli.cli.lookup_card", return_value=mock_card),
    ):
        result = runner.invoke(app, ["lookup", "the magician"])

        assert result.exit_code == 0
        assert "The Magician" in result.stdout
        assert "↑ UPRIGHT" in result.stdout
        assert "↓ REVERSED" in result.stdout
        assert "Skill, diplomacy" in result.stdout
        assert "Physician, Magus" in result.stdout
        # Should NOT show imagery by default
        assert "IMAGERY" not in result.stdout


def test_lookup_command_with_imagery_flag():
    """Should display imagery descriptions when --show-imagery flag is used."""
    mock_deck = Mock()
    mock_card = Mock()
    mock_card.name = "Ace of Wands"
    mock_card.upright_meaning = "Creation, invention, enterprise"
    mock_card.reversed_meaning = "Fall, decadence, ruin"
    mock_card.description = "A hand issuing from a cloud grasps a stout wand..."

    with (
        patch("tarotcli.cli.TarotDeck.load_default", return_value=mock_deck),
        patch("tarotcli.cli.lookup_card", return_value=mock_card),
    ):
        result = runner.invoke(app, ["lookup", "ace of wands", "--show-imagery"])

        assert result.exit_code == 0
        assert "Ace of Wands" in result.stdout
        assert "🖼️  IMAGERY (Waite 1911)" in result.stdout
        assert "A hand issuing from a cloud" in result.stdout


def test_lookup_command_multiple_matches():
    """Should display list of options when search is ambiguous."""
    mock_deck = Mock()
    mock_card1 = Mock()
    mock_card1.name = "Ace of Wands"
    mock_card2 = Mock()
    mock_card2.name = "Ace of Cups"
    mock_card3 = Mock()
    mock_card3.name = "Ace of Swords"

    # Return list for ambiguous match
    with (
        patch("tarotcli.cli.TarotDeck.load_default", return_value=mock_deck),
        patch(
            "tarotcli.cli.lookup_card",
            return_value=[mock_card1, mock_card2, mock_card3],
        ),
    ):
        result = runner.invoke(app, ["lookup", "ace"])

        assert result.exit_code == 1
        assert "Multiple cards matched 'ace'" in result.stdout
        assert "Ace of Wands" in result.stdout
        assert "Ace of Cups" in result.stdout
        assert "Ace of Swords" in result.stdout
        assert "Please refine your search" in result.stdout


def test_lookup_command_not_found():
    """Should display helpful error when card not found."""
    mock_deck = Mock()

    # Return None for not found
    with (
        patch("tarotcli.cli.TarotDeck.load_default", return_value=mock_deck),
        patch("tarotcli.cli.lookup_card", return_value=None),
    ):
        result = runner.invoke(app, ["lookup", "nonexistent"])

        assert result.exit_code == 1
        assert "Card not found: 'nonexistent'" in result.stdout
        assert "Try:" in result.stdout
        assert "Full name: 'Ace of Wands'" in result.stdout
        assert "Partial match: 'magician'" in result.stdout


def test_lookup_command_case_insensitive():
    """Should handle case-insensitive searches."""
    mock_deck = Mock()
    mock_card = Mock()
    mock_card.name = "The Fool"
    mock_card.upright_meaning = "Folly, mania, extravagance"
    mock_card.reversed_meaning = "Negligence, absence, distribution"
    mock_card.description = "With light step..."

    with (
        patch("tarotcli.cli.TarotDeck.load_default", return_value=mock_deck),
        patch("tarotcli.cli.lookup_card", return_value=mock_card),
    ):
        result = runner.invoke(app, ["lookup", "THE FOOL"])

        assert result.exit_code == 0
        assert "The Fool" in result.stdout


def test_lookup_command_partial_match():
    """Should handle partial name matching."""
    mock_deck = Mock()
    mock_card = Mock()
    mock_card.name = "The Magician"
    mock_card.upright_meaning = "Skill, diplomacy"
    mock_card.reversed_meaning = "Physician, Magus"
    mock_card.description = "A youthful figure..."

    with (
        patch("tarotcli.cli.TarotDeck.load_default", return_value=mock_deck),
        patch("tarotcli.cli.lookup_card", return_value=mock_card),
    ):
        result = runner.invoke(app, ["lookup", "magician"])

        assert result.exit_code == 0
        assert "The Magician" in result.stdout


def test_lookup_command_error_handling():
    """Should handle unexpected errors gracefully."""
    with patch(
        "tarotcli.cli.TarotDeck.load_default", side_effect=Exception("Deck load error")
    ):
        result = runner.invoke(app, ["lookup", "the fool"])

        assert result.exit_code == 1
        assert "Error" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__])
