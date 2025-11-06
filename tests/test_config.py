"""
Tests for configuration management system.

Tests the three-tier configuration hierarchy:
1. Environment variables (highest priority)
2. User config files (project root or ~/.config)
3. Bundled defaults (fallback)
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from tarotcli.config import Config, get_config


@pytest.fixture
def clean_environment(monkeypatch, tmp_path):
    """Remove all TAROTCLI_ environment variables and user config for isolated testing."""
    for key in list(os.environ.keys()):
        if key.startswith("TAROTCLI_"):
            monkeypatch.delenv(key, raising=False)

    # Also clean API keys
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    # Mock _load_user_config to return empty dict (ignore project config.yaml)
    # This ensures tests only use default.yaml
    def mock_load_user_config(self):
        return {}

    monkeypatch.setattr(
        "tarotcli.config.Config._load_user_config", mock_load_user_config
    )


class TestConfigLoading:
    """Test configuration file loading and merging."""

    def test_loads_default_config(self, clean_environment):
        """Config should load bundled defaults from src/tarotcli/default.yaml."""
        config = Config()

        # Should have default provider
        default_provider = config.get("models.default_provider")
        assert default_provider == "claude"

        # Should have claude config
        claude_config = config.get("models.providers.claude")
        assert claude_config is not None
        assert "model" in claude_config
        assert "temperature" in claude_config

    def test_deep_merge_preserves_unmodified_keys(self, clean_environment):
        """Deep merge should preserve nested keys not explicitly overridden."""
        config = Config()

        # Get a nested value that wouldn't be in minimal user config
        max_tokens = config.get("models.providers.claude.max_tokens")
        assert max_tokens == 2000  # From default.yaml


class TestConfigGet:
    """Test config.get() method with dot notation and hierarchy."""

    def test_get_top_level_key(self, clean_environment):
        """Should retrieve top-level config keys."""
        config = Config()
        models = config.get("models")
        assert isinstance(models, dict)
        assert "default_provider" in models

    def test_get_nested_key_with_dot_notation(self, clean_environment):
        """Should navigate nested dicts using dot notation."""
        config = Config()
        model = config.get("models.providers.claude.model")
        assert isinstance(model, str)
        assert "claude" in model.lower()

    def test_get_returns_default_for_missing_key(self, clean_environment):
        """Should return provided default when key doesn't exist."""
        config = Config()
        result = config.get("nonexistent.key.path", default="fallback")
        assert result == "fallback"

    def test_get_returns_none_for_missing_key_without_default(self, clean_environment):
        """Should return None when key missing and no default provided."""
        config = Config()
        result = config.get("nonexistent.key")
        assert result is None

    def test_environment_variable_overrides_config(
        self, clean_environment, monkeypatch
    ):
        """Environment variables should override file-based config."""
        config = Config()

        # Set env var override
        monkeypatch.setenv("TAROTCLI_MODELS_DEFAULT_PROVIDER", "ollama")

        result = config.get("models.default_provider")
        assert result == "ollama"

    def test_environment_variable_with_nested_path(
        self, clean_environment, monkeypatch
    ):
        """Env vars should work for deeply nested config paths."""
        config = Config()

        monkeypatch.setenv("TAROTCLI_MODELS_PROVIDERS_CLAUDE_TEMPERATURE", "0.9")

        result = config.get("models.providers.claude.temperature")
        assert result == 0.9  # Should be parsed as float


class TestEnvValueParsing:
    """Test type coercion for environment variable strings."""

    def test_parse_boolean_true_variants(self, clean_environment, monkeypatch):
        """Should parse various true boolean strings."""
        config = Config()

        for true_val in ["true", "True", "TRUE", "yes", "Yes", "1", "on", "ON"]:
            monkeypatch.setenv("TAROTCLI_TEST_BOOL", true_val)
            result = config.get("test.bool")
            assert result is True, f"Failed to parse '{true_val}' as True"

    def test_parse_boolean_false_variants(self, clean_environment, monkeypatch):
        """Should parse various false boolean strings."""
        config = Config()

        for false_val in ["false", "False", "FALSE", "no", "No", "0", "off", "OFF"]:
            monkeypatch.setenv("TAROTCLI_TEST_BOOL", false_val)
            result = config.get("test.bool")
            assert result is False, f"Failed to parse '{false_val}' as False"

    def test_parse_integer(self, clean_environment, monkeypatch):
        """Should parse integer strings."""
        config = Config()

        monkeypatch.setenv("TAROTCLI_TEST_INT", "2000")
        result = config.get("test.int")
        assert result == 2000
        assert isinstance(result, int)

    def test_parse_float(self, clean_environment, monkeypatch):
        """Should parse float strings."""
        config = Config()

        monkeypatch.setenv("TAROTCLI_TEST_FLOAT", "0.7")
        result = config.get("test.float")
        assert result == 0.7
        assert isinstance(result, float)

    def test_parse_string_fallback(self, clean_environment, monkeypatch):
        """Should return string unchanged if not a recognized type."""
        config = Config()

        monkeypatch.setenv("TAROTCLI_TEST_STRING", "claude-sonnet-4")
        result = config.get("test.string")
        assert result == "claude-sonnet-4"
        assert isinstance(result, str)


