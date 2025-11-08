# TarotCLI - Development Agent Context

## Project Overview

**Purpose**: Minimalist tarot reading CLI with optional AI interpretation. Foundation-first architecture ensuring core functionality works reliably without LLM dependency.

**Current Status**: v0.4.0 (Milestone 4 Complete)
- **Test Coverage**: 94% overall (86/86 tests passing)
- **Production Ready**: CLI fully functional with interactive and argument modes
- **Multi-Provider Support**: Claude, Ollama (local), OpenAI, OpenRouter

**Key Achievement**: Professional Python CLI demonstrating scope discipline, test-driven development, and graceful degradation patterns. Portfolio piece showcasing ability to ship working MVP without overengineering.

---

## Project Scope

### In Scope (Current Implementation)

**Core Functionality**:
- 78-card Rider-Waite-Smith deck with authoritative 1911 Waite imagery descriptions
- Three spread types: Single Card, Three Card (Past/Present/Future), Celtic Cross (10 cards)
- Multi-provider AI interpretation (Claude, Ollama, OpenAI, OpenRouter)
- Baseline interpretation (static card meanings, works offline)
- Interactive CLI (questionary prompts) and argument mode
- Three-tier configuration (environment → user config → bundled defaults)
- JSON and markdown output formats
- Graceful degradation (readings never fail)

**Development Standards**:
- Foundation-first methodology (each milestone proven before next)
- Comprehensive test coverage (target >90%)
- Google-style docstrings throughout
- Conventional commits and milestone tagging
- Type safety with Pydantic models

### Out of Scope (Explicitly Excluded)

**Features NOT being added**:
- Reading history persistence/retrieval (database, search, filtering)
- Statistical analysis or pattern recognition
- Multiple tarot decks (Thoth, Marseille, etc.)
- Astrological integration
- Golden Dawn correspondences
- Image generation or visualization
- Web UI or API server
- Voice interface
- RAG/vector search/embeddings

**Rationale**: Previous version (371 commits) abandoned due to scope creep. Current version demonstrates ability to ship working MVP and maintain focus.

### Future Minimal Additions (Post v1.0)

**Milestone 5 - Reading Export** (v0.5.0):
- Save readings to configurable directory
- Timestamped filenames (e.g., `reading_2025-11-07_14-30-22.md`)
- Markdown and JSON formats
- **NOT a database** - simple file export only
- No retrieval, search, or history management

**Card Imagery Toggle** (v0.6.0):
- CLI flag: `--show-imagery` to include Waite's 1911 descriptions in output
- User sees both symbolic imagery analysis AND traditional meanings
- Helps users understand how AI synthesizes card interpretations
- Preserves minimalist default (effective meanings only)

---

## Architecture & Principles

### Foundation-First Development

**Methodology**:
1. Core deck operations (load, shuffle, draw) - NO LLM dependency
2. Spread layouts with baseline interpretation (works offline)
3. AI integration with graceful degradation (enhancement, not requirement)
4. Interactive CLI polish (UX layer on proven foundation)

**Critical Rule**: Each milestone must work perfectly before proceeding to next. No feature additions from future milestones until current milestone complete and tested.

### Graceful Degradation Pattern

**Philosophy**: Readings ALWAYS complete successfully. AI interpretation is enhancement, not requirement.

