# TarotCLI - Development Agent Context

## Project Overview

Minimalist tarot reading CLI with optional AI interpretation.
Foundation-first architecture: core functionality works reliably without LLM dependency.

**Current Status**: v0.4.0 stable ✅ COMPLETE (Milestone 4 finished, CLI fully implemented)

**Test Coverage**: 94%+ overall (86/86 tests passing)
- ai.py: 100% coverage ✅
- models.py: 100% coverage ✅  
- spreads.py: 100% coverage ✅
- config.py: 99% coverage ✅
- cli.py: 100% coverage ✅ (NEW)
- deck.py: 87% coverage ⚠️
- ui.py: 95% coverage ✅ (NEW)

**Completed Milestones:**
- ✅ Milestone 1 (v0.1.0): Core deck operations - COMPLETE
- ✅ Milestone 2 (v0.2.0): Spread layouts with baseline interpretation - COMPLETE
- ✅ Milestone 3 (v0.3.0): AI integration via Claude API - COMPLETE
- ✅ Milestone 3.5 (v0.3.5): Three-tier configuration system - COMPLETE
- ✅ Milestone 4 (v0.4.0): Interactive CLI - **COMPLETE**

**Milestone 4 Status**: CLI implementation complete and production-ready
- Full typer-based CLI with interactive and argument modes
- Complete test suite (12 CLI tests + 74 existing = 86 total)
- Comprehensive questionary UI for parameter collection
- AI provider override functionality
- JSON and markdown output formats
- Graceful degradation with proper error handling
- Production-ready documentation and code quality

## Commands

### Development
- `uv pip install -e '.[dev]'` - Install package in editable mode with dev dependencies
- `pytest` - Run full test suite (86/86 tests passing)
- `pytest tests/test_cli.py -v` - Run CLI tests specifically
- `pytest --cov=tarotcli --cov-report=html` - Generate coverage report
- `python -m tarotcli` - Run CLI entry point

### Usage
- `tarotcli read` - Interactive reading (questionary prompts for spread, focus, question)
- `tarotcli read --spread single --focus spiritual --no-ai` - CLI argument mode
- `tarotcli read --spread three --focus career --provider ollama` - Provider override
- `tarotcli read --spread celtic --question "specific question" --json` - JSON output
- `tarotcli list-spreads` - Show available spread types with descriptions
- `tarotcli version` - Display current version
- `tarotcli config-info` - Show current configuration (provider, model, data path)

## Architecture Principles

**Foundation-First Development:**
- Each milestone must work perfectly before moving to next
- Baseline functionality never depends on LLM availability
- Graceful degradation: readings always complete successfully

**Milestone Progression:**
1. Core deck operations (load, shuffle, draw) - NO LLM dependency
2. Spread layouts with baseline interpretation
3. AI integration with graceful degradation
4. Interactive CLI polish

**YOU MUST NOT add features from later milestones before current milestone is complete and tested.**

## Code Style

### Type Safety
- Use Pydantic v2 models for all data structures
- Include type hints on all function signatures
- Use `str | None` syntax (not `Optional[str]`)

### Docstrings
- Google-style docstrings for all public functions
- Include Args, Returns, Raises, Example sections
- Explain WHY (architectural decisions), not just WHAT

### Error Handling
- All functions that could fail must handle errors gracefully
- LLM functions return baseline on any error (never raise)
- Use descriptive error messages with context

### Testing
- Test coverage target: >90%
- Unit tests for each module independently
- Integration tests for full reading flow
- Mock external APIs (LiteLLM) in tests

**Current test status:**
- `tests/test_deck.py`: 11 tests (87% deck.py coverage)
- `tests/test_spreads.py`: 10 tests (100% spreads.py coverage)
- `tests/test_config.py`: 33 tests (99% config.py coverage)
- `tests/test_ai.py`: 20 tests (100% ai.py coverage)
- **Total**: 74/74 tests passing (100% pass rate, 91% overall coverage)