class TestGetModelConfig:
    """Test get_model_config() convenience method."""

    def test_get_model_config_for_claude(self, clean_environment):
        """Should return complete Claude configuration."""
        config = Config()

        claude_config = config.get_model_config("claude")
        assert isinstance(claude_config, dict)
        assert "model" in claude_config
        assert "temperature" in claude_config
        assert "max_tokens" in claude_config

    def test_get_model_config_for_ollama(self, clean_environment):
        """Should return complete Ollama configuration."""
        config = Config()

        ollama_config = config.get_model_config("ollama")
        assert isinstance(ollama_config, dict)
        assert "model" in ollama_config
        assert "api_base" in ollama_config

    def test_get_model_config_uses_default_provider(self, clean_environment):
        """When no provider specified, should use default_provider from config."""
        config = Config()

        # Default provider is 'claude'
        result = config.get_model_config()
        assert result == config.get_model_config("claude")

    def test_get_model_config_with_env_override(self, clean_environment, monkeypatch):
        """Should respect env var override for default provider."""
        config = Config()

        monkeypatch.setenv("TAROTCLI_MODELS_DEFAULT_PROVIDER", "ollama")

        result = config.get_model_config()  # No provider specified
        assert result == config.get_model_config("ollama")

    def test_get_model_config_returns_empty_for_unknown_provider(
        self, clean_environment
    ):
        """Should return empty dict for nonexistent provider."""
        config = Config()

        result = config.get_model_config("nonexistent_provider")
        assert result == {}


class TestGetApiKey:
    """Test API key retrieval from environment."""

    def test_get_api_key_for_claude(self, clean_environment, monkeypatch):
        """Should retrieve ANTHROPIC_API_KEY for claude provider."""
        config = Config()

        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-123")

        api_key = config.get_api_key("claude")
        assert api_key == "sk-ant-test-123"

    def test_get_api_key_for_openai(self, clean_environment, monkeypatch):
        """Should retrieve OPENAI_API_KEY for openai provider."""
        config = Config()

        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-123")

        api_key = config.get_api_key("openai")
        assert api_key == "sk-test-123"

    def test_get_api_key_for_openrouter(self, clean_environment, monkeypatch):
        """Should retrieve OPENROUTER_API_KEY for openrouter provider."""
        config = Config()

        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-123")

        api_key = config.get_api_key("openrouter")
        assert api_key == "sk-or-test-123"

    def test_get_api_key_for_ollama_returns_none(self, clean_environment):
        """Ollama doesn't need API key, should return None."""
        config = Config()

        api_key = config.get_api_key("ollama")
        assert api_key is None

    def test_get_api_key_returns_none_when_not_set(self, clean_environment):
        """Should return None when API key not in environment."""
        config = Config()

        api_key = config.get_api_key("claude")
        assert api_key is None

    def test_get_api_key_uses_default_provider(self, clean_environment, monkeypatch):
        """When no provider specified, should use default provider."""
        config = Config()

        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-123")

        # Default provider is claude
        api_key = config.get_api_key()
        assert api_key == "sk-ant-test-123"

    def test_get_api_key_with_provider_override(self, clean_environment, monkeypatch):
        """Should respect provider parameter even if default is different."""
        config = Config()

        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-123")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-test-456")

        # Even though default is claude, explicitly request openai
        api_key = config.get_api_key("openai")
        assert api_key == "sk-openai-test-456"


class TestGetDataPath:
    """Test data file path resolution."""

    def test_get_data_path_returns_absolute_path(self):
        """Should return absolute Path object."""
        config = Config()

        path = config.get_data_path("tarot_cards_RW.jsonl")
        assert isinstance(path, Path)
        assert path.is_absolute()

    def test_get_data_path_points_to_data_directory(self):
        """Should resolve to data/ directory in project root."""
        config = Config()

        path = config.get_data_path("tarot_cards_RW.jsonl")
        assert path.name == "tarot_cards_RW.jsonl"
        assert path.parent.name == "data"

    def test_get_data_path_with_env_override(
        self, clean_environment, monkeypatch, tmp_path
    ):
        """Should respect TAROTCLI_DATA_DIR environment variable."""
        config = Config()

        custom_dir = tmp_path / "custom_data"
        custom_dir.mkdir()
        monkeypatch.setenv("TAROTCLI_DATA_DIR", str(custom_dir))

        path = config.get_data_path("tarot_cards_RW.jsonl")
        assert path.parent == custom_dir


class TestSingletonPattern:
    """Test get_config() singleton function."""

    def test_get_config_returns_same_instance(self):
        """Multiple calls to get_config() should return same instance."""
        config1 = get_config()
        config2 = get_config()

        assert config1 is config2

    def test_get_config_returns_config_instance(self):
        """Should return Config instance."""
        config = get_config()
        assert isinstance(config, Config)


class TestConfigurationHierarchy:
    """Integration tests for three-tier hierarchy."""

    def test_hierarchy_env_overrides_all(self, clean_environment, monkeypatch):
        """Environment variables should override both user and default config."""
        config = Config()

        # Default has claude as default_provider
        # Override with env var
        monkeypatch.setenv("TAROTCLI_MODELS_DEFAULT_PROVIDER", "ollama")

        result = config.get("models.default_provider")
        assert result == "ollama"

    def test_hierarchy_default_fallback(self, clean_environment):
        """Without user config or env var, should use default from default.yaml."""
        config = Config()

        # These should come from default.yaml
        provider = config.get("models.default_provider")
        assert provider == "claude"

        temperature = config.get("models.providers.claude.temperature")
        assert temperature == 0.7

    def test_complete_workflow_with_overrides(self, clean_environment, monkeypatch):
        """Test realistic usage with multiple override levels."""
        config = Config()

        # Start with defaults
        assert config.get("models.default_provider") == "claude"

        # Override provider with env var
        monkeypatch.setenv("TAROTCLI_MODELS_DEFAULT_PROVIDER", "ollama")
        assert config.get("models.default_provider") == "ollama"

        # Override specific setting
        monkeypatch.setenv("TAROTCLI_MODELS_PROVIDERS_OLLAMA_TEMPERATURE", "0.95")
        assert config.get("models.providers.ollama.temperature") == 0.95

        # Unrelated setting still uses default
        assert config.get("models.providers.claude.max_tokens") == 2000
