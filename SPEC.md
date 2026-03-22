# OpenWorkoutFormat (OWF) Specification

**Version:** 3.0

## 1. Overview

OWF is a human-readable text format for describing workouts and training programs. It supports endurance training, strength training, and CrossFit-style WoDs in a single, unified format. Version 3.0 adds training programs with progression rules and simplifies container blocks.

### Design Principles

- **Human-first**: Files are readable and writable without special tools
- **Zero ambiguity**: Every line has exactly one interpretation
- **Minimal syntax**: Four prefixes (`#`, `##`, `-`, `>`) plus `@` for metadata and `---` for week separators cover all constructs
- **Application-agnostic**: Training variables (FTP, 1RM, etc.) are provided at resolve time, not stored in the file

## 2. Document Types

OWF has two document types:

### Workout Document (`.owf`)

Contains one or more workouts. No program-level structure.

```
@ description: Saturday training block
@ author: Coach Smith

# Threshold Ride [Cycling] (2026-03-09)
@ location: Indoor trainer

- 5x:
  - Bike 5min @95% FTP
  - Recover 3min @Z1

# Upper Body [Strength Training] (2026-03-09)

- Bench Press 3x8 @80kg @rest 90s

> Great session.
```

### Program Document (`.owfp`)

Contains a `##` program heading, week separators, and workouts organized into a training plan.

```
## Beginner Strength (4 weeks)
@ author: Coach Smith
@ phase: Hypertrophy
@ progression: Bench Press +2.5kg/week
@ progression: Back Squat +2.5kg/week
@ deload: week 4 x0.8

--- Week 1 ---
@ template: true
@ focus: Base volume

# Upper [Strength Training]
- Bench Press 3x8 @60kg @rest 90s
- Dumbbell Row 3x8 @24kg @rest 90s

# Lower [Strength Training]
- Back Squat 3x8 @80kg @rest 2min
- Romanian Deadlift 3x8 @60kg @rest 90s

--- Week 4 ---
@ deload: true
```

## 3. Line Types

| Prefix | Meaning | Example |
|--------|---------|---------|
| `## ` | Program heading | `## Strength Block (12 weeks)` |
| `# ` | Workout heading | `# Threshold Ride [Cycling]` |
| `--- ` | Week separator | `--- Week 1 ---` |
| `- ` | Step line | `- Run 5km @4:30/km` |
| `> ` | Note | `> Felt strong today.` |
| `@ ` | Metadata | `@ location: Downtown Gym` |
| *(blank)* | Section separator | |

### Indentation

- Steps use **2-space indentation** to denote nesting within container blocks.
- Step lines (`- `) and metadata lines (`@ `) participate in indentation; headings, week separators, and notes are always at column 0.

## 4. Metadata

Metadata lines use the `@ key: value` syntax. They can attach to documents/programs, weeks, workouts, containers, and steps.

### Syntax

```
@ key: value
```

- `@ ` prefix (at-sign followed by a space) starts a metadata line
- Key and value separated by `: ` (colon-space)
- Values are strings
- One key-value pair per line
- Keys must not contain spaces (use underscores)

### Attachment Rules

1. `@ key: value` before any heading → **document/program-level** metadata
2. `@ key: value` after a `--- Week ---` separator → attaches to that week
3. `@ key: value` at indent 0 after a `#` heading → attaches to that workout
4. `@ key: value` indented under a step or container → attaches to that step/container
5. Metadata lines appear immediately after the element they describe, before any child steps or notes

### Reserved Metadata Keys

