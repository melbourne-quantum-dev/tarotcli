# TarotCLI

Minimalist tarot reading CLI with optional AI interpretation. Works offline with baseline meanings, and for card lookup. Plug and play with Claude/OpenAI etc with an API key or Ollama with a local model instance running.

**Status**: v0.4.5 - Production ready, actively maintained

---

## What to Expect

**Interactive reading flow:**
```
$ tarotcli read

🔮 TarotCLI - Interactive Reading

? Select spread type: Single Card - One card for immediate guidance or daily draw
? What is the focus of this reading? General
? Specific question (press Enter to skip): Should I have pasta for dinner?
? Use AI interpretation? (provider: claude) Yes

══════════════════════════════════════════════════
Single Card - General
══════════════════════════════════════════════════

❓ Question: Should I have pasta for dinner?

Cards Drawn:

  Present: Eight of Swords ↑ Upright

──────────────────────────────────────────────────
INTERPRETATION
──────────────────────────────────────────────────

The Eight of Swords suggests you're overthinking this decision. The 
card represents feeling trapped by perceived constraints or anxieties 
that may be self-imposed.

In the context of your dinner choice, this card isn't saying "pasta" 
or "no pasta" - it's pointing to a pattern of mental restriction. Are 
you genuinely concerned about the meal, or is anxiety from other areas 
spilling over into simple decisions?

Practical guidance: Choose whatever brings comfort without judgment. 
The Eight of Swords reminds you that many of our constraints are mental 
rather than real. Sometimes the best choice is the one that reduces 
stress rather than adds another decision to analyze.

(And yes, pasta sounds good.)

══════════════════════════════════════════════════
```

**Card lookup for physical readings:**
```
$ tarotcli lookup "ace of wands"

══════════════════════════════════════════════════
Ace of Wands
══════════════════════════════════════════════════

↑ UPRIGHT
──────────────────────────────────────────────────
Creation, invention, enterprise, the powers which result in these; 
principle, beginning, source; birth, family, origin, and in a sense 
the virility which is behind them; the starting point of enterprises; 
according to another account, money, fortune, inheritance.

↓ REVERSED
──────────────────────────────────────────────────
Fall, decadence, ruin, perdition, to perish also a certain clouded joy.

══════════════════════════════════════════════════
```

---

## Features

- **Three spread types**: Single card, three-card (past/present/future), Celtic Cross
- **Multi-provider AI**: Claude, Ollama (local), OpenAI, OpenRouter
- **Graceful degradation**: Readings never fail - AI enhances, baseline always works
- **Card lookup**: Physical deck companion with fuzzy name matching
- **Authoritative source**: A.E. Waite's 1911 *Pictorial Key to the Tarot*
- **Zero config required**: Runs immediately with bundled defaults

## Quick Start
```bash
# Install with uv (recommended)
git clone https://github.com/yourusername/tarotcli.git
cd tarotcli
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .

# Or with pip
pip install -e .

# Run immediately (works without API keys)
tarotcli read

# Add AI interpretation (optional)
export ANTHROPIC_API_KEY="your-key-here"
tarotcli read --provider claude
```

## Usage

### Interactive Readings
```bash
# Guided prompts for spread, focus, and question
tarotcli read

# Specify everything via CLI
tarotcli read --spread three --focus career --question "Should I freelance?"

# Use local Ollama model
tarotcli read --provider ollama --spread single

# JSON output for scripting
tarotcli read --spread celtic --format json > reading.json
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

### Other Commands
```bash
tarotcli list-spreads    # Show available spreads
tarotcli config-info     # Display current configuration
tarotcli version         # Show version
```

## Configuration

TarotCLI uses three-tier configuration: environment variables → `~/.config/tarotcli/config.yaml` → bundled defaults.

### API Keys (Environment Variables Only)
```bash
# Claude (Anthropic)
export ANTHROPIC_API_KEY="sk-ant-..."

# OpenAI
export OPENAI_API_KEY="sk-..."

# OpenRouter
export OPENROUTER_API_KEY="sk-or-..."

# Ollama runs locally (no key needed)
```

### User Configuration (Optional)

Create `~/.config/tarotcli/config.yaml` to customize:
```yaml
# AI provider (claude, ollama, openai, openrouter)
ai:
  default_provider: claude

# Provider-specific settings
models:
  providers:
    claude:
      model: claude-sonnet-4-20250514
      temperature: 0.7
      max_tokens: 1500
    
    ollama:
      model: llama3.2:latest
      base_url: http://localhost:11434
      temperature: 0.8
      timeout: 30

# Output preferences
output:
  show_baseline: false  # Show baseline even when AI available
```

Full configuration reference: see `config.example.yaml` in repository.

## How It Works

### Graceful Degradation

Readings complete successfully regardless of AI availability:

1. **AI available**: Enhanced interpretation synthesizing card meanings, imagery, and focus context
2. **AI unavailable**: Baseline interpretation from traditional card meanings
3. **AI errors**: Falls back to baseline without failing

No reading ever fails due to API issues.

### Data Source

Card meanings and imagery descriptions from A.E. Waite's *The Pictorial Key to the Tarot* (1911). The 78-card dataset includes:

- Traditional upright and reversed meanings (~140 chars each)
- Waite's complete imagery descriptions (~1,600 chars each)
- Proper suit and value metadata

AI prompts include imagery descriptions (not just keywords) - this differentiates interpretations from generic tarot apps using scraped meanings.

## Requirements

- Python 3.10+
- uv or pip for installation
- Optional: Anthropic/OpenAI API key for AI interpretation
- Optional: Local Ollama installation for offline AI

## Development
```bash
# Install with dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Check coverage
pytest --cov=tarotcli --cov-report=html

# Format code
ruff format src/ tests/
```

## Architecture

Foundation-first design ensuring core functionality works without dependencies:
```
Layer 1: Data models (Pydantic)      → Type-safe card/reading structures
Layer 2: Deck operations             → Load, shuffle, draw (no AI dependency)
Layer 3: Spread layouts              → Position meanings, baseline interpretation
Layer 4: AI integration (optional)   → Enhanced interpretation with graceful degradation
Layer 5: CLI interface               → Interactive + argument modes
```

Each layer works independently. AI is enhancement, not requirement.

## Project Goals

**In scope**:
- Reliable tarot readings (programmatic or physical deck companion)
- Educational resource with authoritative Waite source material
- Portfolio demonstration of scope discipline and foundation-first development

**Explicitly out of scope**:
- Multiple deck systems (Thoth, Marseille, etc.)
- Reading history/persistence (no database)
- Astrological integration or Golden Dawn correspondences
- Web UI or API server

This is a focused CLI tool, not a framework.

## Why This Exists

Built as response to algorithmic collective tarot readings on YouTube. Provides:

1. **Autonomy**: Personal readings without platform dependency
2. **Authority**: Waite's original text, not SEO-optimized interpretations  
3. **Privacy**: Local readings, no data collection
4. **Education**: Learn tarot using authoritative source material

Also serves as portfolio piece demonstrating:
- Scope discipline (shipped working MVP without overengineering)
- Foundation-first methodology (each layer proven before next)
- Graceful degradation patterns (never fails)
- Professional Python practices (Pydantic, pytest, conventional commits)

## License

MIT License - see LICENSE file for details.

## Contributing

This is a personal portfolio project with intentionally limited scope. Bug reports welcome, feature requests evaluated against scope boundaries.

For development context: see `AGENTS.md` (detailed context).

---

**Built with foundation-first methodology**: Each milestone proven before proceeding to next. No feature creep or scope expansion.