**Implementation**:
```python
# Check preconditions before attempting API call
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

**No exceptions propagate to user** - all error paths return valid baseline interpretation.

---

## Core Components

### Module Responsibilities

**src/tarotcli/models.py** (100% coverage):
- Pydantic data models: `Card`, `DrawnCard`, `Reading`, `FocusArea`
- Type-safe data structures with validation
- JSON serialization for output formats

**src/tarotcli/deck.py** (87% coverage):
- Load 78 cards from JSONL dataset
- Shuffle with optional seed (reproducible testing)
- Draw N cards without replacement
- Static method `load_default()` uses config system

**src/tarotcli/spreads.py** (100% coverage):
- Spread layout definitions (single, three, celtic)
- Position meaning assignment
- Baseline interpretation generation from card meanings
- Registry pattern: `get_spread(name)` factory function

**src/tarotcli/ai.py** (100% coverage):
- LiteLLM integration (async implementation)
- Multi-provider support (Claude, Ollama, OpenAI, OpenRouter)
- Waite imagery descriptions in prompts (~4,300 chars for 3-card reading)
- Focus area contexts (career, relationships, personal growth, spiritual, general)
- Graceful degradation on all error paths
- Sync wrapper `interpret_reading_sync()` for CLI usage

**src/tarotcli/config.py** (99% coverage):
- Three-tier configuration hierarchy
- Singleton pattern with lazy loading
- Provider-specific model configs
- API key management (environment only)
- Path handling (data directory, XDG compliance)

**src/tarotcli/ui.py** (95% coverage):
- Questionary interactive prompts
- Spread selection with descriptions
- Focus area choice with context
- Optional question input
- AI preference prompt (shows configured provider)
- Formatted reading display with ASCII borders

**src/tarotcli/cli.py** (100% coverage):
- Typer-based command interface
- Commands: `read`, `version`, `list-spreads`, `config-info`
- Interactive and argument modes
- Provider override support
- JSON/markdown output formats
- Error handling with helpful messages

**data/tarot_cards_RW.jsonl** (read-only):
- 78 complete cards from A.E. Waite's *The Pictorial Key to the Tarot* (1911)
- Authoritative source - do not regenerate or modify
- Fields: name, arcana, suit, value, upright_meaning, reversed_meaning, description, img

---

## Configuration System

### Three-Tier Hierarchy

**1. Environment Variables** (highest priority):
```bash
# Config overrides
TAROTCLI_MODELS_DEFAULT_PROVIDER=ollama
TAROTCLI_MODELS_PROVIDERS_CLAUDE_TEMPERATURE=0.9

# API keys (security: never in YAML files)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
OPENROUTER_API_KEY=sk-or-...
```

**2. User Config Files** (middle priority):
```yaml
# ./config.yaml (project root - development)
# ~/.config/tarotcli/config.yaml (XDG standard - installed package)

models:
    default_provider: "ollama"
    providers:
        ollama:
            model: "ollama_chat/deepseek-r1:8b"
            api_base: "http://localhost:11434"
            temperature: 0.8
            max_tokens: 1500
        claude:
            model: "claude-sonnet-4-20250514"
            temperature: 0.7
            max_tokens: 2000
```

**3. Bundled Defaults** (fallback):
- `src/tarotcli/default.yaml` (versioned with package)
- Ensures application works without any user configuration

### Supported AI Providers

**claude** (Anthropic):
- Cloud API, requires `ANTHROPIC_API_KEY`
- Default model: `claude-sonnet-4-20250514`
- Best quality interpretations

**ollama** (Local):
- Local inference, no API key needed
- Requires Ollama server running (`ollama serve`)
- Model example: `ollama_chat/deepseek-r1:8b`
- Hardware-dependent performance (8B param models need decent GPU)

**openai** (OpenAI):
- Cloud API, requires `OPENAI_API_KEY`
- Model example: `gpt-4`

**openrouter** (OpenRouter):
- Cloud aggregator, requires `OPENROUTER_API_KEY`
- Access to multiple model providers

### Configuration Usage

```python
from tarotcli.config import get_config

config = get_config()
provider = config.get("models.default_provider")  # "claude"
model_config = config.get_model_config("ollama")  # Full provider config
api_key = config.get_api_key("claude")  # ANTHROPIC_API_KEY from env
data_path = config.get_data_path("tarot_cards_RW.jsonl")  # Path to dataset
```

---

## AI Integration

### The Differentiator: Waite Imagery Descriptions

**What makes this authentic vs generic AI tarot**:

Dataset includes A.E. Waite's 1911 imagery descriptions (~1,600 chars per card) alongside traditional meanings (~140 chars). AI prompt includes **both** description (symbolic analysis) and meanings (interpretation keywords).

**Example from dataset**:
```json
{
  "name": "The Magician",
  "upright_meaning": "Skill, diplomacy, address, subtlety...",
  "description": "A youthful figure in the robe of a magician, having the 
                  countenance of divine Apollo, with smile of confidence and 
                  shining eyes. Above his head is the mysterious sign of the 
                  Holy Spirit, the sign of life, like an endless cord, forming 
                  the figure 8 in a horizontal position..."
}
```

**Result**: AI synthesizes authoritative 1911 source material, not generic training data. Interpretations reference actual card symbolism (white robe, red cloak, garden roses) rather than abstract meanings.

**Prompt size**: 
- 3-card reading: ~4,300 chars
- Celtic Cross (10 cards): ~12,000 chars

### Focus Area Contexts

AI prompt includes tailored framing for each `FocusArea`:
- **Career**: Professional development, decision-making, workplace dynamics
- **Relationships**: Interpersonal connections, emotional patterns, communication
- **Personal Growth**: Self-development, inner work, behavioral patterns
- **Spiritual**: Consciousness exploration, higher purpose, existential questions
- **General**: Holistic life guidance without specific domain focus

### LiteLLM Integration

**Async implementation** (future-proofed for web API):
```python
async def interpret_reading(
    reading: Reading,
    provider: str | None = None
) -> str:
    """Generate AI interpretation or return baseline on any error."""
    # Config-driven provider selection
    # Graceful degradation on all error paths
    # Always returns valid interpretation
