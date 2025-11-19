# TarotCLI - Development Agent Context

## Project Overview

**Purpose**: Minimalist tarot reading CLI with optional AI interpretation. Foundation-first architecture ensuring core functionality works reliably without LLM dependency.

**Current Status**: v0.5.0 (Milestone 5 Complete)
- **Test Coverage**: Coverage is at 83% overall (120/120 passing). The low coverage areas are expected: `ui.py` at 23% (interactive prompts), `cli.py` at 78% (some command paths untested).
- **Production Ready**: CLI fully functional with interactive and argument modes
- **Multi-Provider Support**: Claude, Ollama (local), OpenAI, OpenRouter
- **Reading Persistence**: Auto-save readings to JSONL storage, view history
- **Cross-Platform**: Uses platformdirs for proper config/data paths on Linux, macOS, Windows

**Key Achievement**: Professional Python CLI demonstrating scope discipline, test-driven development, and graceful degradation patterns. Portfolio piece showcasing ability to ship working MVP without overengineering.

---

## Project Scope

### In Scope (Current Implementation)

**Core Functionality**:
- 78-card Rider-Waite-Smith deck with authoritative 1911 Waite imagery descriptions
- Three spread types: Single Card, Three Card (Past/Present/Future), Celtic Cross (10 cards)
- Multi-provider AI interpretation (Claude, Ollama, OpenAI, OpenRouter)
- Static interpretation (non-AI card meanings, works offline)
- Interactive CLI (questionary prompts) and argument mode
- Three-tier configuration (environment → user config → bundled defaults)
- Cross-platform support (platformdirs for Linux, macOS, Windows compatibility)
- JSON and markdown output formats
- Graceful degradation (readings never fail)
- Lightweight reading persistence (JSONL append-only storage)
- Reading history retrieval (`tarotcli history` command)

**Development Standards**:
- Foundation-first methodology (each milestone proven before next)
- Comprehensive test coverage (target >90%)
- Google-style docstrings throughout
- Conventional commits and milestone tagging
- Type safety with Pydantic models

### Out of Scope (Explicitly Excluded)

**Features NOT being added**:
- Database persistence (file-based JSONL storage only)
- Advanced search or filtering (basic history retrieval only)
- Statistical analysis or pattern recognition
- Multiple tarot decks (Thoth, Marseille, etc.)
- Astrological integration
- Golden Dawn correspondences
- Image generation or visualization
- Web UI or API server
- Voice interface
- RAG/vector search/embeddings

**Rationale**: Previous version (371 commits) abandoned due to scope creep. Current version demonstrates ability to ship working MVP and maintain focus. Persistence is being added in Milestone 5 but kept minimal (JSONL files, no database complexity).

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

**src/tarotcli/deck.py** (93% coverage):
- Load 78 cards from JSONL dataset
- Shuffle with optional seed (reproducible testing)
- Draw N cards without replacement
- Static method `load_default()` uses config system
- `lookup_card()` function provides card reference functionality

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

**src/tarotcli/ui.py** (23% coverage):
- Questionary interactive prompts
- Spread selection with descriptions
- Focus area choice with context
- Optional question input
- AI preference prompt (shows configured provider)
- Formatted reading display with ASCII borders
- Note: Lower coverage expected for interactive UI components

**src/tarotcli/cli.py** (96% coverage):
- Typer-based command interface
- Commands: `read`, `lookup`, `version`, `list-spreads`, `config-info`
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

### Hermeneutical Layers: What "Interpretation" Means

**Terminology Problem**: Both `interpretation` and `static_interpretation` fields use "interpretation" in their names, which can mislead developers about what the AI actually does.

**The Three-Layer Framework**:

1. **Waite's Source Material (1911)** - Primary Interpretation Layer
   - A.E. Waite's *Pictorial Key to the Tarot* interprets RWS deck symbolism
   - Provides traditional divinatory meanings for each card
   - This is already **interpretation** - Waite interpreted the symbolic imagery
   - Our dataset (`tarot_cards_RW.jsonl`) preserves these authoritative 1911 interpretations

2. **Static Interpretation** (`static_interpretation` field) - Structured Presentation
   - Assembles Waite's pre-existing interpretations by spread position
   - **No new interpretation occurs** - just formatting and assembly
   - Example: "Past: The Magician (Upright)\nSkill, diplomacy..."
   - Think: "What Waite said about these cards, organized by reading structure"

3. **AI Synthesis** (`interpretation` field) - Hybrid Narrative Transformation
   - Draws from **both** AI training data knowledge AND Waite's source material
   - Waite material provides specific symbolic grounding (imagery, traditional meanings)
   - Training data contributes broader tarot tradition and narrative fluency
   - **Not mystical divination** - informed interpretation built from multiple knowledge sources
   - The result: Authoritative grounding + accessible narrative + traditional context

