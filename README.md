# OpenWorkoutFormat (OWF)

[![CI](https://github.com/hoopeekoo/OpenWorkoutFormat/actions/workflows/ci.yml/badge.svg)](https://github.com/hoopeekoo/OpenWorkoutFormat/actions/workflows/ci.yml)
**Spec Version: 4.0** | **License: MIT** | **Zero Dependencies**

A human-readable, machine-parseable language for workouts and training programs.
One format for endurance, strength, and everything in between.

```
# Threshold Ride [Cycling] (2026-04-05) @RPE 7
@ location: Indoor trainer

> Sweet spot session. Keep cadence 85-95 RPM.

- Warmup 15min @Z1:power
- 4x:
  - Bike 8min @95%FTP
  - Recover 4min @Z1:power
- Cooldown 10min @Z1

# Push Day [Strength Training] @RIR 2

- Bench Press 4x6 @82.5kg @tempo 30X1 @rest 2min
- superset 3x:
  - Overhead Press 8 @40kg @rest 60s
  - Lateral Raise 12 @10kg @rest 60s
- Triceps Pushdown 3x15 @RPE 8 @rest 60s

# Cindy [HIIT]

- amrap 20min:
  - Pull-Up 5
  - Push-Up 10
  - Air Squat 15
```

Three workouts. Three disciplines. One file a human can read and a machine can parse.

## Why OWF?

- **Human-first** -- Write and read workouts in plain text. No app required, no proprietary format.
- **One format for all training** -- Running intervals, barbell programs, CrossFit metcons, triathlon bricks, yoga flows. One syntax handles it all.
- **Machine-readable** -- A four-phase parser turns `.owf` text into a typed AST with source locations on every node. Build real software on top.
- **Application-agnostic** -- Training variables like FTP, 1RM, and max HR are supplied by your app at resolve time. The same workout template works for every athlete.
- **Plain text is powerful** -- Version control your training with git. Grep across a season of workouts. Generate programs with LLMs. Print a workout card. Share it in a chat message.

## OWF vs. Alternatives

| | OWF | FIT / TCX | Workout JSON schemas | App-specific formats |
|---|---|---|---|---|
| Human-readable | Yes -- plain text | No -- binary or verbose XML | Barely -- deeply nested | Sometimes -- varies |
| Machine-parseable | Yes -- typed AST | Yes -- with SDK | Yes -- with schema | Depends on API |
| Strength + endurance | Yes -- unified syntax | Endurance only | Usually one or the other | Depends on app |
| Vendor lock-in | None -- open spec | Device-specific | Schema-specific | Yes |
| Version control | Excellent -- text diffs | Poor | Noisy diffs | Usually impossible |

## Installation

```bash
pip install -e .
```

Zero runtime dependencies. Python 3.10+.

## Quick Start

```python
import owf

# Parse from text or file
doc = owf.parse(open("workout.owf").read())
doc = owf.load("workout.owf")

# Resolve training variables against athlete-specific values
resolved = owf.resolve(doc, {
    "FTP": "250W",
    "1RM bench press": "100kg",
    "bodyweight": "80kg",
    "max HR": "185bpm",
})
# Before: @80% FTP  --> PercentOfParam(80, "FTP")
# After:  @80% FTP  --> PowerParam(200.0)

# Serialize back to .owf text (round-trip safe)
text = owf.dumps(resolved)
```

## CLI

```bash
# Pretty-print a workout
owf workout.owf

# Output the AST as JSON (for piping into other tools)
owf workout.owf --json

# Resolve variable expressions before output
owf workout.owf --resolve
```

## Examples

### Easy Recovery Run

```
# Recovery Run [Running]

- Warmup 10min @Z1
- Run 6km @5:30/km
- Cooldown 5min @Z1
```

### Cycling Threshold Intervals

```
# Sweet Spot [Cycling] @RPE 7

- Warmup 15min @60%FTP
- 5x:
  - Bike 5min @92%FTP
  - Recover 3min @Z1:power
- Cooldown 10min @Z1
```

### Swim Intervals

```
# Threshold Swim [Pool Swimming]

- Swim 400m @Z1
- 6x:
  - Swim 100m @1:32/100m
  - Recover 50m @Z1
- Swim 200m @Z1
```

### Upper Body Strength

```
# Upper Body [Strength Training] @RIR 2

- Bench Press 4x6 @80kg @tempo 30X1 @rest 2min
- superset 3x:
  - Dumbbell Row 8 @34kg @rest 60s
  - Incline Dumbbell Press 8 @28kg @rest 60s
- Pull-Up 3xmax @bodyweight + 15kg @rest 90s
- Cable Face Pull 3x15 @RPE 7 @rest 45s
```

### CrossFit "Fran"

```
# Fran [HIIT]

> Classic 21-15-9. Target sub-4 minutes.

- for-time 10min:
  - Thruster 21 @43kg
  - Pull-Up 21
  - Thruster 15 @43kg
  - Pull-Up 15
  - Thruster 9 @43kg
  - Pull-Up 9
```

### Alternating EMOM

```
# Power EMOM [HIIT]

- every 1min for 12min:
  - Power Clean 3 @70kg
  - Front Squat 5 @60kg
  - Burpee Over Bar 8
```

### Triathlon Brick Session

```
@ description: Olympic-distance race simulation
@ author: Coach Rivera

# Swim Leg [Open Water Swimming] (2026-06-14 07:00)
@ location: Lake Zurich

- Swim 400m @Z1
- 3x:
  - Swim 200m @Z3
  - Recover 100m @Z1
- Swim 300m @Z2

# Bike Leg [Cycling] (2026-06-14 08:00-09:00)
@ location: Zurich lake loop

- Warmup 10min @Z1
- Bike 35min @85%FTP
- 3x:
  - Bike 3min @95%FTP
  - Recover 2min @Z1
- Cooldown 5min @Z1

# Brick Run [Running] (2026-06-14 09:05)

> Legs will feel heavy. Push through the first km.

- Run 3km @4:50/km
- Run 2km @4:30/km
- Cooldown 1km @Z1
```

### 4-Week Strength Program

Programs use the `.owfp` extension and add week separators, progression rules, and deload logic:

```
## Hypertrophy Block (4 weeks)
@ author: Coach Smith
@ phase: Hypertrophy
@ progression: Bench Press +2.5kg/week
@ progression: Back Squat +2.5kg/week
@ progression: Romanian Deadlift +2.5kg/week
@ deload: week 4 x0.8

--- Week 1 ---
@ template: true
@ focus: Base volume

# Upper [Strength Training]

- Bench Press 3x8 @60kg @tempo 30X1 @rest 90s
- Dumbbell Row 3x8 @24kg @rest 90s
- superset 3x:
  - Lateral Raise 12 @8kg @rest 30s
  - Face Pull 15 @RPE 7 @rest 30s

# Lower [Strength Training]

- Back Squat 3x8 @80kg @rest 2min
- Romanian Deadlift 3x8 @60kg @rest 90s
- Leg Press 3x10 @120kg @rest 90s

--- Week 2 ---
@ description: Bench 62.5kg, Squat 82.5kg, RDL 62.5kg

--- Week 3 ---
@ description: Bench 65kg, Squat 85kg, RDL 65kg

--- Week 4 ---
@ deload: true
@ description: 80% of week 3 weights
```

Weeks 2-4 are derived from the Week 1 template by applying progression and deload rules automatically.

## Format at a Glance

### Line Types

| Prefix | Meaning | Example |
|--------|---------|---------|
| `## ` | Program heading | `## Strength Block (12 weeks)` |
| `# ` | Workout heading | `# Threshold Ride [Cycling] (2026-04-05)` |
| `--- ` | Week separator | `--- Week 1 ---` |
| `- ` | Step | `- Run 5km @4:30/km` |
| `> ` | Description | `> Keep cadence above 90.` |
| `@ ` | Metadata | `@ location: Downtown Gym` |

### Parameters

| Type | Syntax | Example |
|------|--------|---------|
| Zone | `@Zn` | `@Z2`, `@Z4:power`, `@Z3:hr` |
| Typed % | `@N%TARGET` | `@95%FTP`, `@85%1RM`, `@88%LTHR` |
| % of variable | `@N% VAR` | `@80% FTP`, `@70% max HR` |
| Power | `@NW` | `@200W` |
| Heart rate | `@Nbpm` | `@140bpm` |
| Pace | `@MM:SS/unit` | `@4:30/km`, `@1:45/500m`, `@1:32/100m` |
| Weight | `@Nkg` / `@Nlb` | `@80kg`, `@175lb` |
| BW + weight | `@bodyweight + N` | `@bodyweight + 20kg` |
| RPE | `@RPE N` | `@RPE 7` |
| RIR | `@RIR N` | `@RIR 2` |
| Tempo | `@tempo NNNN` | `@tempo 30X1`, `@tempo 4010` |
| Set type | `@type` | `@warmup`, `@drop`, `@failure`, `@cluster` |
| Rest | `@rest DUR` | `@rest 90s`, `@rest 2min` |

### Container Blocks

| Block | Syntax | Use |
|-------|--------|-----|
| Repeat | `Nx:` | Repeat steps N times |
| Superset | `superset Nx:` | Paired exercises |
| Circuit | `circuit Nx:` | Rotation through exercises |
| Interval | `every DUR for DUR:` | Timed intervals (EMOM, etc.) |
| AMRAP | `amrap DUR:` | As many rounds as possible |
| For-time | `for-time [CAP]:` | Complete for time |

Full formal specification with EBNF grammar: **[SPEC.md](SPEC.md)**

## What You Can Build

OWF is a format, not a product. Here is what you can build on top of it:

- **Coaching platforms** -- Coaches author programs in plain text; athletes see structured workouts in an app
- **Device sync** -- Convert OWF to Garmin (FIT), Wahoo, or Zwift (ZWO) structured workout formats
- **Training analytics** -- Parse workout logs for volume tracking, tonnage calculations, and progressive overload analysis
- **AI coaching** -- LLMs can generate and parse OWF natively; the format is designed for both human and machine authoring
- **Workout libraries** -- Git repositories of benchmark WoDs, race prep plans, and community training templates
- **Calendar integration** -- Dated workouts map directly to calendar events
- **Cross-platform interchange** -- Athletes switch apps without losing training history; coaches share programs across platforms

## Design Principles

From the [specification](SPEC.md):

- **Human-first** -- Files are readable and writable without special tools
- **Zero ambiguity** -- Every line has exactly one interpretation
- **Minimal syntax** -- Four prefixes (`#`, `-`, `>`, `@`) plus `---` for week separators cover all constructs
- **Application-agnostic** -- Training variables are provided at resolve time, not stored in the file

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/ -v          # 227 tests
mypy src/                 # strict mode
ruff check src/           # linting
```

Zero runtime dependencies -- stdlib imports only.

## License

MIT