```

**Sync wrapper for CLI**:
```python
def interpret_reading_sync(
    reading: Reading,
    provider: str | None = None
) -> str:
    """Synchronous wrapper using asyncio.run()."""
    return asyncio.run(interpret_reading(reading, provider))
```

---

## Dataset & Sample Data

### Rider-Waite-Smith Tarot Deck

**Source**: A.E. Waite's *The Pictorial Key to the Tarot* (1911)
**Format**: JSONL (JSON Lines) - one card per line
**Total Cards**: 78 (22 Major Arcana + 56 Minor Arcana)

### Sample Card Entries

**Major Arcana Example**:
```json
{
  "name": "The Fool",
  "arcana": "Major Arcana",
  "suit": null,
  "value": 0,
  "upright_meaning": "Folly, mania, extravagance, intoxication, delirium, frenzy, bewrayment.",
  "reversed_meaning": "Negligence, absence, distribution, carelessness, apathy, nullity, vanity.",
  "description": "With light step, as if earth and its trammels had little power to restrain him, a young man in gorgeous vestments pauses at the brink of a precipice among the great heights of the world; he surveys the blue distance before him-its expanse of sky rather than the prospect below. His act of eager walking is still indicated, though he is stationary at the given moment; his dog is still bounding. The edge which opens on the depth has no terror; it is as if angels were waiting to uphold him, if it came about that he leaped from the height. His countenance is full of intelligence and expectant dream. He has a rose in one hand and in the other a costly wand, from which depends over his right shoulder a wallet curiously embroidered. He is a prince of the other world on his travels through this one-all amidst the morning glory, in the keen air. The sun, which shines behind him, knows whence he came, whither he is going, and how he will return by another path after many days.",
  "img": "https://sacred-texts.com/tarot/pkt/img/ar00.jpg"
}
```

**Minor Arcana Example**:
```json
{
  "name": "Seven of Cups",
  "arcana": "Minor Arcana",
  "suit": "Cups",
  "value": 7,
  "upright_meaning": "Fairy favours, images of reflection, sentiment, imagination, things seen in the glass of contemplation; some attainment in these degrees, but nothing permanent or substantial is suggested.",
  "reversed_meaning": "Desire, will, determination, project.",
  "description": "Strange chalices of vision, but the images are more especially those of the fantastic spirit. There is a draped figure looking at these cups, or rather at the images which they reflect in the manner of a mirror. On one is the figure of a man, on another a woman, on a third the form of a bird, and on the fourth is a monster with three heads. The fifth has a house, the sixth a wreath of jewels, and the seventh is veiled, but shows the semblance of a face.",
  "img": "https://sacred-texts.com/tarot/pkt/img/cu07.jpg"
}
```

### Field Definitions

- **name**: Card title (e.g., "The Magician", "Seven of Cups")
- **arcana**: "Major Arcana" or "Minor Arcana"
- **suit**: null for Major Arcana, "Wands"/"Cups"/"Swords"/"Pentacles" for Minor
- **value**: 0-21 for Major, 1-10 for Minor (Page=11, Knight=12, Queen=13, King=14)
- **upright_meaning**: Traditional interpretation (~140 chars)
- **reversed_meaning**: Inverted card meaning (~140 chars)
- **description**: Waite's 1911 imagery analysis (~1,600 chars) - **the differentiator**
- **img**: URL to card artwork from sacred-texts.com

---

## Development Standards

### Code Style

**Type Safety**:
- Pydantic v2 models for all data structures
- Type hints on all function signatures
- Use `str | None` syntax (not `Optional[str]`)
- Strict validation at data boundaries

**Docstrings**:
```python
def function_name(arg1: str, arg2: int) -> dict:
    """Short description in imperative mood.
    
    Longer explanation with architectural context and rationale.
    
    Args:
        arg1: Description of first argument.
        arg2: Description of second argument.
    
    Returns:
        Description of return value and structure.
    
    Raises:
        ErrorType: When this specific error occurs.
    
    Example:
        >>> result = function_name("value", 42)
        >>> print(result)
        {'key': 'value'}
    
    Notes:
        - Foundation-first principle: Why this approach scales
        - Technical consideration: Edge case handling
    """