**Why This Matters**:

- ✅ **Epistemological Honesty**: AI integrates multiple sources, with Waite as authoritative grounding
- ✅ **Practical Quality**: Combination of historical source + traditional knowledge = richer interpretations
- ✅ **Educational Value**: Users can compare static (pure Waite) vs AI (hybrid synthesis) via `lookup` command
- ✅ **Architectural Flexibility**: System supports swapping/adding other source datasets (Thoth, Marseille, custom)
- ✅ **User Choice**: Three modes available (static-only, AI synthesis, comparison between both)

**Field Naming Decision**:

We maintain `interpretation` and `static_interpretation` despite ambiguity because:
- API stability (no breaking changes to field names)
- User intuitiveness (`interpretation` is what users expect to see)
- Comprehensive documentation (module docstrings, README) clarifies the distinction

The code's module-level documentation (`models.py`) and this section provide the hermeneutical framework for anyone reading the codebase.

---

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

**Documentation Language Standards**:

Use human, varied language in documentation and docstrings. Avoid repetitive AI buzzwords that make text sound machine-generated.

**Prefer varied, accessible terms**:
- "draws on" / "pulls from" / "works with" (instead of repetitive "synthesizes")
- "combines" / "integrates" / "weaves together" (natural variety)
- "informed by" / "grounded in" / "contextualizes" (academic alternatives)
- "constructs" / "builds upon" (foundation metaphors)

**Language variability principle**:
- First mention: Use most accessible term ("draws on")
- Second mention: Vary with simple alternative ("combines")
- Third mention: Academic but clear ("integrates")
- Throughout: Maintain human rhythm through synonym variation

**Why this matters**:
- Token-efficient terms like "synthesizes" repeated 5+ times sound AI-generated
- Natural writing uses varied vocabulary even for same concept
- Human readers expect rhetorical variation, not robotic consistency
- Academic writing traditionally employs elegant variation

**Apply to**:
- Module docstrings (`models.py`, `ai.py`, etc.)
- Function/class docstrings
- README.md and AGENTS.md documentation
- Help text and CLI descriptions
- Comments explaining complex logic

**Don't apply to**:
- Variable names (consistency critical)
- Function names (clarity over variety)
- Error messages (consistency aids debugging)
- Test names (explicit over elegant)

This standard maintains professional quality while sounding human-authored rather than LLM-generated.

---

**Error Handling**:
- All functions that could fail must handle errors gracefully
- LLM functions return baseline on any error (never raise)
- Use descriptive error messages with actionable guidance
- Log errors for debugging, display user-friendly messages

### Testing Requirements

**Current Coverage**: 88% overall (103/103 tests passing)
- ai.py: 100% ✅
- models.py: 100% ✅
- spreads.py: 100% ✅
- config.py: 99% ✅
- cli.py: 96% ✅
- deck.py: 93% ✅
- ui.py: 23% ⚠️ (interactive components, acceptable)

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
- `tests/test_cli.py`: CLI commands (19 tests, CliRunner)
- `tests/test_lookup.py`: Card lookup function (10 tests)
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

### Mileston 4.5 (v0.4.5) - Card Lookup ✅

**Deliverables**:
- CLI command: `tarotcli lookup <card_name>`
- Fuzzy name matching (case-insensitive, partial matches)
- Display both upright and reversed meanings
- Optional `--show-imagery` flag includes Waite's 1911 descriptions
- Educational resource for physical deck practice

**Acceptance Criteria**:
- `tarotcli lookup "ace of wands"` displays both orientations ✅
- Fuzzy matching handles typos and partial names ✅
- `--show-imagery` includes Waite's imagery descriptions ✅
- Graceful error handling for not found ✅
- 10 tests for `lookup_card()` function in deck.py ✅
- 7 tests for `lookup` CLI command in cli.py ✅
- Documentation updated with usage examples ✅

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

### Milestone 5 (v0.5.0) - Reading Persistence ✅

**Scope**:
- JSONL append-only storage for reading history
- Cross-platform paths using `platformdirs`:
  - Linux: `~/.local/share/tarotcli/readings.jsonl`
  - macOS: `~/Library/Application Support/tarotcli/readings.jsonl`
  - Windows: `C:\Users\<user>\AppData\Local\tarotcli\readings.jsonl`
- Config option: `output.save_readings` (boolean, default: `false`)
- Config option: `output.readings_dir` (path override, default: `null`)
- New command: `tarotcli history` to view past readings
- Auto-save after each reading when enabled (no extra command needed)

