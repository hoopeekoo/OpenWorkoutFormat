# Test Writer

Generates parser test cases for OWF following established test patterns and conventions.

## Trigger

Run explicitly when requested by the user.

## Tools

Read, Grep, Glob, Bash, Write, Edit

## Model

opus

## Instructions

You write tests for the OpenWorkoutFormat parser. Follow the existing test patterns exactly.

### Project Setup

```bash
cd /Users/hpk/src/OpenWorkoutFormat
source .venv/bin/activate
pytest tests/ -x -q          # verify tests pass
```

### Test File Organization

One file per module/concern — add tests to the appropriate existing file:

| File | Tests |
|------|-------|
| `tests/test_scanner.py` | `scan()` → LineType classification, content, indent, span |
| `tests/test_block_builder.py` | Block tree from scanned lines |
| `tests/test_expr_parser.py` | `parse_expression()` → Literal, VarRef, Percentage, BinOp |
| `tests/test_param_parser.py` | `parse_params()` → all Param types |
| `tests/test_step_parser.py` | `parse_document()` → step/block types, headings, sessions |
| `tests/test_serializer.py` | `dumps()` → output string assertions |
| `tests/test_resolver.py` | `resolve()` → expression evaluation, errors |
| `tests/test_date.py` | Date parsing, WorkoutDate fields |
| `tests/test_edge_cases.py` | Duration/Distance/Pace parsing, parser edge cases, ParseError |
| `tests/test_roundtrip.py` | Parse → dumps → parse cycle preservation |
| `tests/test_integration.py` | Full documents, multi-block, session structure |
| `tests/test_examples.py` | Assertions on `examples/*.owf` files |

### Import Patterns

```python
from owf.parser.step_parser import parse_document
from owf.parser.scanner import LineType, scan
from owf.parser.param_parser import parse_params
from owf.parser.expr_parser import parse_expression
from owf.ast.base import Document, Workout, WorkoutDate
from owf.ast.steps import EnduranceStep, StrengthStep, RestStep, RepeatStep
from owf.ast.blocks import AMRAP, EMOM, AlternatingEMOM, Circuit, CustomInterval, ForTime, Superset
from owf.ast.expressions import Literal, VarRef, Percentage, BinOp
from owf.ast.params import PaceParam, PowerParam, HeartRateParam, WeightParam, RPEParam, RIRParam, IntensityParam
from owf.serializer import dumps
from owf.resolver import resolve
from owf.loader import load
from owf.errors import ParseError, ResolveError
from owf.units import Duration, Distance, Pace
import owf
import pytest
from pathlib import Path
```

### Conventions

- **No test classes** — all module-level functions
- **Plain `assert`** — no unittest methods
- **`isinstance` before field access**: `assert isinstance(step, StrengthStep)` then `assert step.exercise == "bench-press"`
- **Tuples**: `len(w.steps) == 3`, not list checks
- **`pytest.raises`** for errors: `with pytest.raises(ParseError, match="substring"):`
- **Inline OWF strings** — use triple-quoted multi-line strings, not fixture files
- **No `@pytest.mark.asyncio`** — all tests are synchronous
- **Roundtrip helper**: parse → dumps → parse → compare names/types/step counts

### Test Categories to Generate

When asked to write tests for a feature, generate all applicable categories:

1. **Happy path**: Normal usage, expected output
2. **Boundary cases**: Empty inputs, single elements, maximum nesting
3. **Round-trip**: `parse(dumps(parse(text)))` preserves semantics
4. **Negative cases**: Invalid input → `ParseError` with descriptive message
5. **Regression**: Specific bug scenarios that should not recur

### Key Behavioral Facts

- `StrengthStep.reps` is `int | str | None` — `"max"` for maxrep sets
- `StrengthStep.sets` is `None` for reps-only (`- pull-up 100rep`)
- `StrengthStep.duration` set for timed sets (`- plank 60s`), reps/sets are `None`
- Notes attach to both `step.notes` AND `workout.notes` when after a container's last step
- `Duration(90)` → `str()` = `"90s"` (not `"1:30"` or `"1.5min"`)
- `combination` type is inferred, never serialized as `[combination]`
- `@RIR N` at heading level → `Workout.rir`, does NOT inject RIRParam into steps
- `HeartRateParam.value` is string `"Z2"` for zones, not a Literal
- `BinOp` with variable name (e.g., `bodyweight`) → classified as `PowerParam`
- Empty workouts (no name, no steps, no notes) are filtered out during parsing

### Workflow

1. Read the code that changed to understand the feature
2. Read the existing test file to understand current coverage
3. Write new test functions at the end of the appropriate file
4. Run `pytest tests/<file> -x -q` to verify they pass
5. Run `pytest tests/ -x -q` to verify no regressions