```

**Error Handling**:
- All functions that could fail must handle errors gracefully
- LLM functions return baseline on any error (never raise)
- Use descriptive error messages with actionable guidance
- Log errors for debugging, display user-friendly messages

### Testing Requirements

**Current Coverage**: 94% overall (86/86 tests passing)
- ai.py: 100% ✅
- models.py: 100% ✅
- spreads.py: 100% ✅
- config.py: 99% ✅
- cli.py: 100% ✅
- ui.py: 95% ✅
- deck.py: 87% ⚠️ (error paths not fully tested, acceptable)

**Testing Strategy**:
1. Write test for new functionality FIRST
2. Implement functionality until test passes
3. Run full test suite to verify no regressions
4. Check coverage: `pytest --cov=tarotcli`
5. Only commit when all tests pass

**Test Organization**:
- `tests/test_deck.py`: Deck operations (11 tests)
- `tests/test_spreads.py`: Spread layouts (10 tests)
- `tests/test_config.py`: Configuration system (33 tests)
- `tests/test_ai.py`: AI integration (20 tests, all mocked)
- `tests/test_cli.py`: CLI commands (12 tests, CliRunner)
- `tests/conftest.py`: Shared fixtures

**Mocking Standards**:
- Mock external APIs (LiteLLM) - no real calls in unit tests
- Mock questionary prompts in CLI tests
- Use pytest fixtures for complex setup
- Isolate tests from user config files

### Git Workflow

**Commit Format** (Conventional Commits):
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types**:
- `feat(scope):` New feature
- `fix(scope):` Bug fix
- `test(scope):` Adding/updating tests
- `docs:` Documentation only
- `refactor(scope):` Code change that neither fixes bug nor adds feature
- `chore:` Maintenance tasks

**Examples**:
```bash
feat(cli): Add interactive reading flow with questionary prompts
test(ai): Add comprehensive mocking for multi-provider support
docs: Update AGENTS.md with dataset sample entries
fix(config): Handle missing user config file gracefully
```

**Milestone Tagging**:
```bash
git tag -a v0.4.0 -m "Milestone 4: Interactive CLI"
git push origin v0.4.0
```

**5-Minute Rule**: If spending >5 minutes on commit strategy, just commit. Perfect is enemy of shipped.

---

## Completed Milestones

### Milestone 1 (v0.1.0) - Core Deck Operations ✅

**Deliverables**:
- Load 78 cards from JSONL dataset
- Shuffle deck (with optional seed for testing)
- Draw N cards without replacement
- Type-safe Card and Deck models

**Acceptance Criteria**:
- `TarotDeck` class with `load()`, `shuffle()`, `draw()` methods
- All 78 cards load correctly with complete data
- Drawing removes cards from available pool
- Reproducible shuffles via seed parameter
- 11 tests passing with 87% coverage

### Milestone 2 (v0.2.0) - Spread Layouts ✅

**Deliverables**:
- Three spread types: single, three, celtic
- Position meaning assignment
- Baseline interpretation from card meanings
- Reversed card handling

**Acceptance Criteria**:
- `Spread` classes for each layout
- `DrawnCard` model with position and reversal
- `Reading` model with baseline interpretation
- Works completely offline (no AI dependency)
- 10 tests passing with 100% coverage

### Milestone 3 (v0.3.0) - AI Integration ✅

**Deliverables**:
- LiteLLM async integration
- Waite imagery descriptions in prompts
- Focus area contexts
- Graceful degradation pattern
- Sync wrapper for CLI usage

**Acceptance Criteria**:
- AI interpretation enhances readings without breaking offline mode
- All error paths return baseline interpretation
- No exceptions propagate to user
- Prompt includes both imagery and meanings
- 20 tests passing with 100% coverage (all mocked)

### Milestone 3.5 (v0.3.5) - Configuration System ✅

**Deliverables**:
- Three-tier config hierarchy (env → user → defaults)
- Multi-provider support (Claude, Ollama, OpenAI, OpenRouter)
- API key management (environment only)
- XDG-compliant user config directory

**Acceptance Criteria**:
- Config singleton with lazy loading
- Provider switching via single config line
- Environment variables override file config
- Bundled defaults ensure zero-config functionality
- 33 tests passing with 99% coverage

### Milestone 4 (v0.4.0) - Interactive CLI ✅

**Deliverables**:
- Typer-based command interface
- Questionary interactive prompts
- Multiple output formats (markdown, JSON)
- Provider override via CLI flag
- Comprehensive help and error messages

**Acceptance Criteria**:
- `tarotcli read` works interactively and with arguments
- Commands: `version`, `list-spreads`, `config-info`
- JSON output for automation/scripting
- Graceful error handling with helpful guidance
- 12 CLI tests passing with 100% coverage

---

## Future Work

### Known Issues

**Ollama Timeout with Long Prompts**:
- Issue: LiteLLM APIConnectionError with full tarot prompts (~4,300 chars)
- Environment: P71 Thinkpad with P5000 GPU (5GB VRAM)
- Resolution: Works perfectly on 3080 GPU (10GB VRAM)
- Assessment: Hardware constraint, not code issue
- Workaround: Use Claude or smaller Ollama models; baseline always works

---

### Milestone 4.5 (v0.4.5) - Card Lookup **[PRIORITY 1]**

**Scope**:
- CLI command: `tarotcli lookup <card_name>`
- Fuzzy name matching (case-insensitive, partial matches)
- Display both upright and reversed meanings
- Optional `--show-imagery` flag includes Waite's 1911 descriptions
- Educational resource for physical deck practice

**Rationale**: Positions tarotcli as both programmatic divination tool AND tarot learning resource. Immediate utility for users practicing with physical decks who want authoritative Waite meanings instead of SEO-optimized interpretations.

**Explicitly NOT included**:
- Multi-card reading mode (defer to observe usage patterns)
- Spread layout for physical readings (Phase 2 consideration)
- History of looked-up cards

**Acceptance Criteria**:
- `tarotcli lookup "ace of wands"` displays both orientations
- Fuzzy matching handles typos and partial names
- `--show-imagery` includes Waite's imagery descriptions
- Graceful error handling for not found
- 5+ tests covering match scenarios
- Documentation updated with usage examples

**Estimated effort**: 2 hours (1 hour implementation, 1 hour testing)

---

### Milestone 5 (v0.5.0) - Reading Export **[PRIORITY 2]**

**Scope**:
- Save readings to configurable directory
- Timestamped filenames: `reading_2025-11-07_14-30-22.md`
- Markdown and JSON formats
- Config option: `output.readings_directory` (default: `~/tarot_readings/`)

**Explicitly NOT included**:
- Database persistence
- Reading history retrieval
- Search or filtering functionality
- Statistics or pattern analysis

**Acceptance Criteria**:
- `tarotcli read --save` writes file to configured directory
- Filename includes timestamp for uniqueness
- Markdown format includes formatted card display
- JSON format matches `reading.model_dump_json()` structure
- User can specify custom directory via config or CLI flag

**Estimated effort**: 2-3 hours (1 hour implementation, 1 hour testing, 30 min docs)

---

### Card Imagery Toggle (v0.6.0)

**Scope**:
- CLI flag: `--show-imagery` includes Waite descriptions in output
- Default behavior unchanged (effective meanings only)
- Helps users understand AI's symbolic synthesis
- Educational feature for tarot learning

**Explicitly NOT included**:
- Generating new imagery descriptions
- Image display (text descriptions only)
- Imagery-based search or filtering

**Implementation**:
```bash
# Default (current behavior)
tarotcli read --spread three

