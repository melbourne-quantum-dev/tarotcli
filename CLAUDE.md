# TarotCLI - Claude Code Context

## Project Overview

Minimalist tarot reading CLI with optional AI interpretation. 
Foundation-first architecture: core functionality works reliably without LLM dependency.

**Current Status**: v0.3.0 development (Milestone 3 complete, Milestone 4 in progress)

**Completed Milestones:**
- ✅ Milestone 1 (v0.1.0): Core deck operations
- ✅ Milestone 2 (v0.2.0): Spread layouts with baseline interpretation
- ✅ Milestone 3 (v0.3.0): AI integration via Claude API
- 🚧 Milestone 4: Interactive CLI (in progress)

## Commands

### Development
- `uv pip install -e '.[dev]'` - Install package in editable mode with dev dependencies
- `pytest` - Run full test suite
- `pytest tests/test_deck.py -v` - Run specific test module with verbose output
- `pytest --cov=tarotcli --cov-report=html` - Generate coverage report
- `python -m tarotcli` - Run CLI entry point

### Usage
- `tarotcli read` - Interactive reading (questionary prompts)
- `tarotcli read --spread three --focus career --no-ai` - CLI arguments mode
- `tarotcli list-spreads` - Show available spread types
- `tarotcli version` - Display version

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
- `tests/test_deck.py`: 11 tests (95% deck.py coverage)
- `tests/test_spreads.py`: 10 tests (100% spreads.py coverage)
- `tests/test_ai.py`: 20 tests (100% ai.py coverage)
- **Total**: 41/41 tests passing

**Demonstration scripts** (manual validation):
- `test_deck_basic.py`: Validates deck operations
- `test_spread_basic.py`: Validates spread layouts
- `test_ai_basic.py`: Validates AI integration (use `DEBUG_PROMPT=1` to see full prompt)

## Core Files

- `src/tarotcli/models.py` - Pydantic data models (Card, DrawnCard, Reading, FocusArea)
- `src/tarotcli/deck.py` - Deck operations (load 78 cards from JSONL, shuffle, draw)
- `src/tarotcli/spreads.py` - Spread layouts (single, three-card, Celtic Cross)
- `src/tarotcli/ai.py` - Claude API integration via LiteLLM (graceful degradation)
- `src/tarotcli/ui.py` - Questionary interactive prompts
- `src/tarotcli/cli.py` - Typer CLI commands
- `data/tarot_cards_RW.jsonl` - 78-card Rider-Waite dataset

## AI Integration (Milestone 3)

### Architecture

**LiteLLM + Claude API:**
- Async implementation via `acompletion()` (future-proofed for web API)
- Sync wrapper `interpret_reading_sync()` for CLI usage
- Model: `claude-sonnet-4-20250514` (consider adding `anthropic/` prefix)

**Graceful Degradation Pattern:**
```python
# Check for API key before attempting call
if not os.getenv("ANTHROPIC_API_KEY"):
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
python test_ai_basic.py                       # End-to-end validation

# Debug mode: See actual prompt sent to AI
DEBUG_PROMPT=1 python test_ai_basic.py
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