| Level | Key | Description |
|-------|-----|-------------|
| Document | `description` | Free-text description |
| Document | `author` | Author name |
| Document | `tags` | Comma-separated tags |
| Document | `source` | Origin URL or reference |
| Document | `equipment` | Required gear (comma-separated) |
| Program | `phase` | Training phase (Hypertrophy, Strength, etc.) |
| Program | `progression` | Progression rule (see Section 13) |
| Program | `deload` | Deload rule (see Section 14) |
| Program | `cycle` | `true` if program repeats after last workout |
| Week | `template` | `true` if this week is the base template |
| Week | `focus` | Training focus for this week |
| Week | `deload` | `true` if this is a deload week |
| Workout | `location` | Where the workout takes place |
| Workout | `source` | Data origin (device, platform) |
| Workout | `focus` | Training focus or intent |
| Container | `rest_between_rounds` | Rest injected between rounds |
| Step | `tempo` | Lifting tempo (eccentric-pause-concentric-pause) |
| Step | `unilateral` | Reps/weight apply per side |
| Step | `equipment` | Specific gear for this movement |

## 5. Headings

### Program Heading (`##`)

```
## Name [(duration)]
```

- **Name**: Free text identifying the program.
- **Duration** (optional): Parenthesized duration (e.g., `(4 weeks)`, `(12 weeks)`, `(rotating)`).
- Only one `##` heading per document. If present, the document is a program (`.owfp`).

Examples:

```
## Beginner Strength (4 weeks)
## Push Pull Legs (rotating)
## Marathon Prep (16 weeks)
```

### Workout Heading (`#`)

```
# Name [type] (YYYY-MM-DD HH:MM-HH:MM) @RPE N @RIR N
```

All parts except `#` and the name are optional:

- **Name**: Free text identifying the workout.
- **Type** (optional): A bracket-enclosed tag classifying the workout. Can be any string; the FIT SDK sport type names (Appendix C) are canonical.
- **Date** (optional): A parenthesized date or date-time range. See Section 11.
- **@RPE** (optional): Workout-level Rate of Perceived Exertion (integer, 1-10).
- **@RIR** (optional): Default Reps In Reserve (integer). Individual steps may override.

Examples:

```
# Easy Run [Running]
# Morning Run [Trail Running] (2025-02-27)
# Upper Body [Strength Training] (2025-02-27 15:00-16:00)
# Full Gym Session [Strength Training] @RIR 2
# Morning Run [Running] @RPE 7
```

## 6. Steps

Every step line begins with `- ` followed by the step content. All steps use the same unified syntax.

### Syntax

```
- Action [sets×reps] [duration] [distance] [params...] [@rest duration]
```

Action names use Title Case (`Run`, `Bike`, `Bench Press`, `Pull-Up`). There is no hardcoded list of actions — any Title Case word or phrase is a valid action.

### Examples

Endurance-style:

```
- Run 5km @4:30/km
- Bike 30min @200W
- Warmup 15min @Z1
- Swim 200m @Z2
- Recover 3min @Z1
```

Strength-style:

```
- Bench Press 3x8 @80kg @rest 90s
- Pull-Up 3xmax @bodyweight + 20kg @rest 90s
- Plank 3x60s @rest 30s
- Back Squat 5x5 @RIR 3 @rest 120s
```

Mixed (any combination of fields is valid):

```
- Run 3x10min @Z3 @rest 2min
- Sled Push 4x50m @100kg
```

### Sets x Reps Formats

| Format | Meaning | Example |
|--------|---------|---------|
| `3x8` | 3 sets of 8 reps | `- Bench Press 3x8 @80kg` |
| `3x8rep` | 3 sets of 8 reps (explicit) | `- Bench Press 3x8rep @80kg` |
| `100rep` | 100 reps (no set count) | `- Pull-Up 100rep` |
| `100` | 100 reps (shorthand) | `- Pull-Up 100` |
| `3xmax` | 3 sets to failure | `- Face Pull 3xmax @15kg` |
| `3xmaxrep` | 3 sets to failure (explicit) | `- Face Pull 3xmaxrep @15kg` |

The `rep` suffix is optional — `3x8` and `3x8rep` are equivalent. Both parse to the same AST.

### Rest Step

A standalone rest period:

```
- Rest 5min
- Rest 90s
```

## 7. Container Blocks

Container blocks hold nested steps and are indicated by a trailing `:` on the step line. Children are indented by 2 spaces. There are four container types.

### Repeat

```
- Nx:
  - child step
  - child step
```

Repeats the nested steps `N` times.

**Superset and circuit** use a first-class prefix before the repeat count:

