# OpenWorkoutFormat (OWF)

A human-readable workout description language with a Python parser. Supports endurance (running, cycling), strength (weightlifting), and CrossFit WoDs (EMOM, AMRAP, for-time).

## Example

```
---
FTP: 250W
1RM bench press: 100kg
---

# Threshold Ride [bike]

- warmup 15min @60% of FTP
- 5x:
  - bike 5min @95% of FTP
  - recover 3min @50% of FTP
- cooldown 10min @easy

> Felt strong through set 3, faded on 4-5.

# Upper Body [strength]

- 3x superset:
  - bench press 3x8rep @80% of 1RM bench press rest:90s
  - bent-over row 3x8rep @60kg rest:90s

# Metcon [wod]

- amrap 12min:
  - pull-up 5rep
  - push-up 10rep
  - air squat 15rep
```

## Installation

```bash
pip install -e .
```

## Usage

```python
import owf

# Parse from text
doc = owf.parse(open("workout.owf").read())

# Parse from file (resolves includes)
doc = owf.load("workout.owf")

# Resolve expressions against variables
resolved = owf.resolve(doc)

# Serialize back to .owf text
text = owf.dumps(doc)
```

## Format Reference

| Element | Syntax |
|---|---|
| Frontmatter | `---` delimited key-value pairs |
| Heading | `# Name [type]` |
| Step | `- action [setsXreps] [duration/distance] [@params] [rest:duration]` |
| Repeat | `- Nx:` with sub-steps |
| Superset | `- Nx superset:` with sub-steps |
| EMOM | `- emom duration:` / `- emom duration alternating:` |
| AMRAP | `- amrap duration:` |
| For-time | `- for-time [cap]:` |
| Include | `- include: Workout Name` |
| Notes | `> blockquote` |

### Parameters (`@` prefix)

- Pace: `@4:30/km`
- Power: `@200W`, `@80% of FTP`
- Heart rate: `@Z2`, `@140bpm`, `@70% of max HR`
- Weight: `@80kg`, `@70% of 1RM bench press`
- RPE: `@RPE 7`
- Intensity: `@easy`, `@moderate`, `@hard`, `@max`

### Expressions

- `80% of FTP` — percentage of a variable
- `bodyweight + 20kg` — arithmetic with variables
- `70% of 1RM bench press` — multi-word variable names

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/ -v
mypy src/
ruff check src/
```

## License

MIT
