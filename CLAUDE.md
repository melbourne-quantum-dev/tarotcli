# TarotCLI - Claude Code Context

## Project Overview

Minimalist tarot reading CLI with optional AI interpretation. 
Foundation-first architecture: core functionality works reliably without LLM dependency.

**Current Status**: v1.0 development (Milestone 1-4 implementation)

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

## Core Files

- `src/tarotcli/models.py` - Pydantic data models (Card, DrawnCard, Reading, FocusArea)
- `src/tarotcli/deck.py` - Deck operations (load 78 cards from JSONL, shuffle, draw)
- `src/tarotcli/spreads.py` - Spread layouts (single, three-card, Celtic Cross)
- `src/tarotcli/ai.py` - Claude API integration via LiteLLM (graceful degradation)
- `src/tarotcli/ui.py` - Questionary interactive prompts
- `src/tarotcli/cli.py` - Typer CLI commands
- `data/tarot_cards_RW.jsonl` - 78-card Rider-Waite dataset

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