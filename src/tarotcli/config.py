"""Configuration management for tarotCLI.

Implements three-tier configuration hierarchy:
1. Environment variables (highest priority)
2. User config files (project root or dotfiles)
3. Bundled defaults (fallback)

Environment variables use TAROTCLI_ prefix and override all file-based config.
Secrets (API keys) are ONLY stored in environment variables, never in config files.
"""

import os
from pathlib import Path
from typing import Any, Optional, cast
import yaml
from dotenv import load_dotenv

# Load .env file if present (for development workflow)
load_dotenv()


class Config:
    """Configuration manager with hierarchical override system.

    Loads configuration from multiple sources at initialization and merges them
    into a single dictionary. Environment variables are checked dynamically on
    each get() call to allow runtime overrides.

    Usage:
        Use the get_config() singleton function rather than instantiating directly:

        >>> from tarotcli.config import get_config
        >>> config = get_config()
        >>> provider = config.get("models.default_provider")

    Architecture:
        - Eager loading: All config files read at initialization (performance)
        - Lazy env check: Environment variables checked per-request (flexibility)
        - Deep merge: Nested dicts merged recursively (allows partial overrides)
    """

    def __init__(self):
        """Load and merge all configuration sources.

        Loads files eagerly at initialization to fail fast if bundled defaults
        are missing. User config is optional and may not exist.
        """
        self._system_config = self._load_system_defaults()
        self._user_config = self._load_user_config()
        self._merged_config = self._merge_configs()

    def _load_system_defaults(self) -> dict:
        """Load bundled default configuration.

        Reads src/tarotcli/default.yaml which is versioned and packaged with
        the application. This ensures the application always has valid config
        even without user customization.

        Returns:
            dict: System defaults from src/tarotcli/default.yaml

        Raises:
            FileNotFoundError: If default.yaml is missing (packaging error)
        """
        config_dir = Path(__file__).parent
        default_path = config_dir / "default.yaml"

        with open(default_path, "r") as f:
            return yaml.safe_load(f)

    def _load_user_config(self) -> dict:
        """Load user configuration from multiple locations.

        Searches in priority order, returning the first config found. This dual
        approach supports both development workflows (project root) and installed
        package usage (XDG dotfiles).

        Search priority:
        1. ./config.yaml (project root - for editable install development)
        2. ~/.config/tarotcli/config.yaml (user dotfiles - for installed package)

        Why this pattern:
            - Developers work with project root config during development
            - End users install package and use ~/.config/tarotcli/config.yaml
            - Same codebase supports both workflows seamlessly

        Returns:
            dict: User configuration or empty dict if no config found.
        """
        # Get project root (3 levels up from src/tarotcli/config.py)
        project_root = Path(__file__).parent.parent.parent

        user_config_paths = [
            project_root / "config.yaml",  # Development
            Path.home() / ".config" / "tarotcli" / "config.yaml",  # Installed
        ]

        for config_path in user_config_paths:
            if config_path.exists():
                with open(config_path, "r") as f:
                    return yaml.safe_load(f) or {}

        return {}

    def _merge_configs(self) -> dict:
        """Deep merge user config over system defaults.

        Uses recursive merging to allow partial overrides. For example, a user
        can override just "models.providers.claude.temperature" without having
        to redefine the entire "models" section.

        Why deep merge vs shallow:
            - Shallow merge would replace entire nested dicts
            - Deep merge preserves unmodified nested keys
            - Enables surgical overrides without duplication

        Returns:
            dict: Merged configuration with user overrides applied.
        """

        def deep_merge(base: dict, override: dict) -> dict:
            """Recursively merge override into base, preserving nested structure."""
            result = base.copy()
            for key, value in override.items():
                if (
                    key in result
                    and isinstance(result[key], dict)
                    and isinstance(value, dict)
                ):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result

        return deep_merge(self._system_config, self._user_config)

    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value with environment variable override.

        Implements three-tier hierarchy with dynamic environment check:
        1. Environment variables (checked every call - allows runtime override)
        2. Merged file config (user + system defaults)
        3. Provided default parameter

        Dot notation for nested keys: "models.providers.claude.model"
        Becomes env var: TAROTCLI_MODELS_PROVIDERS_CLAUDE_MODEL

        Type coercion: Environment variables are strings, but get() attempts
        intelligent type conversion via _parse_env_value() for booleans,
        integers, and floats.

        Args:
            key_path: Dot-separated path to config key.
            default: Default value if key not found in any source.

        Returns:
            Configuration value (env var > user config > defaults > provided default).

        Example:
            >>> config.get("models.default_provider")
            "claude"

            >>> os.environ["TAROTCLI_MODELS_DEFAULT_PROVIDER"] = "ollama"
            >>> config.get("models.default_provider")
            "ollama"  # Environment variable takes precedence

            >>> config.get("models.providers.claude.temperature")
            0.7  # Returns float, not string "0.7"
        """
        # Check environment variable first (highest priority)
        env_key = f"TAROTCLI_{key_path.upper().replace('.', '_')}"
        env_value = os.getenv(env_key)
        if env_value is not None:
            return self._parse_env_value(env_value)

        # Navigate nested config using dot notation
        keys = key_path.split(".")
        value = self._merged_config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def _parse_env_value(self, value: str) -> Any:
        """Parse environment variable string to appropriate type.

        Environment variables are always strings, but config values may be
        booleans, integers, or floats. This method provides intelligent type
        coercion for common patterns.

        Why this is needed:
            - YAML configs preserve types: temperature: 0.7 → float
            - Environment vars are strings: TEMPERATURE=0.7 → str "0.7"
            - Without coercion, behavior differs between config sources

        Supported conversions:
            - Boolean: "true", "yes", "1", "on" → True
            - Boolean: "false", "no", "0", "off" → False
            - Float: "0.7" → 0.7
            - Integer: "2000" → 2000
            - Fallback: Unchanged string
        """
        # Handle booleans
        if value.lower() in ("true", "yes", "1", "on"):
            return True
        if value.lower() in ("false", "no", "0", "off"):
            return False

        # Try numeric conversion
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            pass

        return value

    def get_model_config(self, provider: Optional[str] = None) -> dict:
        """Get complete model configuration for specified provider.

        Convenience method that retrieves the entire provider config dict,
        allowing callers to access model, temperature, max_tokens, api_base, etc.
        in one call instead of multiple get() invocations.

        If no provider specified, uses "models.default_provider" from config.
        This enables "switch provider by changing one config value" workflow.

        Args:
            provider: Model provider name. If None, uses configured default.

        Returns:
            dict: Model configuration including model name, temperature, max_tokens, etc.
                  Returns empty dict if provider not found.

        Example:
            >>> config.get_model_config("ollama")
            {
                "model": "deepseek-r1:8b",
                "api_base": "http://localhost:11434",
                "temperature": 0.8,
                "max_tokens": 1500
            }

            >>> config.get_model_config()  # Uses default provider
            {
                "model": "claude-sonnet-4-5-20250929",
                "temperature": 0.7,
                "max_tokens": 2000
            }
        """
        if provider is None:
            provider = self.get("models.default_provider", "claude")

        return self.get(f"models.providers.{provider}", {})

    def get_api_key(self, provider: Optional[str] = None) -> Optional[str]:
        """Get API key for specified provider from environment only.

        Security: API keys are NEVER stored in config files, only environment variables.
        This method deliberately ignores config files and only checks environment.

        Provider resolution: If no provider specified, resolves to default provider
        from config. This allows switching providers without changing API key lookup.

        Returns None for providers that don't require API keys (e.g., Ollama local).

        Args:
            provider: Provider name. If None, uses configured default.

        Returns:
            Optional[str]: API key from environment or None if not found/not needed.

        Example:
            >>> os.environ["ANTHROPIC_API_KEY"] = "sk-ant-..."
            >>> config.get_api_key("claude")
            "sk-ant-..."

            >>> config.get_api_key("ollama")
            None  # Ollama doesn't need API key
        """
        # Resolve provider to concrete string
        provider_name: str
        if provider is None:
            provider_name = cast(str, self.get("models.default_provider", "claude"))
        else:
            provider_name = provider

        # Map provider names to environment variable names
        env_key_map: dict[str, Optional[str]] = {
            "claude": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "ollama": None,  # Local model, no API key needed
        }

        env_key = env_key_map.get(provider_name)
        if env_key is None:
            return None

        return os.getenv(env_key)

    def get_data_path(self, filename: str) -> Path:
        """Get absolute path to data file.

        Provides portable path resolution for data files, supporting both
        development (editable install) and distribution (installed package)
        scenarios.

        Environment override: TAROTCLI_DATA_DIR allows custom data location
        without modifying code (useful for testing or alternative datasets).

        Default behavior: Resolves to data/ at project root by walking up from
        this file's location (src/tarotcli/config.py → src/tarotcli → src → root).

        Args:
            filename: Data filename (e.g., "tarot_cards_RW.jsonl").

        Returns:
            Path: Absolute path to data file.

        Example:
            >>> config.get_data_path("tarot_cards_RW.jsonl")
            PosixPath('/home/user/tarotCLI/data/tarot_cards_RW.jsonl')

            >>> os.environ["TAROTCLI_DATA_DIR"] = "/custom/data"
            >>> config.get_data_path("tarot_cards_RW.jsonl")
            PosixPath('/custom/data/tarot_cards_RW.jsonl')
        """
        # Check for custom data directory
        data_dir = os.getenv("TAROTCLI_DATA_DIR")
        if data_dir:
            return Path(data_dir) / filename

        # Default: project root data/ directory
        # Get project root (3 levels up from src/tarotcli/config.py)
        project_root = Path(__file__).parent.parent.parent
        return project_root / "data" / filename


# Singleton pattern for global config instance
_config = None


def get_config() -> Config:
    """Get global configuration instance (singleton).

    Use this function rather than instantiating Config() directly. The singleton
    pattern ensures config files are only loaded once per process, improving
    performance and consistency.

    When to use vs direct instantiation:
        - Application code: ALWAYS use get_config() (standard pattern)
        - Tests: MAY instantiate Config() directly to isolate test state
        - Library users: Use get_config() (standard pattern)

    Thread safety: Not thread-safe. Config should be initialized at application
    startup before spawning threads/processes.

    Returns:
        Config: Global configuration manager instance.

    Example:
        >>> from tarotcli.config import get_config
        >>> config = get_config()
        >>> model = config.get("models.default_provider")
    """
    global _config
    if _config is None:
        _config = Config()
    return _config
