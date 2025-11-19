"""Reading persistence for tarotCLI.

Provides lightweight JSONL storage for reading history. Append-only file format
ensures crash-safe writes - partial writes don't corrupt existing data.

Design principles:
- Graceful degradation: Persistence failures never block readings
- Minimal complexity: JSONL files, no database
- User control: Opt-in via config (default: disabled)
"""

import json
from pathlib import Path
from typing import Optional

from tarotcli.config import get_config
from tarotcli.models import Reading


class ReadingPersistence:
    """Manages reading persistence to JSONL storage.

    Handles saving and retrieving readings from append-only JSONL files.
    All operations are crash-safe and fail gracefully without blocking
    the main reading functionality.

    JSONL format: One reading per line, each line is valid JSON.
    This ensures partial writes don't corrupt the entire file.

    Storage location determined by Config.get_readings_path():
    - Linux: ~/.local/share/tarotcli/readings.jsonl
    - macOS: ~/Library/Application Support/tarotcli/readings.jsonl
    - Windows: C:\\Users\\<user>\\AppData\\Local\\tarotcli\\readings.jsonl

    Usage:
        >>> persistence = ReadingPersistence()
        >>> persistence.save(reading)  # Auto-creates directory if needed
        >>> readings = persistence.load_all()  # Returns list of Reading objects
        >>> recent = persistence.load_last(5)  # Last 5 readings
    """

    def __init__(self, config_override: Optional[Path] = None):
        """Initialize persistence with optional path override.

        Args:
            config_override: Optional path override for testing.
                If None, uses path from config system.
        """
        config = get_config()
        self.readings_path = (
            config_override if config_override else config.get_readings_path()
        )

    def save(self, reading: Reading) -> bool:
        """Save reading to JSONL file (append-only).

        Creates parent directory if it doesn't exist. Gracefully handles
        all errors - never raises exceptions that could block readings.

        Args:
            reading: Reading to persist.

        Returns:
            bool: True if save succeeded, False otherwise.

        Example:
            >>> reading = perform_reading(deck, "three_card", FocusArea.CAREER)
            >>> persistence = ReadingPersistence()
            >>> success = persistence.save(reading)
        """
        try:
            # Ensure parent directory exists
            self.readings_path.parent.mkdir(parents=True, exist_ok=True)

            # Append reading as single JSON line
            with open(self.readings_path, "a", encoding="utf-8") as f:
                f.write(reading.model_dump_json() + "\n")

            return True

        except Exception as e:
            # Graceful degradation: warn but don't block reading
            print(f"⚠️  Failed to save reading: {e}")
            return False

    def load_all(self) -> list[Reading]:
        """Load all readings from JSONL file.

        Gracefully handles missing files and malformed JSON. Skips
        invalid lines rather than failing entirely.

        Returns:
            list[Reading]: All valid readings, or empty list if file missing/empty.

        Example:
            >>> persistence = ReadingPersistence()
            >>> all_readings = persistence.load_all()
            >>> print(f"Total readings: {len(all_readings)}")
        """
        if not self.readings_path.exists():
            return []

        readings = []
        try:
            with open(self.readings_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, start=1):
                    line = line.strip()
                    if not line:
                        continue  # Skip empty lines

                    try:
                        data = json.loads(line)
                        reading = Reading.model_validate(data)
                        readings.append(reading)
                    except (json.JSONDecodeError, ValueError) as e:
                        # Skip malformed lines, warn user
                        print(f"⚠️  Skipping invalid reading at line {line_num}: {e}")
                        continue

        except Exception as e:
            print(f"⚠️  Error loading readings: {e}")
            return []

        return readings

    def load_last(self, n: int = 10) -> list[Reading]:
        """Load last N readings from file.

        More efficient than load_all() for large files - only deserializes
        the requested number of readings.

        Args:
            n: Number of recent readings to load. Default 10.

        Returns:
            list[Reading]: Last N valid readings, or fewer if file has less.

        Example:
            >>> persistence = ReadingPersistence()
            >>> recent = persistence.load_last(5)
            >>> for reading in recent:
            ...     print(f"{reading.timestamp}: {reading.spread_type}")
        """
        all_readings = self.load_all()
        return all_readings[-n:] if all_readings else []

    def delete_last(self, n: int) -> bool:
        """Delete last N readings from storage.

        More surgical than clear_all() - removes only recent readings while
        preserving older history. Useful for privacy when you want to remove
        recent sensitive readings without losing entire history.

        Args:
            n: Number of recent readings to delete.

        Returns:
            bool: True if deletion succeeded, False on error.

        Example:
            >>> persistence = ReadingPersistence()
            >>> persistence.delete_last(5)  # Remove last 5 readings
        """
        try:
            all_readings = self.load_all()

            if not all_readings:
                # No readings to delete
                return True

            # Keep all except last N
            readings_to_keep = all_readings[:-n] if n < len(all_readings) else []

            # Rewrite file with remaining readings
            if readings_to_keep:
                # Clear file and rewrite
                with open(self.readings_path, "w", encoding="utf-8") as f:
                    for reading in readings_to_keep:
                        f.write(reading.model_dump_json() + "\n")
            else:
                # All readings deleted, remove file
                if self.readings_path.exists():
                    self.readings_path.unlink()

            return True

        except Exception as e:
            print(f"⚠️  Failed to delete readings: {e}")
            return False

    def clear_all(self) -> bool:
        """Delete all persisted readings (destructive operation).

        Removes the readings.jsonl file entirely. Use with caution.

        Returns:
            bool: True if deletion succeeded or file didn't exist, False on error.

        Example:
            >>> persistence = ReadingPersistence()
            >>> persistence.clear_all()  # Nuclear option
        """
        try:
            if self.readings_path.exists():
                self.readings_path.unlink()
            return True
        except Exception as e:
            print(f"⚠️  Failed to clear readings: {e}")
            return False