**Demonstration scripts** (manual validation in `examples/`):
- `demo_deck_operations.py`: Validates deck operations
- `demo_spread_layouts.py`: Validates spread layouts
- `demo_ai_interpretation.py`: Validates AI integration (use `DEBUG_PROMPT=1` to see full prompt)
- `demo_ai_comparison.py`: Side-by-side Claude vs Ollama comparison

**Note**: All tests now pass with proper config system integration and test isolation from user config files.

## Core Files

- `src/tarotcli/models.py` - Pydantic data models (Card, DrawnCard, Reading, FocusArea)
- `src/tarotcli/deck.py` - Deck operations (load 78 cards from JSONL, shuffle, draw)
- `src/tarotcli/spreads.py` - Spread layouts (single, three-card, Celtic Cross)
- `src/tarotcli/ai.py` - LLM API integration via LiteLLM (graceful degradation)
- `src/tarotcli/config.py` - **Configuration management system (Milestone 3.5)**
- `src/tarotcli/ui.py` - Questionary interactive prompts
- `src/tarotcli/cli.py` - Typer CLI commands
- `src/tarotcli/default.yaml` - Bundled default configuration
- `data/tarot_cards_RW.jsonl` - 78-card Rider-Waite dataset

## Configuration System (Milestone 3.5)

**Three-tier configuration hierarchy:**

1. **Environment variables** (highest priority)
   - `TAROTCLI_*` prefix for config overrides
   - API keys: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `OPENROUTER_API_KEY`
   - Example: `TAROTCLI_MODELS_DEFAULT_PROVIDER=ollama`

2. **User config files** (middle priority)
   - `./config.yaml` (project root - for development)
   - `~/.config/tarotcli/config.yaml` (XDG standard - for installed package)

3. **Bundled defaults** (fallback)
   - `src/tarotcli/default.yaml` (versioned with package)

**Usage:**
```python
from tarotcli.config import get_config

config = get_config()
provider = config.get("models.default_provider")  # "claude"
model_config = config.get_model_config("ollama")  # Full provider config
api_key = config.get_api_key("claude")  # ANTHROPIC_API_KEY from env
```

**Supported providers:**
- `claude`: Anthropic Claude (cloud, requires `ANTHROPIC_API_KEY`)
- `ollama`: Local inference via Ollama (no API key needed)
- `openai`: OpenAI (cloud, requires `OPENAI_API_KEY`)
- `openrouter`: OpenRouter (cloud, requires `OPENROUTER_API_KEY`)

**Example config.yaml:**
```yaml
models:
    default_provider: "ollama"
    providers:
        ollama:
            model: "ollama_chat/deepseek-r1:8b"
            api_base: "http://localhost:11434"
            temperature: 0.8
            max_tokens: 1500
```

**See:** `config.example.yaml` for complete configuration template.

## AI Integration (Milestone 3)

### Architecture

**LiteLLM + Multi-provider support:**
- Async implementation via `acompletion()` (future-proofed for web API)
- Sync wrapper `interpret_reading_sync()` for CLI usage
- Configuration-driven: Provider and model selection via config system
- Supports Claude (cloud), Ollama (local), OpenAI, OpenRouter

**Graceful Degradation Pattern:**
```python
# Check for API key before attempting call (config-driven)
api_key = config.get_api_key(provider)
if not api_key and provider != "ollama":
    return reading.baseline_interpretation

try:
    response = await acompletion(...)
    return interpretation
except asyncio.TimeoutError:
    return reading.baseline_interpretation  # Never fail
except Exception:
    return reading.baseline_interpretation  # Always return valid result
```

**Key principle**: Readings ALWAYS complete. AI is enhancement, not requirement.

### The Differentiator: Waite Imagery Descriptions

**What makes this authentic vs generic AI tarot:**

The dataset includes A.E. Waite's 1911 imagery descriptions (~1,600 chars per card):

