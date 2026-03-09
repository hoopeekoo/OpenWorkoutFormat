# OpenWorkoutFormat (OWF)

[![CI](https://github.com/hoopeekoo/OpenWorkoutFormat/actions/workflows/ci.yml/badge.svg)](https://github.com/hoopeekoo/OpenWorkoutFormat/actions/workflows/ci.yml)

A human-readable workout description language with a Python parser. Supports endurance (running, cycling, swimming, rowing, skiing, skating, paddling, climbing, and more), strength (weightlifting), and CrossFit WoDs (EMOM, AMRAP, for-time, circuits).

## Example

```
## Threshold Ride [Cycling]

- warmup 15min @60% of FTP
- 5x:
  - bike 5min @95% of FTP
  - recover 3min @50% of FTP
- cooldown 10min @Z1

> Felt strong through set 3, faded on 4-5.

## Upper Body [Strength Training]

- 3x superset:
  - Bench Press 3x8rep @80% of 1RM bench press @rest 90s
  - Bent-Over Row 3x8rep @60kg @RIR 2 @rest 90s

## Metcon [HIIT]

- amrap 12min:
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

Every OWF document uses `##` session headings. Files with only `#` headings are auto-wrapped in an implicit session by the parser.

```
@ description: Saturday training block
@ author: Coach Smith

## Saturday Training (2025-02-27)

# Threshold Ride [Cycling]

- warmup 15min @Z1
- 5x:
  - bike 5min @95% of FTP
  - recover 3min @50% of FTP
- cooldown 10min @Z1

# Upper Body [Strength Training]

- Bench Press 3x8rep @80kg @rest 90s

> Great session overall.
```

| Element | Syntax |
|---------|--------|
| Metadata | `@ key: value` lines before any heading (document-level) or after a heading |
| Session | `## Name [sport type] (date)` — groups `#` workouts |
| Workout | `# Name [sport type]` — child workout within a session |
| Step | `- action [sets×reps] [duration/distance] [@params] [@rest dur]` |
| Note | `> text` |
| Date | `(YYYY-MM-DD)` or `(YYYY-MM-DD HH:MM-HH:MM)` — session level only |

### Workout Types

Four modality-based types (auto-inferred from sport type or step content):

| Type | Description |
|------|-------------|
| `endurance` | Running, cycling, swimming, rowing, and all cardio activities |
| `strength` | Weightlifting, bodyweight exercises |
| `mixed` | Auto-inferred when a session has 2+ distinct child types |
| `mobility` | Stretching, yoga, recovery work |

### Sport Types

Bracket tags on headings set the specific sport type. Legacy modality tags (`[endurance]`, `[strength]`, `[mobility]`) are still accepted, but specific sport types are preferred:

```
## Morning Run [Running]
## Threshold Ride [Cycling]
## Swim Intervals [Pool Swimming]
## Full Gym Session [Strength Training]
## Metcon [HIIT]
## Yoga Flow [Yoga]
```

### Step Classification by Casing

Steps are classified by the casing of their first word — no hardcoded keyword list:

- **Lowercase → endurance**: `run`, `bike`, `swim`, `warmup`, `recover`, etc.
- **Title Case → strength**: `Bench Press`, `Pull-Up`, `Deadlift`, etc.

Any lowercase word is a valid endurance action. Users can invent new ones (`paddle-board`, `rollerblade`) without parser changes.

### Endurance Steps

```
- run 5km @4:30/km
- bike 30min @200W
- swim 200m @Z2
- warmup 15min @Z1
- recover 3min @Z1
```

### Strength Steps

Sets × reps formats:

```
- Bench Press 3x8rep @80kg @rest 90s
- Pull-Up 100rep
- Face Pull 3xmaxrep @15kg @rest 60s
- Plank 60s
```

Weight parameters:

```
- Bench Press 3x8rep @80% of 1RM bench press @rest 90s
- Dip 3x8rep @bodyweight + 20kg @rest 90s
```

RIR (Reps In Reserve) — workout-level default with per-step override:

```
## Full Gym Session [Strength Training] @RIR 2

- Back Squat 5x5rep @rest 120s
- Romanian Deadlift 3x10rep @60kg @rest 90s
- Face Pull 3xmaxrep @15kg @RIR 3 @rest 60s
```

RPE (Rate of Perceived Exertion) — on session headings:

```
## Morning Run [Running] @RPE 7

- warmup 15min @Z1
- run 5km @4:30/km
- cooldown 10min @Z1
```

### Container Blocks

**Repeat:**

```
- 5x:
  - bike 5min @200W
  - recover 3min @Z1
```

**Superset:**

```
- 3x superset:
  - Bench Press 3x8rep @80kg @rest 90s
  - Bent-Over Row 3x8rep @60kg @rest 90s
```

**Circuit:**

```
- 3x circuit:
  - Kettlebell Swing 10rep @24kg
  - Push-Up 15rep
  - Air Squat 20rep
  - Burpee 10rep
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
- amrap 12min:
  - Pull-Up 5rep
  - Push-Up 10rep
  - Air Squat 15rep
```

**For-time:**

```
- for-time:
  - run 1mile
  - Pull-Up 100rep
  - Push-Up 200rep
  - Air Squat 300rep
  - run 1mile

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
| % of variable | `@80% of FTP`, `@70% of max HR`, `@80% of 1RM bench press` |
| Power | `@200W` |
| Heart rate | `@140bpm` |
| Pace | `@4:30/km`, `@7:00/mi`, `@pace:5:00/km` |
| Weight | `@80kg`, `@175lb` |
| BW + weight | `@bodyweight + 20kg` |
| RPE | `@RPE 7`, `@RPE 8` |
| RIR | `@RIR 2`, `@RIR 0` |
| Rest | `@rest 90s`, `@rest 2min` |

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

# Before resolve: @80% of FTP → PercentOfParam(80, "FTP")
# After resolve:  @80% of FTP → PowerParam(200.0)
```

### Notes

Step-level and workout-level notes:

```
## Easy Run [Running]

- run 5km @4:30/km
> Aim for negative splits.

- cooldown 10min @Z1

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
