"""Test suite for CLI commands using typer.testing."""

import pytest
import json
from typer.testing import CliRunner
from unittest.mock import Mock, patch

from tarotcli.cli import app
from tarotcli.models import FocusArea

runner = CliRunner()


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
            "baseline_interpretation": "Single Card Reading\n\nFocus: General\n\n## Present: The Magician (Upright)\nSkill, diplomacy",
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
        assert "baseline_interpretation" in reading_data
        assert reading_data["spread_type"] == "single"
        assert reading_data["focus_area"] == "general"


def test_read_command_missing_spread_prompt_interactive():
    """Should prompt for spread when not provided via CLI."""
    # Test with mocked interactive prompts
    with patch("tarotcli.cli.gather_reading_inputs") as mock_gather:
        mock_gather.return_value = ("single", FocusArea.GENERAL, None, False)

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
    """Should fall back to baseline when AI interpretation fails."""
    mock_deck = Mock()
    mock_deck.load_default.return_value = mock_deck
    mock_deck.draw.return_value = [Mock()]  # Provide mock cards

    mock_spread = Mock()
    mock_spread.card_count.return_value = 1
    mock_reading = Mock()
    mock_reading.interpretation = None
    mock_reading.baseline_interpretation = "Baseline interpretation"
    mock_reading.question = None
    mock_reading.cards = [Mock()]
    mock_reading.spread_type = "single"
    mock_reading.focus_area = FocusArea.GENERAL

    mock_spread.create_reading.return_value = mock_reading

    with (
        patch("tarotcli.cli.TarotDeck.load_default", return_value=mock_deck),
        patch("tarotcli.cli.get_spread", return_value=mock_spread),
        patch("tarotcli.cli.interpret_reading_sync") as mock_ai,
        patch("tarotcli.cli.display_reading") as mock_display,
    ):
        # Make AI raise an exception
        mock_ai.side_effect = Exception("API error")

        result = runner.invoke(
            app, ["read", "--spread", "single", "--focus", "general"]
        )

        assert result.exit_code == 0
        mock_display.assert_called_once_with(
            mock_reading
        )  # Remove show_baseline parameter
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


if __name__ == "__main__":
    pytest.main([__file__])