```
- superset 3x:
  - Bench Press 8rep @80kg
  - Dumbbell Row 8rep @32kg
```

```
- circuit 4x:
  @ rest_between_rounds: 90s
  - Kettlebell Swing 15rep @24kg
  - Push-Up 15rep
  - Goblet Squat 12rep @24kg
```

The style prefix sets the `style` field on the `RepeatBlock` AST node. It is informational — it does not change execution behavior. It allows consuming applications to display and label the block appropriately.

> **Fallback**: `@ style: superset` or `@ style: circuit` metadata on a plain `Nx:` block is also accepted for backward compatibility.

### Interval

```
- every <interval> for <duration>:
  - step
```

Performs the step every `<interval>` for `<duration>` total. Duration units are required on all values (e.g., `10min`, `90s`, `1h`).

**EMOM** (Every Minute On the Minute) is an interval with a 1-minute interval:

```
- every 1min for 10min:
  - Power Clean 3rep @70kg
```

**Alternating intervals** are inferred when multiple children are present. With one child, the step repeats every interval. With multiple children, they rotate:

```
- every 1min for 12min:
  - Power Clean 3rep @70kg
  - Box Jump 5rep
  - Burpee 8rep
```

This rotates: minute 1 = Power Clean, minute 2 = Box Jump, minute 3 = Burpee, minute 4 = Power Clean, etc.

### AMRAP (As Many Rounds As Possible)

```
- amrap <duration>:
  - step A
  - step B
```

Completes as many rounds as possible of the nested steps within the time limit.

### For-Time

```
- for-time [time_cap]:
  - step A
  - step B
```

Complete all nested steps as fast as possible. Optional time cap.

### Nesting

Container blocks may be nested:

```
- 3x:
  - 2x:
    - Run 30s @Z4
    - Recover 30s @Z1
  - Run 1min @Z4
  - Recover 1min @Z1
```

## 8. Parameters

Parameters modify steps with training targets. They are prefixed with `@`.

### Zone

Heart rate / effort zones:

```
@Z1  @Z2  @Z3  @Z4  @Z5
```

### Percentage of Variable

A percentage of a training variable. The variable is resolved at runtime. The word `of` is optional.

```
@80% FTP
@70% max HR
@95% 1RM bench press
@90% LTHR
```

The longer form with `of` is also accepted: `@80% of FTP`.

Known variables: `FTP`, `LTHR`, `max HR`, `TP` (threshold pace), `1RM <exercise>`.

### Power

Literal watts:

```
@200W
```

### Heart Rate

Literal beats per minute:

```
@140bpm
```

### Pace

```
@4:30/km    @7:00/mi
@pace:5:00/km          (explicit prefix form)
```

Format: `[pace:]MM:SS/unit` where unit is `km`, `mi`, or `mile`.

### Weight

```
@80kg  @175lb
```

### Bodyweight Plus

```
@bodyweight + 20kg
@bodyweight + 45lb
```

### RPE (Rate of Perceived Exertion)

```
@RPE 7    @RPE 8
```

Value is an integer (1-10 scale). Can also appear at the heading level to set workout-wide RPE.

### RIR (Reps In Reserve)

```
@RIR 2    @RIR 0
```

Value is an integer. Can also appear at the heading level to set a default RIR for all steps; individual steps may override.

### Rest (Between Sets)

```
@rest 90s    @rest 2min    @rest 120s
```

Appears at the end of a step line. Specifies rest between sets of the same exercise. For rest between different exercises, use a standalone `- Rest 90s` step. For rest between rounds of a container, use `@ rest_between_rounds: 90s` metadata on the container.

## 9. Variable Resolution

Parameters containing variable references remain unresolved until an application calls `resolve(doc, variables)` with concrete values:

```python
resolved = owf.resolve(doc, {
    "FTP": "250W",
    "1RM bench press": "100kg",
    "bodyweight": "80kg",
    "max HR": "185bpm",
})
```

### Resolution Rules

