# OpenWorkoutFormat (OWF) Specification

**Version:** 1.1

## 1. Overview

OWF is a human-readable text format for describing workouts. It supports endurance training, strength training, and CrossFit-style WoDs (Workouts of the Day) in a single, unified format.

### Design Principles

- **Human-first**: Files are readable and writable without special tools
- **Zero ambiguity**: Every line has exactly one interpretation
- **Minimal syntax**: Three prefixes (`#`, `-`, `>`) plus `@` for metadata cover all constructs
- **Application-agnostic**: Training variables (FTP, 1RM, etc.) are provided at resolve time, not stored in the file

## 2. Document Structure

An OWF document consists of:

1. Optional **document-level metadata** (`@ key: value` lines)
2. One or more **sessions**, each containing steps and/or child workouts

```
@ description: Saturday training block
@ author: Coach Smith

## Saturday Training (2025-02-27)
@ location: Downtown Gym

# Threshold Ride [Cycling]

- 5x:
  - bike 5min @95% of FTP
  - recover 3min @Z1

# Upper Body [Strength Training]

- Bench Press 3x8rep @80kg @rest 90s

> Great session overall.
```

Every document has at least one session (`##` heading). Files with only `#` headings are auto-wrapped in an implicit unnamed session by the parser.

### Line Types

| Prefix | Meaning | Example |
|--------|---------|---------|
| `## ` | Session heading | `## Saturday Training` |
| `# ` | Child workout heading | `# Threshold Ride [Cycling]` |
| `- ` | Step line | `- run 5km @4:30/km` |
| `> ` | Note | `> Felt strong today.` |
| `@ ` | Metadata | `@ location: Downtown Gym` |
| *(blank)* | Section separator | |

### Indentation

- Steps use **2-space indentation** to denote nesting within container blocks.
- Step lines (`- `) and metadata lines (`@ `) participate in indentation; headings and notes are always at column 0.

```
- 5x:
  - bike 5min @200W
  - recover 3min @Z1
```

## 3. Metadata

Metadata lines use the `@ key: value` syntax (at-sign, space, key, colon-space, value). They can attach to documents, sessions, child workouts, containers, and steps.

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

1. `@ key: value` at the top of the document (before any heading) → **document-level** metadata
2. `@ key: value` at indent 0 after a `##` or `#` heading → attaches to that heading
3. `@ key: value` indented under a step or container → attaches to that step/container
4. Metadata lines appear immediately after the element they describe, before any child steps or notes

### Document-Level Metadata

```
@ description: Threshold development session
@ author: Coach Smith
@ tags: cycling, intervals

## Threshold Ride [Cycling]
```

### Session/Workout-Level Metadata

```
## Morning Run [Running] (2025-02-27)
@ source: Garmin Connect
@ location: Riverside Trail

- warmup 10min @Z1
```

### Step-Level Metadata

```
- Deadlift 1x1rep @95% of 1RM
  @ tempo: 20X1
  @ equipment: barbell, belt
  > Use chalk.
```

### Container-Level Metadata

```
- 3x:
  @ rest_between_rounds: 2min
  - Kettlebell Swing 15rep @24kg
  - Push-Up 15rep
```

- Metadata is informational — it does not affect parsing of steps or expressions.
- Training reference variables (FTP, 1RM, bodyweight, max HR) are **not** stored in metadata. They are provided by the consuming application at resolve time via the `resolve()` API.

### Reserved Metadata Keys

The following keys have conventional meaning:

| Level | Key | Description |
|-------|-----|-------------|
| Document | `description` | Free-text description of the workout |
| Document | `author` | Workout author name |
| Document | `tags` | Comma-separated tags |
| Document | `source` | Origin URL or reference |
| Document | `equipment` | Required gear (comma-separated) |
| Session | `location` | Where the session takes place |
| Session | `source` | Data origin (device, platform) |
| Session | `focus` | Training focus or intent |
| Container | `rest_between_rounds` | Rest injected between rounds |
| Step | `tempo` | Lifting tempo (eccentric-pause-concentric-pause) |
| Step | `unilateral` | Reps/weight apply per side |
| Step | `equipment` | Specific gear for this movement |

## 4. Headings

### Session Heading

```
## Name [type] (YYYY-MM-DD HH:MM-HH:MM) @RPE N @RIR N
```