# With imagery descriptions
tarotcli read --spread three --show-imagery
```

**Output difference**:
```
Default:
  Past: The Magician ↑ Upright
  Meaning: Skill, diplomacy, address, subtlety

With --show-imagery:
  Past: The Magician ↑ Upright
  Meaning: Skill, diplomacy, address, subtlety
  Imagery: A youthful figure in the robe of a magician, having the 
           countenance of divine Apollo, with smile of confidence...
```

**Acceptance Criteria**:
- `tarotcli read --show-imagery` includes descriptions in reading display
- `tarotcli lookup "card" --show-imagery` shows imagery for single card
- Config option to make imagery default: `display.show_imagery: true`
- Preserves minimalist default display
- Documentation explains Waite description source

**Estimated effort**: 1 hour (flag already exists in lookup, extend to read command)

---

## Usage Examples

### Interactive Mode
```bash
# Launch interactive prompts (recommended)
tarotcli read

# Output:
# 🔮 TarotCLI - Interactive Reading
#
# Select spread type:
#   › Three Card - Past, Present, Future (3 cards)
#     Celtic Cross - Comprehensive life situation (10 cards)
#     Single Card - Direct guidance (1 card)
```

### CLI Arguments Mode
```bash
# Quick reading with baseline only
tarotcli read --spread single --focus general --no-ai

