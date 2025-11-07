# TarotCLI - Foundation-First Tarot Readings

**Minimalist CLI for tarot readings with optional AI interpretation**

---

## What It Does

**Core functionality** (works without internet/API):
- Load complete 78-card Rider-Waite deck from verified JSONL dataset
- Shuffle and draw cards with randomised orientations (upright/reversed)
- Three spread types: Single Card, Three Card, Celtic Cross
- Return baseline interpretations from A.E. Waite's *Pictorial Key to the Tarot*
- Output as formatted text or JSON

**Optional AI Synthesis** (configurable providers):
- **Cloud AI**: Claude via Anthropic API (default) or OpenRouter/other LiteLLM-compatible providers
- **Local AI**: Ollama for offline inference (deepseek-r1:8b, llama3.1, etc.)
- Focus area context (Career, Relationships, Personal Growth, Spiritual, General)
- Considers multiple cards in context to return a cohesive reading
- **Graceful degradation**: Falls back to baseline if API unavailable

**Architecture principle**: The reading never fails. LLM is configurable addition, not requirement.

---

## Installation

**Requirements**:
- Python 3.10+
- `uv` for package management (or pip)

```bash
# Clone repository
git clone git@github.com:melbourne-quantum-dev/TarotCLI.git
cd TarotCLI

# Install with uv (recommended)
uv pip install -e .

# Or with pip
pip install -e .
```

