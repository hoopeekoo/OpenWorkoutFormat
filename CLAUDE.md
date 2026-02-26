# OpenWorkoutFormat (OWF)

## Project Overview

A human-readable workout format (`.owf`) with a Python parser. Supports endurance, strength, and CrossFit WoD workout types.

## Architecture

Four-phase parser pipeline:
```
Raw text → Scanner → LogicalLine stream → Block Builder → indentation tree
→ Step Parser (+ Param Parser + Expr Parser) → AST → Resolver → resolved AST
```

- **Scanner** (`parser/scanner.py`): Classifies lines by prefix (`#`, `-`, `>`, `---`, blank)
- **Block Builder** (`parser/block_builder.py`): Uses indentation to create tree of `RawBlock` nodes
- **Step Parser** (`parser/step_parser.py`): Recursive descent over blocks → typed AST nodes
- **Resolver** (`resolver.py`): Evaluates expressions against frontmatter variables

## Key Conventions

- AST nodes are frozen dataclasses with `slots=True` — no inheritance (Python 3.14 slots compatibility)
- Union types used instead of base classes: `Step = EnduranceStep | StrengthStep | ...`
- Zero runtime dependencies; PyYAML is optional
- `SourceSpan` on every node for error reporting (line/col, 1-based)

## Development

```bash
source .venv/bin/activate
pytest tests/ -v          # Run tests
mypy src/                 # Type checking
ruff check src/           # Linting
```

## Public API

```python
import owf
doc = owf.parse(text)              # text → AST
doc = owf.load("workout.owf")     # file → AST (resolves includes)
text = owf.dumps(doc)              # AST → text
doc = owf.resolve(doc, variables)  # evaluate expressions
```