**Implementation Details**:
- Storage format: One reading per line (JSONL) matching `reading.model_dump_json()`
- Retrieval: Deserialize JSONL lines into `Reading` objects
- Display: Reuse existing `display_reading()` function for markdown output
- JSON option: `tarotcli history --json` for scripting/automation
- Graceful degradation: If write fails, warn and continue (never blocks readings)
- Cross-platform support: `platformdirs` for user config and data directories

**Explicitly NOT included**:
- Database persistence (just files)
- Search or filtering functionality
- Statistics or pattern analysis
- Markdown storage (JSONL only - structured and parseable)

**Deliverables (All Complete)**:
- `save_readings: true` in config enables auto-save ✅
- Platform-specific storage paths (Linux/macOS/Windows) ✅
- `tarotcli history` shows last 10 readings (markdown format) ✅
- `tarotcli history --last N` shows last N readings ✅
- `tarotcli history --json` outputs JSON array for scripting ✅
- File corruption on crash doesn't affect new writes (append-only) ✅
- Tests for `ReadingPersistence` class: 22 tests, 86% coverage ✅
- Cross-platform config paths using `platformdirs` ✅
- Updated `tarotcli config-info` to show platform-specific paths ✅
- **Privacy features**: `tarotcli clear-history` with granular deletion ✅
  - Delete last N readings: `--last N`
  - Delete all readings: `--all`
  - Confirmation prompts for all destructive operations
  - Privacy warnings in docs and config

**Actual effort**: ~4 hours (implementation, testing, docs, platformdirs, privacy features)

---

### Milestone 6 (v0.6.0) - Rich Display Enhancement **[PLANNED]**

**Scope**:
- Integrate Rich library for terminal UI improvements
- Add `--show-imagery` flag to `tarotcli read` command
- Enhance both live readings and history display with Rich formatting
- Improve text wrapping for long AI interpretations

**Phase 1: Rich Integration**:
- Replace plain `print()` with Rich Console for proper text wrapping
- Add color-coded sections (headers, cards, interpretations)
- Terminal-aware width (adapts to user's terminal size)
- Rich tables for card layout display
- Markdown rendering for AI interpretations (if Claude uses formatting)
- Panels for visual separation of sections

**Phase 2: Imagery Flag Extension**:
- CLI flag: `tarotcli read --show-imagery` includes Waite descriptions
- Config option: `display.show_imagery: true` (default: `false`)
- Display imagery in Rich panels with proper wrapping
- Extends existing `lookup --show-imagery` pattern to full readings

**Benefits**:
- Automatic text wrapping prevents interpretation overflow on narrow terminals
- Color-coding improves readability (card positions, orientations)
- Tables provide cleaner card layout than current list format
- Consistent with Rich usage in modern Python CLIs (Typer, Poetry, etc.)

**Explicitly NOT included**:
- Generating new imagery descriptions (dataset is authoritative)
- Image display (text descriptions only)
- Imagery-based search or filtering
- Breaking changes to existing output (preserve `--json` behavior)

**Implementation Preview**:
```bash
# Default (enhanced with Rich)
tarotcli read --spread three
# → Rich panels, color headers, wrapped text, tables

# With imagery descriptions
tarotcli read --spread three --show-imagery
# → All Rich enhancements + Waite imagery in card panels

# History also benefits
tarotcli history --last 3
# → Rich formatting for past readings
```

**Acceptance Criteria**:
- `rich` added to dependencies in pyproject.toml ✅
- `display_reading()` refactored to use Rich Console ✅
- Text wraps to terminal width (no more overflow) ✅
- `tarotcli read --show-imagery` includes Waite descriptions ✅
- `tarotcli history` uses Rich formatting ✅
- `--json` output unchanged (Rich only affects markdown display) ✅
- Config option `display.show_imagery` works ✅
- All existing tests pass (display logic isolated) ✅
- UI remains minimal and elegant (no over-styling) ✅

**Estimated effort**: 2-3 hours (1.5 hours Rich integration, 1 hour imagery flag, 30 min testing)

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
### Card Lookup

Look up meanings when using physical tarot deck:
```bash
# Basic lookup
tarotcli lookup "ace of wands"

# Include Waite's imagery descriptions
tarotcli lookup "the magician" --show-imagery

# Fuzzy matching (case-insensitive, partial names)
tarotcli lookup "magician"        # Finds "The Magician"
tarotcli lookup "ACE OF WANDS"    # Finds "Ace of Wands"

# Ambiguous searches show options
tarotcli lookup "ace"
# Multiple cards matched 'ace':
#   - Ace of Wands
#   - Ace of Cups
#   - Ace of Pentacles
#   - Ace of Swords
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
├── tests/               # Test suite (103 tests)
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

**Last Updated**: November 18, 2025 (v0.5.0 - Reading Persistence Complete)
**Maintainer**: melbourne-quantum-dev
**Repository**: Foundation-first development, professional git hygiene, comprehensive testing
