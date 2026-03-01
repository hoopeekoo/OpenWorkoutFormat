# OpenWorkoutFormat (OWF)

Human-readable workout format (`.owf`) with a Python parser. Zero runtime dependencies.

## Quick Reference

```bash
source .venv/bin/activate
pytest tests/ -v          # 206 tests
mypy src/                 # strict mode
ruff check src/           # linting
```

## Public API

```python
import owf
doc = owf.parse(text)              # text → AST
doc = owf.load("workout.owf")     # file → AST (just read + parse, no include resolution)
text = owf.dumps(doc)              # AST → text
doc = owf.resolve(doc, variables)  # evaluate expressions with caller-supplied variables
```

## Architecture

Four-phase parser pipeline:
```
Raw text → Scanner → Block Builder → Step Parser → Resolver → resolved AST
```

- **Scanner** (`parser/scanner.py`): Classifies lines by prefix (`#`, `##`, `-`, `>`, `---`, blank)
- **Block Builder** (`parser/block_builder.py`): Indentation → tree of `RawBlock` nodes
- **Step Parser** (`parser/step_parser.py`): Recursive descent → typed AST nodes
- **Param Parser** (`parser/param_parser.py`): `@intensity`, `@80kg`, `@RPE 8`, `@4:30/km`
- **Resolver** (`resolver.py`): Evaluates expressions against caller-supplied variables

## Critical Rules

- **Zero runtime dependencies** — stdlib imports only (PyYAML is optional)
- **No class inheritance** for AST nodes — use Union types: `Step = EnduranceStep | StrengthStep | ...`
- AST nodes are **frozen dataclasses** with `slots=True` (Python 3.14 compat)
- `SourceSpan` on every AST node for error reporting (1-based line/col)
- Workout types are **modalities only**: `endurance`, `strength`, `mixed`, `mobility`
- `mixed` is auto-inferred for sessions with 2+ distinct child types, **never serialized** (re-inferred on parse)
- Duration supports compound formats: `1h30min`, `5min30s`, `1h28min2s` (both parse and `__str__`)
- `Document.metadata` = frontmatter key-value pairs for doc metadata, NOT training variables
- `resolve(doc, variables)` only uses caller-supplied variables (does not merge frontmatter)

## Gotchas

- Empty workouts (no name, no steps, no notes) are **silently filtered** during parsing
- BinOp params with variable names (e.g. "bodyweight") → `PowerParam`, not `WeightParam`
- `owf.load()` does NOT resolve includes — it's just read + parse
- Notes boundary: no blank line before = step-level; blank line before = workout-level
- Two-level docs: `##` = session, `#` = child workout; steps between `#` headings belong to preceding child
- Heading-level `@RIR` = default for strength exercises (per-step overrides); `@RPE` = workout-wide

## Cross-Project Impact (Grit)

Grit depends on OWF. Changes to these areas affect Grit — run **cross-project-checker** agent:
- **AST class names**: stored as `node_type` strings in Grit DB (`EnduranceStep`, `StrengthStep`, `Workout`, etc.)
- **AST field names**: used in Grit templates via `asdict()` (e.g. `data.exercise`, `data.action`)
- **`workout_type` values**: drive CSS badge classes in Grit (`badge-endurance`, `badge-strength`, etc.)
- **Serializer output**: reconstructed in Grit detail pages via `owf.dumps()`

## Formal Specification

See @SPEC.md for EBNF grammar and semantic rules.

## Workflow Triggers

- After changing `ast/`, `serializer.py`, or `__init__.py` → run **cross-project-checker**
- After changing parser or SPEC.md → run **spec-checker**
- Before committing → run **code-reviewer**
- After writing new features → run **owf-test-writer**
