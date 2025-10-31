"""
Basic usage examples for TarotCLI Python API.

Demonstrates programmatic reading generation without CLI.
"""
from pathlib import Path
from tarotcli.deck import TarotDeck
from tarotcli.spreads import get_spread
from tarotcli.models import FocusArea

def basic_reading():
    """Perform a simple three-card reading."""
    # Load deck
    data_path = Path(__file__).parent.parent / "data" / "tarot_cards_RW.jsonl"
    deck = TarotDeck(data_path)
    
    # Shuffle and draw
    deck.shuffle()
    spread = get_spread("three")
    cards = deck.draw(spread.card_count())
    
    # Create reading
    reading = spread.create_reading(
        cards=cards,
        focus_area=FocusArea.GENERAL,
        question=None
    )
    
    # Output
    print(reading.model_dump_json(indent=2))

if __name__ == "__main__":
    basic_reading()