```json
{
  "name": "The Magician",
  "upright_meaning": "Skill, diplomacy, address...",    // ~140 chars
  "description": "A youthful figure in the robe of a magician, having the
                  countenance of divine Apollo..."      // ~1,600 chars
}
```

**AI prompt includes BOTH**:
- `description`: Waite's symbolic analysis of card imagery
- `upright_meaning`/`reversed_meaning`: Traditional interpretation

**Result**: AI synthesizes authoritative 1911 source material, not generic training data.

**Prompt size**: ~4,300 chars for 3-card reading, ~12,000 chars for Celtic Cross (10 cards)

### Focus Area Contexts

AI prompt includes tailored framing for each `FocusArea`:
- **Career**: Professional development, decision-making guidance
- **Relationships**: Interpersonal dynamics, emotional connections
- **Personal Growth**: Self-development, inner work
- **Spiritual**: Consciousness exploration, higher purpose
- **General**: Holistic life guidance

### Testing AI Integration

**Unit tests** (100% coverage, no real API calls):
```bash
pytest tests/test_ai.py -v                    # 20 tests, all mocked
pytest tests/test_ai.py --cov=tarotcli.ai     # 100% coverage
```

**Manual validation** (requires API key):
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python examples/demo_ai_interpretation.py     # End-to-end validation

# Debug mode: See actual prompt sent to AI
DEBUG_PROMPT=1 python examples/demo_ai_interpretation.py