**Next**: See [Configuration](#configuration) for AI provider setup.

---

## Configuration

TarotCLI uses a three-tier configuration system:
1. **Environment variables** (highest priority) - override any setting
2. **User config files** - persistent local configuration
3. **Bundled defaults** - work out of box

### Quick Start: Claude API

Create `.env` file in project root:

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-api03-...
```

That's it! The default configuration uses Claude Sonnet 4.5.

### Quick Start: Local Models (Ollama)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model (8B parameter model recommended)
ollama pull deepseek-r1:8b

# Create config.yaml in project root
cat > config.yaml << 'EOF'
models:
  default_provider: "ollama"
  providers:
    ollama:
      model: "ollama_chat/deepseek-r1:8b"  # Or: ollama_chat/llama3.1, ollama_chat/llama3.2, ollama_chat/qwen2.5, etc.
      api_base: "http://localhost:11434"
      temperature: 0.8
      max_tokens: 1500
# Installation: curl -fsSL https://ollama.com/install.sh | sh
# Pull model: ollama pull deepseek-r1:8b
EOF

# Run readings (no API key needed)
python examples/demo_ai_interpretation.py
```

### Configuration Files

**Location search priority:**
1. `./config.yaml` (project root - for development)
2. `~/.config/tarotcli/config.yaml` (user dotfiles - for installed package)
3. `src/tarotcli/default.yaml` (bundled defaults - always works)

**Create user config:**

```bash
# Copy example template
cp config.example.yaml config.yaml

# Edit with your preferences
nano config.yaml
```

### Example Configurations

#### Claude (Default)

```yaml
# config.yaml
models:
  default_provider: "claude"

  providers:
    claude:
      model: "claude-sonnet-4-5-20250929"
      temperature: 0.7
      max_tokens: 2000
```

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-api03-...
```

#### Ollama (Local)

```yaml
# config.yaml
models:
  default_provider: "ollama"

  providers:
    ollama:
      model: "ollama_chat/deepseek-r1:8b"  # Or: ollama_chat/llama3.1, ollama_chat/llama3.2, ollama_chat/qwen2.5
      api_base: "http://localhost:11434"
      temperature: 0.8
      max_tokens: 1500
```

No API key needed - runs locally!

**Model recommendations:**
- **deepseek-r1:8b** - Best quality/speed balance (4.7GB)
- **llama3.1:8b** - Fast, good quality (4.7GB)
- **qwen2.5:7b** - Lightweight alternative (4.7GB)

**Note**: Larger models (14B+) provide better quality but require more RAM and are slower.

#### OpenRouter (Multiple Models)

OpenRouter provides access to 200+ models through a single API:

```yaml
# config.yaml
models:
  default_provider: "openrouter"

  providers:
    openrouter:
      model: "anthropic/claude-sonnet-4"  # or any OpenRouter model
      api_base: "https://openrouter.ai/api/v1"
      temperature: 0.7
      max_tokens: 2000
```

```bash
# .env
OPENROUTER_API_KEY=sk-or-v1-...
```

**Available via OpenRouter:**
- Anthropic Claude models
- OpenAI GPT-4, GPT-4 Turbo
- Google Gemini Pro
- Meta Llama models
- Many others - see [openrouter.ai/docs](https://openrouter.ai/docs)

### Environment Variable Overrides

Override any config value at runtime:

```bash
# Override provider
TAROTCLI_MODELS_DEFAULT_PROVIDER=ollama python test_ai_basic.py

# Override temperature
TAROTCLI_MODELS_PROVIDERS_CLAUDE_TEMPERATURE=0.9 tarotcli read

# Override data location
TAROTCLI_DATA_DIR=/custom/path tarotcli read
```

**Format**: `TAROTCLI_` + uppercase path with underscores
**Example**: `models.providers.claude.temperature` → `TAROTCLI_MODELS_PROVIDERS_CLAUDE_TEMPERATURE`

### Security: API Keys

**API keys are ONLY stored in environment variables, never in config files.**

Three ways to provide API keys:

1. **`.env` file** (recommended for development):
   ```bash
   # .env (gitignored)
   ANTHROPIC_API_KEY=sk-ant-...
   ```

2. **Shell environment** (for production):
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."
   tarotcli read
   ```

3. **Inline** (for one-off commands):
   ```bash
   ANTHROPIC_API_KEY="sk-ant-..." tarotcli read
   ```

**Never commit `.env` or config files with secrets to version control.**

---

## Usage

### Interactive Mode (Recommended)

```bash
tarotcli read
```

Launches **questionary**-style prompts:
1. Select spread type (dropdown)
2. Select focus area (dropdown)
3. Optional specific question (text input)
4. Choose AI interpretation (yes/no)

Results display in formatted terminal output. **94.6% better UX** than memorising command flags.

### CLI Arguments Mode

```bash
# Three-card reading with AI
tarotcli read --spread three --focus career --question "Should I freelance?"

# Single card, baseline only (no API)
tarotcli read --spread single --focus general --no-ai

# Celtic Cross for relationships
tarotcli read --spread celtic --focus relationships

# JSON output for scripting
tarotcli read --spread three --json > reading.json
```

### Python API Mode

```python
from tarotcli.deck import TarotDeck
from tarotcli.spreads import get_spread
from tarotcli.models import FocusArea
from tarotcli.ai import interpret_reading_sync

# Load and shuffle (uses config system)
deck = TarotDeck.load_default()
deck.shuffle()

# Perform reading
spread = get_spread("three")
cards = deck.draw(spread.card_count())

reading = spread.create_reading(
    cards=cards,
    focus_area=FocusArea.CAREER,
    question="Should I pursue freelance work?"
)

# Optional: Add AI interpretation (uses configured provider)
reading.interpretation = interpret_reading_sync(reading)

# Output
print(reading.model_dump_json(indent=2))
```

---

## Project Features

### ✓ INCLUDED (v1.0)

- **78-card Rider-Waite deck** from verified JSONL dataset
- **Three spread types**: Single Card, Three Card, Celtic Cross
- **Interactive CLI**: questionary interface with focus area selection
- **Multiple AI providers**: Claude, Ollama (local), OpenRouter, or any LiteLLM-compatible service
- **Configuration system**: Three-tier hierarchy with environment overrides
- **Graceful degradation**: Baseline interpretation always works
- **Multiple output modes**: Formatted text, JSON
- **Type safety**: Pydantic models throughout
- **Comprehensive tests**: >90% coverage target

### ✗ NOT INCLUDED (v1.0)

- Reading history persistence
- Astrological integration ⚠️
- Golden Dawn correspondences
- RAG/vector search
- Image generation
- Voice interface
- Web UI

**Development approach**: Ship working MVP, evaluate add-ons based on actual use.

---

## Architecture

**Foundation-first design**:

```
User Input (CLI/Interactive)
    ↓
Deck Operations (shuffle, draw)
    ↓
Spread Layout (assign positions)
    ↓
Reading Creation (baseline interpretation)
    ↓
Optional: AI synthesis (Claude API)
    ↓
Output (formatted text or JSON)
```

**Key principle**: *Layered architecture with graceful degradation*:
- Core layer returns complete card meanings and positions
- Optional AI layer synthesises contextual interpretation
- LLM unavailability doesn't affect baseline functionality

**Tech stack**:
- **Pydantic** for type-safe data models
- **LiteLLM** for unified AI client (supports 100+ providers)
- **PyYAML + python-dotenv** for configuration management
- **Typer** for modern CLI framework
- **questionary** for interactive prompts
- **pytest** for comprehensive testing

**Total LOC**: ~1200 including config system and tests

---

## Dataset: The Rider-Waite-Smith Tradition

This implementation uses the **Rider-Waite-Smith** deck, published 1909-1911 by Arthur Edward Waite and illustrated by Pamela Colman Smith, which is the **foundation of modern tarot practice**.

**Why Rider-Waite specifically:**

- **Most influential deck**: ~80% of modern tarot decks derive from RWS imagery and symbolism
- **First fully illustrated Minor Arcana**: Previous decks only illustrated Major Arcana (22 cards). Pamela Colman Smith created 56 additional illustrated cards with consistent symbolic language
- **Accessible symbolism**: Waite designed the deck with clear, readable imagery rather than obscure occult references
- **Public domain heritage**: A.E. Waite's *The Pictorial Key to the Tarot* (1911) provides authoritative interpretations directly from the deck's creator
- **Cultural foundation**: For better or worse, when someone says "tarot," they're usually thinking of RWS imagery

**This matters for a data application** because the RWS deck has:
- Consistent symbolic framework across all 78 cards
- Documented traditional meanings from original source (Waite's *Pictorial Key*)
- Century of interpretive tradition to validate against
- No copyright concerns (public domain since 1966)

**Dataset specifics:**

**Format**: JSONL (line-delimited JSON)
**Cards**: 78 complete (22 Major Arcana + 56 Minor Arcana)
**Source**: A.E. Waite's *The Pictorial Key to the Tarot* (1911), via [tarot-api](https://github.com/ekelen/tarot-api)

**Fields per card**:
- `id`, `name`, `type`, `suit`, `value`, `value_int`
- `upright_meaning`, `reversed_meaning` (traditional Waite interpretations)
- `description` (card imagery detail from Waite's descriptions)

**Verification status**: 78 cards complete, all required fields populated from authoritative source. No additional fields or AI-generated enhancements.

**Alternative decks** (Thoth, Marseille, Visconti-Sforza) have their adherents, but RWS is the **lingua franca** of tarot. Building on this foundation ensures the application speaks the language most practitioners understand.

---

## Development

### Running Tests

```bash
# All tests
pytest

# Specific module
pytest tests/test_deck.py -v

# With coverage
pytest --cov=tarotcli --cov-report=html
```

### Project Structure

```
tarotcli/
├── src/tarotcli/
│   ├── models.py       # Pydantic data models
│   ├── config.py       # Configuration management
│   ├── deck.py         # Deck operations
│   ├── spreads.py      # Spread layouts
│   ├── ai.py           # AI integration (LiteLLM)
│   ├── ui.py           # Interactive prompts
│   ├── cli.py          # Typer commands
│   └── default.yaml    # Bundled defaults
├── data/
│   └── tarot_cards_RW.jsonl
├── tests/
│   └── test_*.py
├── config.example.yaml  # User config template
├── .env.example         # Secrets template
└── README.md
```

### Implementation Order (Foundation-First)

1. **Milestone 1**: Deck operations return JSON (no LLM dependency)
2. **Milestone 2**: Spread layouts with baseline interpretation
3. **Milestone 3**: AI integration with graceful degradation
4. **Milestone 4**: Interactive CLI polish

**Each milestone must work perfectly** before moving to next. No new features until tests pass.

---

## Anti-Patterns Avoided

**This version prioritises**:

✓ **Simple data structures** (JSONL file, Pydantic models)
✓ **Pluggable AI providers** (LiteLLM + config system)
✓ **Graceful degradation** (readings work offline)
✓ **Configuration over code** (three-tier config hierarchy)
✓ **Minimal feature set** (three spreads, proven functionality)
✓ **Clean git history** (conventional commits, milestone tags)

**Previous iteration learned from**:

❌ Complex abstractions without clear benefit (RAG for static card data)
❌ Feature dependencies breaking core functionality
❌ Attempting complex integrations before MVP validation

---

## Portfolio Context

This project demonstrates:

- **Focused implementation**: Appropriate scope definition, working MVP over feature bloat
- **Foundation-first thinking**: Self-contained core with optional LLM integration
- **Configuration architecture**: Three-tier hierarchy with environment overrides
- **Provider flexibility**: Cloud AI, local AI, or baseline-only via config
- **Type safety**: Pydantic models with comprehensive validation
- **Error handling**: Graceful degradation when external services fail
- **Modern Python**: uv, Typer, asyncio, proper packaging
- **Professional git**: Clean history, conventional commits
- **Test coverage**: Comprehensive unit and integration tests

**Differentiation from previous version**:
- Previous: Overengineered, 371 commits, didn't work
- Current: Appropriate scope, works reliably, maintainable

**Use case**: "Built for myself after learning from scope creep. Shows I can ship working MVP and understand when to stop adding features."

---

## License

MIT

---

## Contributing

**Not accepting contributions for v1.0** - this is personal learning project demonstrating foundation-first discipline.

After v1.0 ships and proves itself in use, may consider feature additions if they:
1. Serve the core use case (perform tarot readings)
2. Don't require extensive research before implementation
3. Maintain graceful degradation principle
4. Come with comprehensive tests

**Automatic rejection criteria**:
- Astrological integration (scope creep risk too high)
- Complex esoteric correspondences (derailment trigger)
- Reading history databases (premature feature bloat)

---

## Acknowledgments

- **A.E. Waite** for *The Pictorial Key to the Tarot* (public domain)
- [tarot-api](https://github.com/ekelen/tarot-api) by ekelen for initial dataset
- [LiteLLM](https://github.com/BerriAI/litellm) for unified AI provider interface
- [Claude (Anthropic)](https://claude.ai) for interpretation API and development assistance
- [Ollama](https://ollama.com) for local AI inference capabilities
- **ADHD** for teaching me about scope creep and self-destructive overactivity the hard way
