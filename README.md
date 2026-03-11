# OpenWorkoutFormat (OWF)

[![CI](https://github.com/hoopeekoo/OpenWorkoutFormat/actions/workflows/ci.yml/badge.svg)](https://github.com/hoopeekoo/OpenWorkoutFormat/actions/workflows/ci.yml)

A human-readable workout description language with a Python parser. Supports running, cycling, swimming, strength training, CrossFit WoDs (EMOM, AMRAP, for-time, circuits), yoga, and any other sport.

## Example

```
@ author: Coach Smith

# Threshold Ride [Cycling] (2026-03-09) @RPE 7

- Warmup 15min @60% of FTP
- 5x:
  - Bike 5min @95% of FTP
  - Recover 3min @50% of FTP
- Cooldown 10min @Z1

> Felt strong through set 3, faded on 4-5.

# Upper Body [Strength Training] @RIR 2

- 3x superset:
  - Bench Press 8rep @80% of 1RM bench press @rest 90s
  - Dumbbell Row 8rep @32kg @rest 90s
- Pull-Up 3xmaxrep @bodyweight + 10kg @rest 90s

# Cindy [HIIT]

- amrap 20min:
  - Pull-Up 5rep
  - Push-Up 10rep
  - Air Squat 15rep
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

An OWF document contains optional metadata, then one or more `#` workout headings with steps.

```
@ description: Saturday training block
@ author: Coach Smith

# Threshold Ride [Cycling] (2026-03-09)
@ location: Indoor trainer

- Warmup 15min @Z1
- 5x:
  - Bike 5min @95% of FTP
  - Recover 3min @50% of FTP
- Cooldown 10min @Z1

# Upper Body [Strength Training]

- Bench Press 3x8rep @80kg @rest 90s

> Great session overall.
```

| Element | Syntax |
|---------|--------|
| Metadata | `@ key: value` — document-level (before headings) or workout-level (after heading) |
| Workout | `# Name [sport type] (date)` — top-level grouping |
| Step | `- Action [sets x reps] [duration] [distance] [@params] [@rest dur]` |
| Note | `> text` — attaches to preceding step or workout |
| Date | `(YYYY-MM-DD)` or `(YYYY-MM-DD HH:MM-HH:MM)` |

### Sport Types

Bracket tags on headings set the specific sport type. Any string is accepted — these are the common ones:

```
# Morning Run [Running]
# Threshold Ride [Cycling]
# Swim Intervals [Pool Swimming]
# Gravel Century [Gravel Cycling]
# Full Gym Session [Strength Training]
# Metcon [HIIT]
# Yoga Flow [Yoga]
```

### Steps

All steps use Title Case action names. Any action can have any combination of sets, reps, duration, distance, and parameters:

```
- Run 5km @4:30/km
- Bike 30min @200W
- Swim 200m @Z2
- Bench Press 3x8rep @80kg @rest 90s
- Pull-Up 3xmaxrep @bodyweight + 20kg @rest 90s
- Plank 3x60s @rest 30s
- Warmup 15min @Z1
```

Sets x reps formats:

| Format | Meaning | Example |
|--------|---------|---------|
| `3x8rep` | 3 sets of 8 reps | `- Bench Press 3x8rep @80kg` |
| `3x8` | 3 sets of 8 reps (shorthand) | `- Bench Press 3x8 @80kg` |
| `100rep` | 100 reps (no set count) | `- Pull-Up 100rep` |
| `3xmaxrep` | 3 sets to failure | `- Face Pull 3xmaxrep @15kg` |

### Container Blocks

**Repeat:**

```
- 5x:
  - Bike 5min @200W
  - Recover 3min @Z1
```

**Superset:**

```
- 3x superset:
  - Bench Press 8rep @80kg @rest 90s
  - Dumbbell Row 8rep @32kg @rest 90s
```

**Circuit:**

```
- 4x circuit:
  - Kettlebell Swing 15rep @24kg
  - Push-Up 15rep
  - Goblet Squat 12rep @24kg
  - Pull-Up 8rep
```

**EMOM:**

```
- emom 10min:
  - Power Clean 3rep @70kg
```

**Alternating EMOM:**

```
- emom 12min alternating:
  - Deadlift 5rep @100kg
  - Strict Press 7rep @40kg
  - Toes-To-Bar 10rep
```

**Custom Interval:**

```
- every 2min for 20min:
  - Wall Ball 15rep @9kg
  - Box Jump 10rep
```

**AMRAP:**

```
- amrap 20min:
  - Pull-Up 5rep
  - Push-Up 10rep
  - Air Squat 15rep
```

**For-time:**

```
- for-time 60min:
  - Run 1mile
  - Pull-Up 100rep
  - Push-Up 200rep
  - Air Squat 300rep
  - Run 1mile

- for-time 20min:
  - 5x:
    - Deadlift 12rep @70kg
    - Hang Clean 9rep @70kg
    - Push Jerk 6rep @70kg
```

### Parameters (`@` prefix)

| Type | Examples |
|------|----------|
| Zone | `@Z1`, `@Z2`, `@Z3`, `@Z4`, `@Z5` |
| % of variable | `@80% of FTP`, `@70% of max HR`, `@85% of 1RM bench press` |
| Power | `@200W` |
| Heart rate | `@140bpm` |
| Pace | `@4:30/km`, `@7:00/mi` |
| Weight | `@80kg`, `@175lb` |
| BW + weight | `@bodyweight + 20kg` |
| RPE | `@RPE 7`, `@RPE 8` |
| RIR | `@RIR 2`, `@RIR 0` |
| Rest | `@rest 90s`, `@rest 2min` |

### RPE and RIR on Headings

```
# Morning Run [Running] @RPE 7

- Warmup 10min @Z1
- Run 5km @4:30/km
- Cooldown 10min @Z1

# Upper Body [Strength Training] @RIR 2

- Back Squat 5x5rep @rest 120s
- Face Pull 3xmaxrep @15kg @RIR 3 @rest 60s
```

Workout-level `@RIR 2` applies to all steps unless overridden (Face Pull uses `@RIR 3`).

### Metadata

```
@ description: Threshold development session
@ author: Coach Smith
@ tags: cycling, intervals

# Threshold Ride [Cycling]
@ location: Indoor trainer
@ source: Garmin Connect

- Bike 5min @95% of FTP
  @ tempo: 30X1
  > Keep cadence above 90rpm.
```

Metadata attaches to documents, workouts, containers, or steps depending on position. See [SPEC.md](SPEC.md) for full rules.

### Variable Resolution

Training variables are provided by the consuming application, not stored in the workout file:

```python
resolved = owf.resolve(doc, {
    "FTP": "250W",
    "1RM bench press": "100kg",
    "bodyweight": "80kg",
    "max HR": "185bpm",
})

# Before resolve: @80% of FTP → PercentOfParam(80, "FTP")
# After resolve:  @80% of FTP → PowerParam(200.0)
```

### Notes

Step-level and workout-level notes:

```
# Easy Run [Running]

- Run 5km @4:30/km
> Aim for negative splits.

- Cooldown 10min @Z1

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
