# OpenWorkoutFormat (OWF)

Human-readable workout format (`.owf`) with a Python parser. Zero runtime dependencies.

## Quick Reference

```bash
source .venv/bin/activate
pytest tests/ -v          # 232 tests
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

- **Scanner** (`parser/scanner.py`): Classifies lines by prefix (`#`, `##`, `-`, `>`, `@`, blank)
- **Block Builder** (`parser/block_builder.py`): Indentation → tree of `RawBlock` nodes
- **Step Parser** (`parser/step_parser.py`): Recursive descent → typed AST nodes
- **Param Parser** (`parser/param_parser.py`): `@Z2`, `@80kg`, `@RPE 8`, `@80% of FTP`
- **Resolver** (`resolver.py`): Resolves `PercentOfParam` and `BodyweightPlusParam` against caller-supplied variables

## Critical Rules

- **Zero runtime dependencies** — stdlib imports only (PyYAML is optional)
- **No class inheritance** for AST nodes — use Union types: `Step = EnduranceStep | StrengthStep | ...`
- AST nodes are **frozen dataclasses** with `slots=True` (Python 3.14 compat)
- `SourceSpan` on every AST node for error reporting (1-based line/col)
- `Workout.sport_type` = FIT SDK sport type name (e.g. `"Trail Running"`, `"Strength Training"`), set from `[Tag]` in heading
- `Workout.workout_type` = broad category (`endurance`, `strength`, `mixed`, `mobility`), set from legacy `[endurance]` tags
- Legacy tags `[endurance]`/`[strength]`/`[mobility]`/`[mixed]` → `workout_type` set, `sport_type=None`; other tags → `sport_type` set, `workout_type=None`
- Parser accepts **any string** in `[brackets]` — no validation; apps do sport_type → category mapping
- `mixed` is auto-inferred for sessions with 2+ distinct child types, **never serialized** (re-inferred on parse)
- **Step classification by casing**: lowercase first word = `EnduranceStep`, Title Case first word = `StrengthStep`
- No hardcoded endurance action list — any lowercase word is a valid endurance action
- Serializer preserves casing: endurance actions stay lowercase, strength exercises stay Title Case
- Common endurance actions: `run`, `bike`, `swim`, `row`, `ski`, `walk`, `hike`, `warmup`, `cooldown`, `recover`, etc.
- Duration supports compound formats: `1h30min`, `5min30s`, `1h28min2s` (both parse and `__str__`)
- `Document.metadata` = `@ key: value` document-level metadata, NOT training variables
- `Workout.metadata` = session/child workout metadata attached via `@ key: value` after headings
- All step/block AST nodes have a `metadata: dict[str, str]` field for step-level metadata
- `resolve(doc, variables)` only uses caller-supplied variables (does not merge metadata)
- `rest:` syntax replaced by `@rest duration` (e.g. `@rest 90s`)
- **Sessions are mandatory**: every document has `##` session headings; `#`-only files auto-wrapped in unnamed session
- **Dates only on `##` headings** — dates on `#` child headings raise `ParseError`

## Parameter Types

Nine flat param types (no expression trees):

| AST Type | Syntax | Example |
|----------|--------|---------|
| `ZoneParam` | `@Zn` | `@Z2`, `@Z4` |
| `PercentOfParam` | `@N% of VAR` | `@80% of FTP`, `@70% of max HR` |
| `PowerParam` | `@NW` | `@200W` |
| `HeartRateParam` | `@Nbpm` | `@140bpm` |
| `PaceParam` | `@MM:SS/unit` | `@4:30/km`, `@7:00/mi` |
| `WeightParam` | `@Nkg` / `@Nlb` | `@80kg`, `@175lb` |
| `BodyweightPlusParam` | `@bodyweight + Nkg` | `@bodyweight + 20kg` |
| `RPEParam` | `@RPE N` | `@RPE 7`, `@RPE 8` |
| `RIRParam` | `@RIR N` | `@RIR 2` |

Removed syntax (parser rejects with error): `@easy`, `@hard`, `@moderate`, `@threshold`, `@tempo`, `@max`, standalone `@FTP`, `@FTP - 50W`.

## Gotchas

- Empty workouts (no name, no steps, no notes) are **silently filtered** during parsing
- `owf.load()` does NOT resolve includes — it's just read + parse
- Notes boundary: no blank line before = step-level; blank line before = workout-level
- `##` = session, `#` = child workout; steps between `#` headings belong to preceding child
- `#`-only files are auto-wrapped in unnamed session — `doc.workouts[0]` is always a session
- Single-child implicit session: date on `#` heading is lifted to session wrapper
- Heading-level `@RIR` = default for strength exercises (per-step overrides); `@RPE` = session-wide
- Resolver only touches `PercentOfParam` and `BodyweightPlusParam`; all other params pass through

## Cross-Project Impact (Grit)

Grit depends on OWF. Changes to these areas affect Grit — run **cross-project-checker** agent:
- **AST class names**: stored as `node_type` strings in Grit DB (`EnduranceStep`, `StrengthStep`, `Workout`, etc.)
- **AST field names**: used in Grit templates via `asdict()` (e.g. `data.exercise`, `data.action`)
- **`workout_type` values**: drive CSS badge classes in Grit (`badge-endurance`, `badge-strength`, etc.)
- **Serializer output**: reconstructed in Grit detail pages via `owf.dumps()`

## Formal Specification

See @SPEC.md for EBNF grammar and semantic rules.

## Plan Execution

When exiting plan mode to implement a plan, create a task list from the plan's steps using `TaskCreate`. Each task should be a concrete implementation unit (e.g. "Add ZoneParam to ast", "Update param_parser.py"). Then as you work:

- Set each task to `in_progress` when you start it
- Set each task to `completed` when done
- If a task is blocked or needs changes, update its description

This keeps large multi-file features trackable and makes it easy to resume if interrupted.

## Workflow Triggers

- After changing `ast/`, `serializer.py`, or `__init__.py` → run **cross-project-checker**
- After changing parser or SPEC.md → run **spec-checker**
- Before committing → run **code-reviewer**
- After writing new features → run **owf-test-writer**