# Compare Claude vs Ollama with identical reading
python examples/demo_ai_comparison.py
```

Debug mode shows full 4,300-char prompt including Waite imagery descriptions.

### Error Handling

**All error paths return baseline interpretation:**
- Missing API key → immediate return (no API attempt)
- Timeout → catch `asyncio.TimeoutError`
- API error → catch generic `Exception`
- None content → explicit check before return

**No exceptions propagate to user** - readings never fail.

## Testing Workflow

1. Write test for new functionality FIRST
2. Implement functionality until test passes
3. Run full test suite to verify no regressions
4. Check coverage: `pytest --cov=tarotcli`
5. Only commit when all tests pass

## Git Workflow

**Commit Format:** Conventional Commits
- `feat(scope):` New feature
- `fix(scope):` Bug fix
- `test(scope):` Adding/updating tests
- `docs:` Documentation only
- `refactor(scope):` Code change that neither fixes bug nor adds feature

**Milestone Tagging:**
- Tag each completed milestone: `git tag -a v0.1.0 -m "Milestone 1: Core Deck Operations"`
- Push tags: `git push origin --tags`

## Important Notes

- **Dataset integrity**: `data/tarot_cards_RW.jsonl` contains 78 complete cards with essential fields from A.E. Waite's *The Pictorial Key to the Tarot* (1911). Dataset matches ekelen's tarot-api source structure. Do not regenerate or modify.
- **Graceful degradation**: Any function that calls LLM must catch all exceptions and return baseline interpretation. Readings NEVER fail.
- **No premature optimization**: Implement according to blueprint, resist feature additions until milestone complete.

## Repository Structure

```
src/tarotcli/ # Package source
tests/ # Test suite
data/ # Dataset (read-only)
docs/private/ # Personal docs (gitignored, symlinked to Obsidian)
examples/ # Usage examples
```

Private documentation (blueprints, personal notes) lives in Obsidian vault, symlinked to `docs/private/tarotCLI/`.

---

## Core Files

- `src/tarotcli/models.py` - Pydantic data models (Card, DrawnCard, Reading, FocusArea)
- `src/tarotcli/deck.py` - Deck operations (load 78 cards from JSONL, shuffle, draw)
- `src/tarotcli/spreads.py` - Spread layouts (single, three-card, Celtic Cross)
- `src/tarotcli/ai.py` - LLM API integration via LiteLLM (graceful degradation)
- `src/tarotcli/config.py` - Configuration management system (Milestone 3.5)
- `src/tarotcli/ui.py` - **NEW** - Questionary interactive prompts (Milestone 4)
- `src/tarotcli/cli.py` - **NEW** - Typer CLI commands + main entry point (Milestone 4)
- `src/tarotcli/default.yaml` - Bundled default configuration
- `data/tarot_cards_RW.jsonl` - 78-card Rider-Waite dataset

## Configuration System (Milestone 3.5)

**Three-tier configuration hierarchy:**

1. **Environment variables** (highest priority)
   - `TAROTCLI_*` prefix for config overrides
   - API keys: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `OPENROUTER_API_KEY`
   - Example: `TAROTCLI_MODELS_DEFAULT_PROVIDER=ollama`

2. **User config files** (middle priority)
   - `./config.yaml` (project root - for development)
   - `~/.config/tarotcli/config.yaml` (XDG standard - for installed package)

3. **Bundled defaults** (fallback)
   - `src/tarotcli/default.yaml` (versioned with package)

## Testing Workflow

Current test suite: **86/86 tests passing (100% pass rate, 94%+ overall coverage)**
- `tests/test_deck.py`: 11 tests (87% deck.py coverage) ✅
- `tests/test_spreads.py`: 10 tests (100% spreads.py coverage) ✅
- `tests/test_config.py`: 33 tests (99% config.py coverage) ✅
- `tests/test_ai.py`: 20 tests (100% ai.py coverage) ✅
- `tests/test_cli.py`: **NEW 12 tests** (100% cli.py coverage) ✅

**Testing Strategy:**
1. Write test for new functionality FIRST
2. Implement functionality until test passes
3. Run full test suite to verify no regressions
4. Check coverage: `pytest --cov=tarotcli`
5. Only commit when all tests pass
---

## Outstanding Issues & Future Work

### Current Known Issues

**Ollama Timeout Issue** (v0.4.0):
- LiteLLM APIConnectionError with long prompts (~4,300 chars) on current setup
- Simple prompts work fine, full tarot prompts timeout after 30s
- Needs testing on alternate machine to determine if environment-specific
- Workaround: Claude and other providers work perfectly, graceful degradation to baseline

### Future Milestones

**Milestone 4.1 - Ollama Reliability**:
- Resolve timeout issues with long prompts
- Optimize prompt size or increase timeout configuration
- Test on multiple development environments

**Milestone 5 - Reading Persistence** (v0.5.0) - **NEXT**:
- Save readings to user-specified directory
- Multiple output formats: JSON, markdown, plain text
- Reading history and retrieval functionality
- README promises this feature - needs implementation

**Milestone 6 - Advanced CLI Features** (v0.6.0):
- Advanced visualization of cards and spreads
- Reading export formats (HTML, PDF)
- Statistical analysis of reading patterns

---

## Repository Structure

```
src/tarotcli/ # Package source
tests/ # Test suite (86/86 tests passing)
data/ # Dataset (read-only)
docs/ # Documentation
examples/ # Usage examples
scripts/ # Development utils
```

---

## CLI Usage Examples (v0.4.0)

**Interactive Mode:**
```bash
tarotcli read
# Prompts for: spread type ➜ focus area ➜ question ➜ AI preference
```

**CLI Arguments Mode:**
```bash
# Quick reading with baseline interpretation
tarotcli read --spread single --focus general --no-ai

# Full AI reading with specific question
tarotcli read --spread three --focus career --question "Should I change jobs?" --provider claude

# JSON output for automation
tarotcli read --spread celtic --focus relationships --json

# Configuration checks
tarotcli config-info          # Show current setup
tarotcli list-spreads         # Available spread types
tarotcli version              # Current version
```

**Provider Override Examples:**
```bash
# Test different AI providers
tarotcli read --spread three --focus spiritual --provider ollama    # Local inference
tarotcli read --spread three --focus spiritual --provider claude    # Claude (cloud)
tarotcli read --spread three --focus spiritual --provider openai    # OpenAI (cloud)
```