All parts except `##` and the name are optional:

- **Name**: Free text identifying the session.
- **Type** (optional): A bracket-enclosed tag classifying the session. Can be either:
  - A **sport type** from the FIT SDK display name table (e.g., `Trail Running`, `Strength Training`, `Gravel Cycling`). See Appendix C.
  - A **legacy broad category**: `endurance`, `strength`, `mixed`, `mobility`.
  - Any other free-text string — parsers MUST accept any value in brackets.
- **Date** (optional): A parenthesized date or date-time range. See [Section 11: Dates](#11-dates).
- **@RPE** (optional): Session-level Rate of Perceived Exertion (integer, 1-10).
- **@RIR** (optional): Default Reps In Reserve for strength exercises (integer). Individual exercises may override with their own `@RIR`.

Examples:

```
## Easy Run [Running]
## Morning Run [Trail Running] (2025-02-27)
## Upper Body [Strength Training] (2025-02-27 15:00-16:00)
## Full Gym Session [Strength Training] @RIR 2
## Morning Run [Running] @RPE 7
## Sunday Ride [Gravel Cycling]
```

### Child Workout Heading

```
# Name [type] @RPE N @RIR N
```

A `#` heading creates a child workout within a session. Child workouts **may not** have dates — dates are only allowed on `##` session headings.

Examples:

```
# Threshold Ride [Cycling]
# Upper Body [Strength Training] @RIR 2
# Intervals [Indoor Cycling]
```

### Implicit Sessions

Files with only `#` headings (no `##` headings) are auto-wrapped in an implicit unnamed session by the parser for backward compatibility. If such a file has a single `#` heading with a date, the date is lifted to the implicit session.

## 5. Step Types

Every step line begins with `- ` followed by the step content.

### Casing Convention — Step Classification

Steps are classified by the casing of their first word:

- **Lowercase first word → EnduranceStep**: `run`, `bike`, `swim`, `warmup`, etc.
- **Title Case first word → StrengthStep**: `Bench Press`, `Pull-Up`, `Deadlift`, etc.

There is no hardcoded list of endurance actions. Any lowercase word is a valid endurance action, and any Title Case word starts a strength exercise. This makes the format extensible — users can invent new actions (`paddle-board`, `rollerblade`) or exercises (`Turkish Get-Up`) without parser changes.

Common endurance actions include: `run`, `bike`, `swim`, `row`, `ski`, `walk`, `hike`, `skate-ski`, `classic-ski`, `alpine-ski`, `snowboard`, `snowshoe`, `skate`, `paddle`, `kayak`, `surf`, `climb`, `elliptical`, `stairs`, `jumprope`, `ebike`, `other`, `warmup`, `cooldown`, `recover`.

### EnduranceStep

**Syntax:**

```
- action [duration] [distance] [params...]
```

Examples:

```
- run 5km @4:30/km
- bike 30min @200W
- warmup 15min @Z1
- swim 200m @Z2
- recover 3min @Z1
```

### StrengthStep

Strength exercises start with a Title Case word.

**Syntax:**

```
- exercise [sets×reps] [duration] [params...] [@rest duration]
```

**Sets × Reps formats:**

| Format | Meaning | Example |
|--------|---------|---------|
| `3x8rep` | 3 sets of 8 reps | `- Bench Press 3x8rep @80kg` |
| `3x8` | 3 sets of 8 reps (shorthand) | `- Bench Press 3x8 @80kg` |
| `100rep` | 100 reps (no set count) | `- Pull-Up 100rep` |
| `3xmaxrep` | 3 sets to failure | `- Face Pull 3xmaxrep @15kg` |

**Timed sets:**

```
- Plank 60s
```

**Rest between sets:**

```
- Bench Press 3x8rep @80kg @rest 90s
```

Examples:

```
- Bench Press 3x8rep @80kg @rest 90s
- Pull-Up 100rep
- Plank 60s
- Dip 3x8rep @bodyweight + 20kg @rest 90s
- Back Squat 5x5rep @RIR 3 @rest 120s
```

### RestStep

A standalone rest period.

```
- rest 5min
- rest 90s
```

## 6. Container Blocks

Container blocks hold nested steps and are indicated by a trailing `:` on the step line. Children are indented by 2 spaces.

### Repeat

```
- Nx:
  - child step
  - child step
```

Repeats the nested steps `N` times.

### Superset

```
- Nx superset:
  - exercise A
  - exercise B
```

Performs exercises A and B back-to-back for `N` rounds.

### Circuit

```
- Nx circuit:
  - exercise A
  - exercise B
  - exercise C
```

Performs exercises A, B, and C sequentially for `N` rounds.

### EMOM (Every Minute On the Minute)

```
- emom <duration>:
  - step
```

Performs the step at the start of every minute for the given duration. Duration defaults to minutes if no unit is given.

### Alternating EMOM

```
- emom <duration> alternating:
  - step A (odd minutes)
  - step B (even minutes)
  - step C (every third minute)
```

Alternates between the nested steps each minute.

### Custom Interval

```
- every <interval> for <duration>:
  - step
```

Performs the step every `<interval>` for `<duration>` total. Durations default to minutes if no unit is given.

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
    - run 30s @Z4
    - recover 30s @Z1
  - run 1min @Z4
  - recover 1min @Z1
```

## 7. Parameters

Parameters modify steps with training targets. They are prefixed with `@`.

### Zone

Heart rate / effort zones:

```
@Z1  @Z2  @Z3  @Z4  @Z5
```

### Percentage of Variable

A percentage of a training variable. The variable is resolved at runtime.

```
@80% of FTP
@70% of max HR
@95% of 1RM bench press
@90% of LTHR
```

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

Value is an integer (1-10 scale). Can also appear at the heading level to set session-wide RPE.

### RIR (Reps In Reserve)

```
@RIR 2    @RIR 0
```

Value is an integer indicating how many reps could have been performed before failure. Can also appear at the heading level to set a default RIR for all strength exercises; individual exercises may override with their own `@RIR`.

### Rest (Strength Steps)

```
@rest 90s    @rest 2min    @rest 120s
```

Appears at the end of a strength step line. Specifies rest between sets. Follows the same `@keyword value` pattern as `@RPE` and `@RIR`.

## 8. Variable Resolution

Parameters containing variable references remain unresolved until an application calls `resolve(doc, variables)` with concrete values:

```python
resolved = owf.resolve(doc, {
    "FTP": "250W",
    "1RM bench press": "100kg",
    "bodyweight": "80kg",
    "max HR": "185bpm",
})
```

Variable values are strings in the format `<number><unit>` (e.g., `"250W"`, `"100kg"`, `"185bpm"`).

### Resolution Rules

- `PercentOfParam` resolves to the appropriate literal type based on the variable's unit:
  - `@80% of FTP` + `FTP=250W` → `PowerParam(200.0)`
  - `@70% of max HR` + `max HR=185bpm` → `HeartRateParam(130)`
  - `@80% of 1RM bench press` + `1RM bench press=100kg` → `WeightParam(80.0, "kg")`
- `BodyweightPlusParam` resolves using the bodyweight variable:
  - `@bodyweight + 20kg` + `bodyweight=80kg` → `WeightParam(100.0, "kg")`
- All other param types (`ZoneParam`, `PowerParam`, `HeartRateParam`, `PaceParam`, `WeightParam`, `RPEParam`, `RIRParam`) are already concrete and pass through unchanged.

## 9. Units

### Duration

| Format | Example | Meaning |
|--------|---------|---------|
| `Ns` or `Nsec` | `30s`, `90sec` | Seconds |
| `Nmin` | `5min` | Minutes |
| `Nh`, `Nhr`, `Nhour` | `2h` | Hours |
| `NhNmin`, `NhNminNs`, `NminNs` | `1h30min`, `5min30s` | Compound |
| `MM:SS` | `1:30` | Minutes and seconds (= 90s) |
| `HH:MM:SS` | `1:30:00` | Hours, minutes, seconds |

Bare numbers in EMOM, AMRAP, Custom Interval, and For-Time default to **minutes**.

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

## 10. Notes

Notes are lines prefixed with `> `. They can appear:

1. **After a step** — attached to that step:

```
- run 5km @4:30/km
> Aim for negative splits.
```

2. **After all steps in a workout** — attached to the workout:

```
## Easy Run [Running]

- warmup 10min @Z1
- run 5km @4:30/km
- cooldown 10min @Z1

> Great session for building aerobic base.
```

## 11. Dates

Session headings (`##`) may include an optional date or date-time range in parentheses, placed after the name and type. Dates are **only allowed on `##` session headings**, not on `#` child workout headings.

### Date Only

```
## Morning Run [Running] (2025-02-27)
```

### Date with Time Range

```
## Morning Run [Running] (2025-02-27 06:00-07:00)
```

### Date with Start Time Only

```
## Morning Run [Running] (2025-02-27 06:00)
```

### Format

- Date: `YYYY-MM-DD`
- Time: `HH:MM` (24-hour)
- Range: `HH:MM-HH:MM`

## 12. Session Hierarchy

Every OWF document uses `##` session headings. Sessions may contain steps directly and/or `#` child workouts.

```
## Saturday Training (2025-02-27)

- warmup 10min @Z1

# Threshold Ride [Cycling]

- 5x:
  - bike 5min @95% of FTP
  - recover 3min @Z1

# Upper Body [Strength Training]

- Bench Press 3x8rep @80kg @rest 90s
- Bent-Over Row 3x8rep @60kg @rest 90s

> Great session overall.
```

### Rules

1. `##` headings define **sessions** — the top-level grouping in every document.
2. `#` headings after a `##` become **child workouts** of that session.
3. Steps between a `##` heading and the first `#` are **session-level steps** (e.g., a shared warmup).
4. Notes after the last `#` section attach to the session.
5. Dates are only allowed on `##` session headings. Dates on `#` child headings raise an error.
6. **Implicit sessions**: Files with only `#` headings (no `##`) are auto-wrapped in an unnamed session by the parser. If such a file has a single `#` heading with a date, the date is lifted to the implicit session.
7. **Mixed inference:** If a `##` session has no explicit `[type]` and contains child workouts with 2 or more distinct types, its type is automatically inferred as `mixed`. The `[mixed]` tag is never written to `.owf` files — it is re-inferred on each parse.

## Appendix A: EBNF Grammar

```ebnf
document        = { metadata_line } { session } ;
metadata_line   = "@ " key ": " value newline ;
key             = { any_char - ":" - newline - SP } ;
value           = { any_char - newline } ;

session         = session_heading newline { metadata_line } { blank }
                  { step_or_note | child_workout } ;
session_heading = "## " name [ SP "[" type "]" ] [ SP "(" date_spec ")" ]
                  { SP heading_param } ;
child_workout   = child_heading newline { metadata_line } { blank }
                  { step_or_note } ;
child_heading   = "# " name [ SP "[" type "]" ] { SP heading_param } ;
heading_param   = "@RPE" SP integer | "@RIR" SP integer ;
name            = { any_char - "[" - "(" - newline } ;
type            = { any_char - "]" - newline } ;
date_spec       = date [ SP time_range ] ;
date            = digit digit digit digit "-" digit digit "-" digit digit ;
time_range      = time [ "-" time ] ;
time            = digit digit ":" digit digit ;

step_or_note    = step { step_metadata } | note | blank ;
step            = indent "- " step_content newline ;
step_metadata   = indent "  " metadata_line ;
indent          = { "  " } ;

step_content    = rest_step
                | container_block
                | endurance_step
                | strength_step ;

rest_step       = "rest" SP duration ;
container_block = repeat | superset | circuit | emom | alt_emom
                | custom_interval | amrap | for_time ;

repeat          = count "x:" ;
superset        = count "x superset:" ;
circuit         = count "x circuit:" ;
emom            = "emom" SP duration ":" ;
alt_emom        = "emom" SP duration SP "alternating:" ;
custom_interval = "every" SP duration SP "for" SP duration ":" ;
amrap           = "amrap" SP duration ":" ;
for_time        = "for-time" [ SP duration ] ":" ;

endurance_step  = action [ SP duration ] [ SP distance ] { SP param } ;
strength_step   = exercise [ SP sets_reps ] [ SP duration ] { SP param }
                  [ SP rest_param ] ;

action          = lower_word { ( "-" | SP ) lower_word } ;
exercise        = title_word { ( "-" | SP ) title_word } ;
lower_word      = lower { letter | digit } ;
title_word      = upper { letter | digit } ;

sets_reps       = [ count "x" ] ( count | "max" ) [ "rep" | "reps" ] ;
rest_param      = "@rest" SP duration ;

param           = "@" param_value ;
param_value     = zone | rpe | rir | rest_inline | pace | percent_of
                | bodyweight_plus | power | heart_rate | weight ;
zone            = "Z" digit ;
rpe             = "RPE" [ SP ] integer ;
rir             = "RIR" [ SP ] integer ;
rest_inline     = "rest" SP duration ;
pace            = [ "pace:" ] digit digit ":" digit digit "/" pace_unit ;
pace_unit       = "km" | "mi" | "mile" ;
percent_of      = number "%" SP "of" SP variable ;
variable        = { any_char - "@" - newline } ;
bodyweight_plus = "bodyweight" SP "+" SP number ( "kg" | "lb" | "lbs" ) ;
power           = integer "W" ;
heart_rate      = integer "bpm" ;
weight          = number ( "kg" | "lb" | "lbs" ) ;

duration        = compound_dur | number time_unit | mm_ss | hh_mm_ss ;
compound_dur    = [ number "h" ] [ number "min" ] [ number "s" ] ;
time_unit       = "s" | "sec" | "min" | "h" | "hr" | "hour" ;
mm_ss           = digit+ ":" digit digit ;
hh_mm_ss        = digit+ ":" digit digit ":" digit digit ;
distance        = number dist_unit ;
dist_unit       = "m" | "km" | "mi" | "mile" | "miles" | "yd" | "ft" | "in" ;

count           = digit+ ;
number          = digit+ [ "." digit+ ] ;
integer         = digit+ ;
note            = "> " { any_char - newline } ;
blank           = newline ;
```

## Appendix B: Reserved Words

### Common Endurance Actions

These are conventional lowercase action names. Any lowercase word is a valid endurance action — this list is not exhaustive:

`run`, `bike`, `swim`, `row`, `ski`, `walk`, `hike`, `skate-ski`, `classic-ski`, `alpine-ski`, `snowboard`, `snowshoe`, `skate`, `paddle`, `kayak`, `surf`, `climb`, `elliptical`, `stairs`, `jumprope`, `ebike`, `other`, `warmup`, `cooldown`, `recover`

### Container Keywords

`superset`, `circuit`, `emom`, `alternating`, `amrap`, `for-time`, `every`, `for`

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

### Legacy Broad Categories

These single-word values are retained for backward compatibility and simplicity:

`endurance`, `strength`, `mobility`, `mixed`

### FIT SDK Sport Types (canonical)

Applications map these to broad categories for type inference. The parser accepts them all without validation.

**Endurance:** Running, Treadmill Running, Street Running, Trail Running, Track Running, Indoor Running, Ultra Running, Virtual Running, Cycling, Road Cycling, Mountain Biking, Downhill Mountain Biking, Cyclocross, Track Cycling, Gravel Cycling, Mixed Surface Cycling, Bike Commuting, Virtual Cycling, Indoor Cycling, Spin, Recumbent Cycling, Hand Cycling, BMX, Swimming, Pool Swimming, Open Water Swimming, Walking, Indoor Walking, Casual Walking, Speed Walking, Hiking, Rowing, Indoor Rowing, Cross Country Skiing, Skate Skiing, Backcountry XC Skiing, Alpine Skiing, Backcountry Skiing, Resort Skiing, Snowboarding, Backcountry Snowboarding, Resort Snowboarding, Snowshoeing, Mountaineering, Paddling, Kayaking, Whitewater Kayaking, Stand Up Paddleboarding, Surfing, Sailing, Sail Racing, Inline Skating, Ice Skating, E-Biking, E-Bike Fitness, E-Mountain Biking, Elliptical, Stair Climber, Multisport

**Strength:** Strength Training, Cardio Training

**Mobility:** Yoga, Pilates, Flexibility Training

**Other:** Boxing, MMA, Racket Sport, Pickleball, Padel, HIIT, AMRAP, EMOM, Tabata, Rock Climbing, Indoor Climbing, Bouldering, Skydiving, Golf, Disc Golf, Tactical, Breathwork, Floor Climbing, Diving, Wakeboarding, Water Skiing, Wakesurfing, Flying, Wingsuit Flying
