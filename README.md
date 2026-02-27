# OpenWorkoutFormat (OWF)

[![CI](https://github.com/hoopeekoo/OpenWorkoutFormat/actions/workflows/ci.yml/badge.svg)](https://github.com/hoopeekoo/OpenWorkoutFormat/actions/workflows/ci.yml)

A human-readable workout description language with a Python parser. Supports endurance (running, cycling, swimming, rowing), strength (weightlifting), and CrossFit WoDs (EMOM, AMRAP, for-time, circuits).

## Example

```
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
  - bent-over row 3x8rep @60kg @RIR 2 rest:90s

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

# Parse from text or file
doc = owf.parse(open("workout.owf").read())
doc = owf.load("workout.owf")

# Resolve expressions against caller-supplied training variables
resolved = owf.resolve(doc, {
    "FTP": "250W",
    "1RM bench press": "100kg",
    "bodyweight": "80kg",
    "max HR": "185bpm",
})

# Serialize back to .owf text
text = owf.dumps(doc)
```

Training variables like FTP, 1RM, and max HR are provided by your application at resolve time — they are not stored in the `.owf` file. Expressions like `@80% of FTP` remain as unresolved references until `resolve()` is called.

## Format Reference

See [SPEC.md](SPEC.md) for the full formal specification.

### Document Structure

```
---
description: Saturday training block
author: Coach Smith
---

## Saturday Training (2025-02-27)

# Threshold Ride [bike] (2025-02-27 14:00-15:00)

- warmup 15min @easy
- 5x:
  - bike 5min @95% of FTP
  - recover 3min @50% of FTP
- cooldown 10min @easy

# Upper Body [strength] (2025-02-27 15:15-16:00)

- bench press 3x8rep @80kg rest:90s

> Great session overall.
```

| Element | Syntax |
|---------|--------|
| Metadata | `---` delimited key-value pairs (description, author, tags) |
| Session | `## Name [type] (date)` — groups `#` workouts |
| Workout | `# Name [type] (date)` |
| Step | `- action [sets×reps] [duration/distance] [@params] [rest:dur]` |
| Note | `> text` |
| Date | `(YYYY-MM-DD)` or `(YYYY-MM-DD HH:MM-HH:MM)` |

### Endurance Steps

All 10 known actions:

```
- run 5km @4:30/km
- bike 30min @200W
- swim 200m @easy
- row 500m @hard
- ski 20min @moderate
- walk 5min @easy
- hike 2h @easy
- warmup 15min @easy
- cooldown 10min @easy
- recover 3min @easy
```

With pace, power, and heart rate parameters:

```
- run 10min @4:30/km
- bike 5min @80% of FTP
- run 10min @140bpm
- run 10min @70% of max HR
- run 5min @Z3
- run 5min @threshold
- run 5min @tempo
```

### Strength Steps

Sets × reps formats:

```
- bench press 3x8rep @80kg rest:90s
- pull-up 100rep
- face pull 3xmaxrep @15kg rest:60s
- plank 60s
```

Weight parameters and expressions:

```
- bench press 3x8rep @80% of 1RM bench press rest:90s
- dip 3x8rep @bodyweight + 20kg rest:90s
```

RIR (Reps In Reserve) — workout-level default with per-step override:

```
# Full Gym Session [strength] @RIR 2

- back squat 5x5rep rest:120s
- romanian deadlift 3x10rep @60kg rest:90s
- face pull 3xmaxrep @15kg @RIR 3 rest:60s
```

RPE (Rate of Perceived Exertion) — on endurance or strength headings:

```
# Morning Run [run] @RPE 7

- warmup 15min @easy
- run 5km @4:30/km
- cooldown 10min @easy
```

### Container Blocks

**Repeat:**

```
- 5x:
  - bike 5min @200W
  - recover 3min @easy
```

**Superset:**

```
- 3x superset:
  - bench press 3x8rep @80kg rest:90s
  - bent-over row 3x8rep @60kg rest:90s
```

**Circuit:**

```
- 3x circuit:
  - kettlebell swing 10rep @24kg
  - push-up 15rep
  - air squat 20rep
  - burpee 10rep
```

**EMOM:**

```
- emom 10min:
  - power clean 3rep @70kg
```

**Alternating EMOM:**

```
- emom 12min alternating:
  - deadlift 5rep @100kg
  - strict press 7rep @40kg
  - toes-to-bar 10rep
```

**Custom Interval:**

```
- every 2min for 20min:
  - wall ball 15rep @9kg
  - box jump 10rep @24in
```

**AMRAP:**

```
- amrap 12min:
  - pull-up 5rep
  - push-up 10rep
  - air squat 15rep
```

**For-time:**

```
- for-time:
  - run 1mile
  - pull-up 100rep
  - push-up 200rep
  - air squat 300rep
  - run 1mile

- for-time 20min:
  - 5x:
    - deadlift 12rep @70kg
    - hang clean 9rep @70kg
    - push jerk 6rep @70kg
```

### Parameters (`@` prefix)

| Type | Examples |
|------|----------|
| Pace | `@4:30/km`, `@7:00/mi`, `@pace:5:00/km` |
| Power | `@200W`, `@80% of FTP`, `@FTP` |
| Weight | `@80kg`, `@175lb`, `@80% of 1RM bench press` |
| Heart rate | `@140bpm`, `@70% of max HR`, `@Z2`, `@Z3` |
| Intensity | `@easy`, `@moderate`, `@hard`, `@max`, `@threshold`, `@tempo` |
| RPE | `@RPE 7`, `@RPE 8.5` |
| RIR | `@RIR 2`, `@RIR 0` |
| Rest | `rest:90s`, `rest:2min` |

### Expressions

```
@200W                      literal value
@FTP                       variable reference
@80% of FTP                percentage of variable
@bodyweight + 20kg         arithmetic with variable
@70% of 1RM bench press    multi-word variable name
```

### Variable Resolution

Training variables are provided by the consuming application, not stored in the workout file:

```python
# Variables like FTP, 1RM, bodyweight are defined by your app
resolved = owf.resolve(doc, {
    "FTP": "250W",
    "1RM bench press": "100kg",
    "bodyweight": "80kg",
    "max HR": "185bpm",
})

# Before resolve: @80% of FTP → Percentage(80, VarRef("FTP"))
# After resolve:  @80% of FTP → Literal(200, "W")
```

### Two-Level Hierarchy

Use `##` for sessions containing `#` child workouts:

```
## Saturday Training (2025-02-27)

- warmup 10min @easy

# Threshold Ride [bike]

- 5x:
  - bike 5min @200W
  - recover 3min @easy

# Upper Body [strength]

- bench press 3x8rep @80kg rest:90s

> Great session overall.
```

### Notes

Step-level and workout-level notes:

```
# Easy Run [run]

- run 5km @4:30/km
> Aim for negative splits.

- cooldown 10min @easy

> Great session for building aerobic base.
```

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