- `PercentOfParam` resolves based on the variable's unit:
  - `@80% FTP` + `FTP=250W` → `PowerParam(200.0)`
  - `@70% max HR` + `max HR=185bpm` → `HeartRateParam(130)`
  - `@80% 1RM bench press` + `1RM bench press=100kg` → `WeightParam(80.0, "kg")`
- `BodyweightPlusParam` resolves using the bodyweight variable:
  - `@bodyweight + 20kg` + `bodyweight=80kg` → `WeightParam(100.0, "kg")`
- All other param types are already concrete and pass through unchanged.

## 10. Units

### Duration

| Format | Example | Meaning |
|--------|---------|---------|
| `Ns` or `Nsec` | `30s`, `90sec` | Seconds |
| `Nmin` | `5min` | Minutes |
| `Nh`, `Nhr`, `Nhour` | `2h` | Hours |
| `NhNmin`, `NhNminNs`, `NminNs` | `1h30min`, `5min30s` | Compound |
| `MM:SS` | `1:30` | Minutes and seconds (= 90s) |
| `HH:MM:SS` | `1:30:00` | Hours, minutes, seconds |

Duration units are always required — bare numbers are not allowed. Use `10min`, `90s`, `1h30min`, etc.

### Distance

| Unit | Example | Notes |
|------|---------|-------|
| `m` | `200m` | Meters |
| `km` | `10km` | Kilometers |
| `mi` | `3mi` | Miles (short) |
| `mile` / `miles` | `1mile` | Miles (long) |
| `yd` | `400yd` | Yards |
| `ft` | `20ft` | Feet |
| `in` | `24in` | Inches |

### Pace

Format: `MM:SS/unit`

| Unit | Example |
|------|---------|
| `/km` | `4:30/km` |
| `/mi` or `/mile` | `7:00/mi` |

## 11. Notes

Notes are lines prefixed with `> `. They can appear:

1. **After a step** — attached to that step:

```
- Run 5km @4:30/km
> Aim for negative splits.
```

2. **After all steps in a workout** — attached to the workout:

```
# Easy Run [Running]

- Warmup 10min @Z1
- Run 5km @4:30/km
- Cooldown 10min @Z1

> Great session for building aerobic base.
```

3. **After a week separator** (in programs) — attached to the week:

```
--- Week 4 ---
@ deload: true
> Recovery week — reduce all weights by 20%.
```

## 12. Dates

Workout headings (`#`) may include an optional date or date-time range in parentheses.

### Formats

- Date only: `(2025-02-27)`
- Date with time range: `(2025-02-27 06:00-07:00)`
- Date with start time only: `(2025-02-27 06:00)`

Date: `YYYY-MM-DD`. Time: `HH:MM` (24-hour). Range: `HH:MM-HH:MM`.

## 13. Programs

A program document (`.owfp`) wraps workouts into a multi-week training plan with progression rules.

### Structure

```
Program (##)
  └─ Week (--- ---)
       └─ Workout (#)
            └─ Steps (-)
```

### Program Heading

```
## Name [(duration)]
```

Only one `##` heading per document. Metadata after the `##` heading attaches to the program.

### Week Separators

```
--- Name ---
```

Week separators divide the program into microcycles. The name is free text between `---` delimiters.

Examples:

```
--- Week 1 ---
@ template: true

--- Week 2 ---

--- Week 4 ---
@ deload: true

--- Cycle ---
```

### Template Weeks

A week with `@ template: true` metadata defines the base workout pattern. Subsequent weeks without explicit workout content are **derived** from the most recent template by applying progression rules.

- A template week must contain at least one workout with concrete steps.
- Only weeks that differ from the derived version need explicit content.
- If a week has explicit workouts, those override the derived version entirely.

### Progression Rules

Progression rules are program-level metadata that define how training variables change week-to-week:

```
@ progression: <action> <rule>
```