# Full AI reading with specific question
tarotcli read --spread three --focus career \
  --question "Should I change jobs?"

# Provider override (test different models)
tarotcli read --spread three --focus spiritual --provider ollama

# JSON output for automation
tarotcli read --spread celtic --focus relationships --json > reading.json
```

### Information Commands
```bash
# Show current configuration
tarotcli config-info
# Output:
# 🔮 TarotCLI Configuration
#   Default Provider: claude
#   Model: claude-sonnet-4-20250514
#   Data Path: /path/to/data/tarot_cards_RW.jsonl

# List available spreads
tarotcli list-spreads
# Output:
# Available Spreads:
#   single       - Single Card (1 card)
#                  Direct guidance for specific question
#   three        - Three Card (3 cards)
#                  Past, Present, Future analysis
#   celtic       - Celtic Cross (10 cards)
#                  Comprehensive life situation examination

# Check version
tarotcli version
# Output: TarotCLI version 0.4.0
```

### Development Commands
```bash
# Install package in editable mode
uv pip install -e '.[dev]'

# Run full test suite
pytest

# Run specific test module
pytest tests/test_cli.py -v

# Check test coverage
pytest --cov=tarotcli --cov-report=html

# Format code before commit
ruff format src/ tests/

# Run CLI directly from source
python -m tarotcli read
```

---

## Quick Reference

**Project Structure**:
```
tarotcli/
├── src/tarotcli/        # Package source
│   ├── models.py        # Pydantic data models
│   ├── deck.py          # Deck operations
│   ├── spreads.py       # Spread layouts
│   ├── ai.py            # LLM integration
│   ├── config.py        # Configuration system
│   ├── ui.py            # Interactive prompts
│   ├── cli.py           # CLI commands
│   └── default.yaml     # Bundled config
├── tests/               # Test suite (86 tests)
├── data/                # Tarot dataset (read-only)
├── examples/            # Usage demonstrations
├── docs/                # Documentation
├── pyproject.toml       # Package metadata
└── README.md            # User documentation
```

**Key Files**:
- `src/tarotcli/cli.py`: Entry point (`tarotcli` command)
- `data/tarot_cards_RW.jsonl`: 78-card dataset (authoritative source)
- `src/tarotcli/default.yaml`: Bundled configuration defaults
- `config.example.yaml`: User configuration template
- `.env.example`: API key template

**Documentation**:
- `AGENTS.md`: This file (development context)
- `README.md`: User-facing documentation
- `docs/private/`: Session journals (Obsidian vault)

---

**Last Updated**: November 7, 2025 (v0.4.0)
**Maintainer**: melbourne-quantum-dev
**Repository**: Foundation-first development, professional git hygiene, comprehensive testing
