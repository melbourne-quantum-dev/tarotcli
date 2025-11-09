# TarotCLI

Minimalist tarot reading CLI with optional AI interpretation.

Works offline with static meanings and card lookup. Plug and play with Claude/OpenAI/Ollama.

**Status:** v0.4.5 - Production ready, actively maintained

---

## Contents

- [Quick Start](#quick-start)
- [What to Expect](#what-to-expect)
- [Features](#features)
- [Usage](#usage)
- [Configuration](#configuration)
- [How It Works](#how-it-works)
- [Why This Exists](#why-this-exists)
- [Architecture](#architecture)
- [Development](#development)
- [Project Boundaries](#project-boundaries)

---

## Quick Start

```bash
# Install with uv (recommended)
git clone https://github.com/melbourne-quantum-dev/tarotcli.git
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

## Features

- **Three spread types**: Single card, three-card (past/present/future), Celtic Cross
- **Multi-provider AI**: Claude, Ollama (local), OpenAI, OpenRouter
- **Graceful degradation**: Readings never fail - works offline, AI optional
- **Card lookup**: Physical deck companion or AI validation tool with fuzzy matching
- **Authoritative source**: A.E. Waite's 1911 *Pictorial Key to the Tarot*
- **Zero config required**: Runs immediately with bundled defaults

## Usage

### Interactive Readings

```bash
# Guided prompts for spread, focus, and question
tarotcli read

# Specify everything via CLI
tarotcli read --spread three --focus career --question "Should I freelance?"

# Use local Ollama model
tarotcli read --provider ollama --spread single

# Markdown output to file
tarotcli read --spread celtic --focus general > reading.md

# JSON output to file
tarotcli read --spread celtic --focus general --json > reading.json
```

### Card Lookup

Look up static meanings to validate or when using physical tarot deck:

```bash
# Basic lookup
tarotcli lookup "ace of wands"

# Include Waite's imagery descriptions
tarotcli lookup "the magician" --show-imagery

# Save to file
tarotcli lookup "nine of swords" --show-imagery > nine-of-swords.md

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

TarotCLI uses three-tier configuration: environment variables override user config, which overrides bundled defaults.

### API Keys

#### Option 1: .env file (recommended for development)

```bash
# Copy template
cp .env.example .env

# Edit .env file
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
OPENROUTER_API_KEY=sk-or-...
```

#### Option 2: Shell environment variables

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
export OPENROUTER_API_KEY="sk-or-..."
```

**Note**: Ollama runs locally and requires no API key.

### User Configuration (Optional)

Customize provider settings and output preferences:

**For editable install** (development): Copy `config.example.yaml` to `./config.yaml` in project root

**For installed package**: Copy to `~/.config/tarotcli/config.yaml`

Example configuration:

```yaml
# AI provider (claude, ollama, openai, openrouter)
models:
    default_provider: claude # swap to local inference just by changing this to "ollama"
    # Provider specific settings
    providers:
        ollama:
            model: ollama_chat/deepseek-r1:8b # Or: llama3.1, llama3.2, qwen2.5, etc.
            api_base: http://localhost:11434
            temperature: 0.8
            max_tokens: 1500
            # Install: curl -fsSL https://ollama.com/install.sh | sh
            # Pull model: ollama pull deepseek-r1:8b
        claude:
            model: claude-haiku-4-5-20251001
            temperature: 0.7
            max_tokens: 1500
```

See `config.example.yaml` for complete reference with all available options.

## How It Works

### Graceful Degradation

Readings complete successfully regardless of AI availability:

1. **AI available**: Dynamic interpretation using card meanings, imagery, and context
2. **AI unavailable**: Static interpretation from traditional card meanings
3. **AI errors**: Falls back to static interpretation without failing

No reading fails due to API issues.

### Data Source

Card meanings and imagery descriptions from A.E. Waite's *The Pictorial Key to the Tarot* (1911). The 78-card dataset includes:

- Traditional upright and reversed meanings (~140 chars each)
- Waite's complete imagery descriptions (~1,600 chars each)
- Proper suit and value metadata

AI prompts inject full imagery descriptions (not just keywords) - this differentiates interpretations from generic tarot apps using diluted meanings from pop culture or relying on LLM training data or synthetic datasets.

**Card example:**

```json
{
  "id": "ar01",
  "name": "The Magician",
  "upright_meaning": "Skill, diplomacy, address, subtlety...",
  "reversed_meaning": "Physician, Magus, mental disease...",
  "description": "A youthful figure in the robe of a magician, having the 
    countenance of divine Apollo, with smile of confidence and shining eyes. 
    Above his head is the mysterious sign of the Holy Spirit, the sign of 
    life, like an endless cord, forming the figure 8 in a horizontal position. 
    About his waist is a serpent-cincture, the serpent appearing to devour 
    its own tail..."
}
```

**Result**: AI creates reading from pseudorandom card draw, authoritative 1911 source material, spatial positioning of cards, tailored to context provided by querent's focus area and question. Interpretations can pull from actual card symbolism (robe, serpent, figure 8) rather than abstractions or clichés.

## Why This Exists

Built as response to algorithmic collective tarot readings on YouTube. Provides:

1. **Autonomy**: Personal readings without platform dependency
2. **Authority**: Waite's original text, not SEO-optimised interpretations  
3. **Privacy**: Local readings, no data collection
4. **Education**: Learn tarot using authoritative source material

Also serves as portfolio piece demonstrating:

- Scope discipline (shipped working MVP without overengineering)
- Foundation-first methodology (each layer proven before next)
- Graceful degradation patterns (never fails)
- Professional Python practices (Pydantic, pytest, conventional commits)

*But there's more happening here than practical utility suggests.*

## Architecture

Foundation-first design ensuring core functionality works without dependencies:

```
Layer 1: Data models (Pydantic)      → Type-safe card/reading structures
Layer 2: Deck operations             → Load, shuffle, draw (no AI dependency)
Layer 3: Spread layouts              → Position meanings, static interpretation
Layer 4: AI integration (optional)   → Dynamic interpretation with graceful degradation
Layer 5: CLI interface               → Interactive + argument modes
```

Each layer works independently. AI is optional, not required.

**Architectural principle**: The code implements liturgical structure—it serves the same function as ritual in traditional practice. It doesn't matter that you're calling `random.shuffle()` instead of physically shuffling cards. Both operations serve identical purposes: introduce controlled entropy within bounded possibility space.

TarotCLI is a **resonance interface**: computational system that implements structured constraints specifically to enable unstructured emergence. The code doesn't generate meaning—it creates the conditions under which meaning can emerge through interaction.

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

**Requirements:**

- Python 3.10+
- uv or pip for installation
- Optional: Anthropic/OpenAI API key for AI interpretation
- Optional: Local Ollama installation for offline AI

## Project Boundaries

**In scope:**

- Reliable tarot readings (programmatic or physical deck companion)
- Educational resource with authoritative Waite source material
- Portfolio demonstration of scope discipline and foundation-first development
- Consciousness research through observable, measurable implementation

**Explicitly out of scope:**

- Multiple deck systems (Thoth, Marseille, etc.)
- Reading history/persistence (no database)
- Astrological integration or Golden Dawn correspondences
- Web UI or API server

This is a focussed CLI tool and research instrument, not a framework.

**For development context:** See `AGENTS.md` (detailed architecture and session history).

## License

MIT License - see LICENSE file for details.

## Contributing

This is a personal portfolio and research project with intentionally limited scope.

Bug reports welcome. Feature requests evaluated against scope boundaries.

---

**Built with foundation-first methodology**: Each milestone proven before proceeding to next. Maintains scope discipline—no feature creep.