| Rule Format | Meaning | Example |
|-------------|---------|---------|
| `+Nkg/week` | Add N kg each week | `@ progression: Bench Press +2.5kg/week` |
| `+Nlb/week` | Add N lb each week | `@ progression: Back Squat +5lb/week` |
| `+N%/week` | Increase by N% each week | `@ progression: Deadlift +5%/week` |
| `+Nrep/week` | Add N reps each week | `@ progression: Pull-Up +1rep/week` |
| `-Ns/week` | Reduce rest by N seconds each week | `@ progression: Bench Press -5s/week` |

**Action matching**: The action name in the progression rule must match the step action **exactly** (case-insensitive). `Bench Press` matches `- Bench Press 3x8 @60kg` but does not match `- Incline Bench Press 3x8 @50kg`. Multiple progression rules can target the same action (e.g., weight and rest changes).

### Deload Rules

Deload rules specify recovery weeks where training load is reduced:

```
@ deload: week N xM
```

- `N` is the week number
- `M` is the multiplier (e.g., `0.8` = 80% of the previous week's load)

Example:

```
@ deload: week 4 x0.8
```

A week can also be explicitly marked as a deload via metadata:

```
--- Week 4 ---
@ deload: true
```

When `@ deload: true` on a week without explicit workouts, the program's deload rule generates the week content. When explicit workouts are present, they are used as-is.

### Cycling Programs

Programs with `@ cycle: true` repeat after the last workout/week:

```
## Push Pull Legs (rotating)
@ cycle: true

--- Cycle ---

# Push [Strength Training]
- Bench Press 3x8 @80kg @rest 90s
- Overhead Press 3x8 @50kg @rest 90s

# Pull [Strength Training]
- Deadlift 3x5 @100kg @rest 3min
- Barbell Row 3x8 @60kg @rest 90s

# Legs [Strength Training]
- Back Squat 3x8 @80kg @rest 2min
- Romanian Deadlift 3x8 @60kg @rest 90s
```

### Unscheduled Programs

Programs without dates on workout headings are unscheduled — the consuming application presents workouts in sequence (e.g., "next workout").

### Full Program Example

```
## Beginner Strength (4 weeks)
@ author: Coach Smith
@ phase: Hypertrophy
@ description: Linear progression with weekly deload
@ progression: Bench Press +2.5kg/week
@ progression: Back Squat +2.5kg/week
@ progression: Romanian Deadlift +2.5kg/week
@ progression: Dumbbell Row +2kg/week
@ deload: week 4 x0.8

--- Week 1 ---
@ template: true
@ focus: Base volume

# Day 1 — Upper [Strength Training]

- Bench Press 3x8 @60kg @rest 90s
  @ tempo: 30X1
- Dumbbell Row 3x8 @24kg @rest 90s
  @ unilateral: true
- superset 3x:
  - Lateral Raise 12 @8kg @rest 30s
  - Face Pull 15 @RPE 7 @rest 30s
- Triceps Pushdown 3x15 @RPE 8 @rest 60s

# Day 2 — Lower [Strength Training]

- Back Squat 3x8 @80kg @rest 2min
- Romanian Deadlift 3x8 @60kg @rest 90s
- Leg Press 3x10 @120kg @rest 90s
- Plank 3x60s @rest 30s

--- Week 2 ---
> Derived from template. Bench +2.5kg, Squat +2.5kg, RDL +2.5kg, Row +2kg.

--- Week 3 ---
> Derived from template. Bench +5kg, Squat +5kg, RDL +5kg, Row +4kg.

--- Week 4 ---
@ deload: true
> Auto-generated: 80% of Week 3 weights.
```

## 14. Multi-Workout Documents

An OWF workout document (`.owf`) can contain multiple workouts:

```
# Threshold Ride [Cycling] (2026-03-09)

- Warmup 10min @Z1
- 5x:
  - Bike 5min @95% FTP
  - Recover 3min @Z1
- Cooldown 10min @Z1

# Upper Body [Strength Training] (2026-03-09)

- Bench Press 3x8 @80kg @rest 90s
- Dumbbell Row 3x8 @32kg @rest 90s

> Great training day.
```

Rules:

1. `#` headings define workouts.
2. Steps between `#` headings belong to the preceding workout.
3. Notes after the last step (preceded by a blank line) attach to the workout.
4. In workout documents (`.owf`), `##` headings are not allowed.
5. In program documents (`.owfp`), workouts exist within weeks.

## Appendix A: EBNF Grammar

```ebnf
(* ===== Document types ===== *)

document        = workout_document | program_document ;

workout_document = { metadata_line } { workout } ;

program_document = program_heading newline
                   { metadata_line } { blank }
                   { week } ;

(* ===== Program elements ===== *)

program_heading = "## " name [ SP "(" duration_text ")" ] ;
duration_text   = { any_char - ")" - newline } ;

week            = week_separator newline
                  { metadata_line } { blank }
                  { note }
                  { workout } ;
week_separator  = "--- " week_name " ---" ;
week_name       = { any_char - newline } ;

(* ===== Workout elements ===== *)

workout         = heading newline { metadata_line } { blank }
                  { step_or_note } ;
heading         = "# " name [ SP "[" type "]" ] [ SP "(" date_spec ")" ]
                  { SP heading_param } ;
heading_param   = "@RPE" SP integer | "@RIR" SP integer ;
name            = { any_char - "[" - "(" - "@" - newline } ;
type            = { any_char - "]" - newline } ;
date_spec       = date [ SP time_range ] ;
date            = digit digit digit digit "-" digit digit "-" digit digit ;
time_range      = time [ "-" time ] ;
time            = digit digit ":" digit digit ;

(* ===== Metadata ===== *)

metadata_line   = "@ " key ": " value newline ;
key             = { any_char - ":" - newline - SP } ;
value           = { any_char - newline } ;

(* ===== Steps ===== *)

step_or_note    = step { step_metadata } | note | blank ;
step            = indent "- " step_content newline ;
step_metadata   = indent "  " metadata_line ;
indent          = { "  " } ;

step_content    = container_block | action_step ;

container_block = repeat | interval | amrap | for_time ;

repeat          = [ ( "superset" | "circuit" ) SP ] count "x:" ;
interval        = "every" SP duration SP "for" SP duration ":" ;
amrap           = "amrap" SP duration ":" ;
for_time        = "for-time" [ SP duration ] ":" ;

action_step     = action [ SP sets_reps ] [ SP duration ] [ SP distance ]
                  { SP param } [ SP rest_param ] ;

action          = word { ( "-" | SP ) word } ;
word            = letter { letter | digit } ;

sets_reps       = [ count "x" ] ( count | "max" ) [ "rep" | "reps" ] ;
rest_param      = "@rest" SP duration ;

(* ===== Parameters ===== *)

param           = "@" param_value ;
param_value     = zone | rpe | rir | rest_inline | pace | percent_of
                | bodyweight_plus | power | heart_rate | weight ;
zone            = "Z" digit ;
rpe             = "RPE" [ SP ] integer ;
rir             = "RIR" [ SP ] integer ;
rest_inline     = "rest" SP duration ;
pace            = [ "pace:" ] digit digit ":" digit digit "/" pace_unit ;
pace_unit       = "km" | "mi" | "mile" ;
percent_of      = number "%" SP [ "of" SP ] variable ;
variable        = { any_char - "@" - newline } ;
bodyweight_plus = "bodyweight" SP "+" SP number ( "kg" | "lb" | "lbs" ) ;
power           = integer "W" ;
heart_rate      = integer "bpm" ;
weight          = number ( "kg" | "lb" | "lbs" ) ;

(* ===== Units ===== *)

duration        = compound_dur | number time_unit | mm_ss | hh_mm_ss ;
compound_dur    = [ number "h" ] [ number "min" ] [ number "s" ] ;
time_unit       = "s" | "sec" | "min" | "h" | "hr" | "hour" ;
mm_ss           = digit+ ":" digit digit ;
hh_mm_ss        = digit+ ":" digit digit ":" digit digit ;
distance        = number dist_unit ;
dist_unit       = "m" | "km" | "mi" | "mile" | "miles" | "yd" | "ft" | "in" ;

(* ===== Primitives ===== *)

count           = digit+ ;
number          = digit+ [ "." digit+ ] ;
integer         = digit+ ;
note            = "> " { any_char - newline } ;
blank           = newline ;
```

## Appendix B: Reserved Words

### Common Actions

These are conventional action names. Any word or phrase is a valid action — this list is not exhaustive:

`Run`, `Bike`, `Swim`, `Row`, `Ski`, `Walk`, `Hike`, `Warmup`, `Cooldown`, `Recover`, `Bench Press`, `Back Squat`, `Deadlift`, `Pull-Up`, `Push-Up`, `Plank`, `Rest`, `Kettlebell Swing`, `Burpee`, `Power Clean`, `Thruster`

### Container Keywords

`amrap`, `for-time`, `every`, `for`, `superset`, `circuit`

### Parameter Prefixes

`@RPE`, `@RIR`, `@Z`, `@rest`

### Units

- **Duration:** `s`, `sec`, `min`, `h`, `hr`, `hour`
- **Distance:** `m`, `km`, `mi`, `mile`, `miles`, `yd`, `ft`
- **Weight:** `kg`, `lb`, `lbs`
- **Power:** `W`
- **Heart Rate:** `bpm`
- **Pace:** `/km`, `/mi`, `/mile`

## Appendix C: Sport Types

The `[type]` tag on headings accepts any string. The following sport type names are derived from the FIT SDK sport/sub_sport enum table and serve as the canonical list. Applications SHOULD use these names for interoperability.

### FIT SDK Sport Types (canonical)

The parser accepts any string as a sport type without validation. Applications may group these into broad categories for display purposes.

**Endurance:** Running, Treadmill Running, Street Running, Trail Running, Track Running, Indoor Running, Ultra Running, Virtual Running, Cycling, Road Cycling, Mountain Biking, Downhill Mountain Biking, Cyclocross, Track Cycling, Gravel Cycling, Mixed Surface Cycling, Bike Commuting, Virtual Cycling, Indoor Cycling, Spin, Recumbent Cycling, Hand Cycling, BMX, Swimming, Pool Swimming, Open Water Swimming, Walking, Indoor Walking, Casual Walking, Speed Walking, Hiking, Rowing, Indoor Rowing, Cross Country Skiing, Skate Skiing, Backcountry XC Skiing, Alpine Skiing, Backcountry Skiing, Resort Skiing, Snowboarding, Backcountry Snowboarding, Resort Snowboarding, Snowshoeing, Mountaineering, Paddling, Kayaking, Whitewater Kayaking, Stand Up Paddleboarding, Surfing, Sailing, Sail Racing, Inline Skating, Ice Skating, E-Biking, E-Bike Fitness, E-Mountain Biking, Elliptical, Stair Climber, Multisport

**Strength:** Strength Training, Cardio Training

**Mobility:** Yoga, Pilates, Flexibility Training

**Other:** Boxing, MMA, Racket Sport, Pickleball, Padel, HIIT, Tabata, Rock Climbing, Indoor Climbing, Bouldering, Skydiving, Golf, Disc Golf, Tactical, Breathwork, Floor Climbing, Diving, Wakeboarding, Water Skiing, Wakesurfing, Flying, Wingsuit Flying

## Appendix D: Progression Rule Reference

### Weight Progression

```
@ progression: Bench Press +2.5kg/week
@ progression: Back Squat +5lb/week
```

Adds the specified weight to every matching step each week. Applied to the weight parameter (`@Nkg` or `@Nlb`) of the step.

### Percentage Progression

```
@ progression: Deadlift +5%/week
```

Multiplies the weight by (1 + N/100) each week.

### Rep Progression

```
@ progression: Pull-Up +1rep/week
```

Adds N reps to the rep count of every matching step each week.

### Rest Reduction

```
@ progression: Bench Press -5s/week
```

Reduces the rest duration by N seconds each week. Rest cannot go below 0.

### Computation

For a step in week W (1-indexed), with the template value V:
- Linear: `V + (W - 1) * increment`
- Percentage: `V * (1 + percent/100) ^ (W - 1)`
- Deload: `previous_week_value * deload_multiplier`
