# OpenWorkoutFormat (OWF) Specification

**Version:** 1.0

## 1. Overview

OWF is a human-readable text format for describing workouts. It supports endurance training, strength training, and CrossFit-style WoDs (Workouts of the Day) in a single, unified format.

### Design Principles

- **Human-first**: Files are readable and writable without special tools
- **Zero ambiguity**: Every line has exactly one interpretation
- **Minimal syntax**: Four prefixes (`#`, `-`, `>`, `---`) cover all constructs
- **Application-agnostic**: Training variables (FTP, 1RM, etc.) are provided at resolve time, not stored in the file

## 2. Document Structure

An OWF document consists of:

1. Optional **metadata** block (frontmatter)
2. One or more **workout** sections

```
---
description: Saturday training block
author: Coach Smith
---

# Workout Name [type]

- step description
- step description

> Note text
```

### Line Types

| Prefix | Meaning | Example |
|--------|---------|---------|
| `---` | Metadata fence (open/close) | `---` |
| `## ` | Session heading (two-level) | `## Saturday Training` |
| `# ` | Workout heading | `# Threshold Ride [bike]` |
| `- ` | Step line | `- run 5km @4:30/km` |
| `> ` | Note | `> Felt strong today.` |
| *(blank)* | Section separator | |

### Indentation

- Steps use **2-space indentation** to denote nesting within container blocks.
- Only step lines (`- `) participate in indentation; headings, notes, and metadata are always at column 0.

```
- 5x:
  - bike 5min @200W
  - recover 3min @easy
```

## 3. Metadata (Frontmatter)

A `---` fenced block at the top of the document contains key-value pairs for document metadata.

```
---
description: Threshold development session
author: Coach Smith
tags: cycling, intervals
---
```

- Keys and values are separated by `: ` (colon-space).
- Keys may contain spaces and special characters.
- Values are strings.
- Metadata is informational — it does not affect parsing of steps or expressions.
- Training reference variables (FTP, 1RM, bodyweight, max HR) are **not** stored in metadata. They are provided by the consuming application at resolve time via the `resolve()` API.

### Reserved Metadata Keys

The following keys have conventional meaning:

| Key | Description |
|-----|-------------|
| `description` | Free-text description of the workout |
| `author` | Workout author name |
| `tags` | Comma-separated tags |

## 4. Headings

### Workout Heading

```
# Name [type] (YYYY-MM-DD HH:MM-HH:MM) @RPE N @RIR N
```

All parts except `#` and the name are optional:

- **Name**: Free text identifying the workout.
- **Type** (optional): A bracket-enclosed tag classifying the workout. Common types: `endurance`, `strength`, `mixed`, `mobility`.
- **Date** (optional): A parenthesized date or date-time range. See [Section 11: Dates](#11-dates).
- **@RPE** (optional): Workout-level Rate of Perceived Exertion (float, 1-10).
- **@RIR** (optional): Default Reps In Reserve for strength exercises (integer). Individual exercises may override with their own `@RIR`.

Examples:

```
# Easy Run
# Threshold Ride [endurance]
# Morning Run [endurance] (2025-02-27)
# Upper Body [strength] (2025-02-27 15:00-16:00)
# Full Gym Session [strength] @RIR 2
# Morning Run [endurance] @RPE 7
# Upper Body [strength] (2025-02-27) @RPE 8 @RIR 2
```

### Session Heading (Two-Level)

```
## Session Name [type] (date) @RPE N @RIR N
```

A `##` heading creates a session that contains `#` child workouts. See [Section 12: Two-Level Hierarchy](#12-two-level-hierarchy).

## 5. Step Types

Every step line begins with `- ` followed by the step content.

### EnduranceStep

An endurance step starts with one of the known actions:

| Action | Description |
|--------|-------------|
| `run` | Running |
| `bike` | Cycling |
| `swim` | Swimming |
| `row` | Rowing |
| `ski` | Skiing / ski erg |
| `walk` | Walking |
| `hike` | Hiking |
| `skate-ski` | XC skate skiing |
| `classic-ski` | XC classic skiing |
| `alpine-ski` | Downhill skiing |
| `snowboard` | Snowboarding |
| `snowshoe` | Snowshoeing |
| `skate` | Inline / ice skating |
| `paddle` | SUP / kayak / canoe |
| `kayak` | Kayaking |
| `surf` | Surfing / windsurfing / kite |
| `climb` | Mountaineering |
| `elliptical` | Elliptical trainer |
| `stairs` | Stair climber |
| `jumprope` | Jump rope |
| `ebike` | E-bike riding |
| `other` | Other / uncategorized activity |
| `warmup` | Warm-up (any modality) |
| `cooldown` | Cool-down (any modality) |
| `recover` | Recovery interval |

**Syntax:**

```
- action [duration] [distance] [params...]
```

Examples:

```
- run 5km @4:30/km
- bike 30min @200W
- warmup 15min @easy
- swim 200m @easy
- recover 3min @easy
```

### StrengthStep

Any step whose first word is **not** a known endurance action is classified as a strength step.

**Syntax:**

```
- exercise [sets×reps] [duration] [params...] [rest:duration]
```

**Sets × Reps formats:**

| Format | Meaning | Example |
|--------|---------|---------|
| `3x8rep` | 3 sets of 8 reps | `- bench press 3x8rep @80kg` |
| `3x8` | 3 sets of 8 reps (shorthand) | `- bench press 3x8 @80kg` |
| `100rep` | 100 reps (no set count) | `- pull-up 100rep` |
| `3xmaxrep` | 3 sets to failure | `- face pull 3xmaxrep @15kg` |

**Timed sets:**

```
- plank 60s
```

**Rest between sets:**

```
- bench press 3x8rep @80kg rest:90s
```

Examples:

```
- bench press 3x8rep @80kg rest:90s
- pull-up 100rep
- plank 60s
- dip 3x8rep @bodyweight + 20kg rest:90s
- back squat 5x5rep @RIR 3 rest:120s
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
    - run 30s @hard
    - recover 30s @easy
  - run 1min @hard
  - recover 1min @easy
```

## 7. Parameters

Parameters modify steps with training targets. They are prefixed with `@`.

### Intensity

Named effort levels:

```
@easy  @moderate  @hard  @max  @threshold  @tempo
```

### Pace

```
@4:30/km    @7:00/mi
@pace:5:00/km          (explicit prefix form)
```

Format: `MM:SS/unit` where unit is `km`, `mi`, or `mile`.

### Power

```
@200W                  (literal watts)
@80% of FTP            (percentage of variable)
@FTP                   (variable reference)
```

### Weight

```
@80kg  @175lb          (literal weight)
@80% of 1RM bench press  (percentage of variable)
@bodyweight + 20kg     (binary expression)
```

### Heart Rate

```
@140bpm                (literal bpm)
@70% of max HR         (percentage of variable)
@Z2  @Z3               (heart rate zone)
```

### RPE (Rate of Perceived Exertion)

```
@RPE 7    @RPE 8.5
```

Value is a float (typically 1-10 scale). Can also appear at the heading level to set workout-wide RPE.

### RIR (Reps In Reserve)

```
@RIR 2    @RIR 0
```

Value is an integer indicating how many reps could have been performed before failure. Can also appear at the heading level to set a default RIR for all strength exercises; individual exercises may override with their own `@RIR`.

### Rest (Strength Steps)

```
rest:90s    rest:2min    rest:120s
```

Appears at the end of a strength step line. Specifies rest between sets.

## 8. Expressions

Expressions appear as parameter values and are resolved against caller-supplied variables.

### Literal

A numeric value with optional unit.

```
200W    80kg    140bpm    15    24in
```

### VarRef (Variable Reference)

A reference to a variable provided at resolve time. Variable names may contain spaces.

```
FTP
1RM bench press
bodyweight
max HR
```

### Percentage

A percentage of another expression.

```
80% of FTP
70% of max HR
95% of 1RM bench press
```

### BinOp (Binary Operation)

Addition or subtraction of two expressions.

```
bodyweight + 20kg
FTP - 50W
```

### Resolution

Expressions containing variable references remain as unresolved `VarRef` or `Percentage` nodes until an application calls `resolve(doc, variables)` with concrete values:

```python
resolved = owf.resolve(doc, {
    "FTP": "250W",
    "1RM bench press": "100kg",
    "bodyweight": "80kg",
    "max HR": "185bpm",
})
```

Variable values are strings in the format `<number><unit>` (e.g., `"250W"`, `"100kg"`, `"185bpm"`).

## 9. Units

### Duration

| Format | Example | Meaning |
|--------|---------|---------|
| `Ns` or `Nsec` | `30s`, `90sec` | Seconds |
| `Nmin` | `5min` | Minutes |
| `Nh`, `Nhr`, `Nhour` | `2h` | Hours |
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
# Easy Run [run]

- warmup 10min @easy
- run 5km @4:30/km
- cooldown 10min @easy

> Great session for building aerobic base.
```

## 11. Dates

Workout headings may include an optional date or date-time range in parentheses, placed after the name and type.

### Date Only

```
# Morning Run [run] (2025-02-27)
```

### Date with Time Range

```
# Morning Run [run] (2025-02-27 06:00-07:00)
```

### Date with Start Time Only

```
# Morning Run [run] (2025-02-27 06:00)
```

### Format

- Date: `YYYY-MM-DD`
- Time: `HH:MM` (24-hour)
- Range: `HH:MM-HH:MM`

Dates apply to both `#` and `##` headings.

## 12. Two-Level Hierarchy

Documents may use `##` session headings to group `#` child workouts.

```
## Saturday Training (2025-02-27)

- warmup 10min @easy

# Threshold Ride [bike]

- 5x:
  - bike 5min @200W
  - recover 3min @easy

# Upper Body [strength]

- bench press 3x8rep @80kg rest:90s
- bent-over row 3x8rep @60kg rest:90s

> Great session overall.
```

### Rules

1. If any `##` heading appears in the document, two-level mode is activated.
2. `#` headings after a `##` become **child workouts** of that session.
3. Steps between a `##` heading and the first `#` are **session-level steps** (e.g., a shared warmup).
4. `#` headings before the first `##` remain **top-level workouts** (backward compatibility).
5. Notes after the last `#` section attach to the session workout.
6. If no `##` headings exist, each `#` heading is a top-level workout (flat mode).
7. **Mixed inference:** If a `##` session has no explicit `[type]` and contains child workouts with 2 or more distinct types, its type is automatically inferred as `mixed`. The `[mixed]` tag is never written to `.owf` files — it is re-inferred on each parse.

## Appendix A: EBNF Grammar

```ebnf
document        = [ frontmatter ] { workout } ;
frontmatter     = "---" newline { kv_pair newline } "---" newline ;
kv_pair         = key ":" SP value ;
key             = { any_char - ":" - newline } ;
value           = { any_char - newline } ;

workout         = heading newline { blank } { step_or_note } ;
heading         = ( "# " | "## " ) name [ SP "[" type "]" ] [ SP "(" date_spec ")" ] { SP heading_param } ;
heading_param   = "@RPE" SP number | "@RIR" SP integer ;
name            = { any_char - "[" - "(" - newline } ;
type            = { word_char } ;
date_spec       = date [ SP time_range ] ;
date            = digit digit digit digit "-" digit digit "-" digit digit ;
time_range      = time [ "-" time ] ;
time            = digit digit ":" digit digit ;

step_or_note    = step | note | blank ;
step            = indent "- " step_content newline ;
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
strength_step   = exercise [ SP sets_reps ] [ SP duration ] { SP param } [ SP rest_param ] ;

action          = "run" | "bike" | "swim" | "row" | "ski"
                | "walk" | "hike" | "skate-ski" | "classic-ski"
                | "alpine-ski" | "snowboard" | "snowshoe" | "skate"
                | "paddle" | "kayak" | "surf" | "climb"
                | "elliptical" | "stairs" | "jumprope" | "ebike"
                | "other" | "warmup" | "cooldown" | "recover" ;
exercise        = word { SP word } ;

sets_reps       = [ count "x" ] ( count | "max" ) [ "rep" | "reps" ] ;
rest_param      = "rest:" duration ;

param           = "@" param_value ;
param_value     = pace | intensity | rpe | rir | hr_zone | expression ;
pace            = [ "pace:" ] digit digit ":" digit digit "/" pace_unit ;
pace_unit       = "km" | "mi" | "mile" ;
intensity       = "easy" | "moderate" | "hard" | "max" | "threshold" | "tempo" ;
rpe             = "RPE" [ SP ] number ;
rir             = "RIR" [ SP ] integer ;
hr_zone         = "Z" digit ;

expression      = percentage | binop | literal | varref ;
percentage      = number "%" SP "of" SP expression ;
binop           = expression SP ( "+" | "-" ) SP expression ;
literal         = number [ unit ] ;
varref          = { any_char - "@" - newline } ;

duration        = number time_unit | mm_ss | hh_mm_ss ;
time_unit       = "s" | "sec" | "min" | "h" | "hr" | "hour" ;
mm_ss           = digit+ ":" digit digit ;
hh_mm_ss        = digit+ ":" digit digit ":" digit digit ;
distance        = number dist_unit ;
dist_unit       = "m" | "km" | "mi" | "mile" | "miles" | "yd" | "ft" ;

count           = digit+ ;
number          = digit+ [ "." digit+ ] ;
integer         = digit+ ;
note            = "> " { any_char - newline } ;
blank           = newline ;
```

## Appendix B: Reserved Words

### Endurance Actions

`run`, `bike`, `swim`, `row`, `ski`, `walk`, `hike`, `skate-ski`, `classic-ski`, `alpine-ski`, `snowboard`, `snowshoe`, `skate`, `paddle`, `kayak`, `surf`, `climb`, `elliptical`, `stairs`, `jumprope`, `ebike`, `other`, `warmup`, `cooldown`, `recover`

### Intensity Names

`easy`, `moderate`, `hard`, `max`, `threshold`, `tempo`

### Container Keywords

`superset`, `circuit`, `emom`, `alternating`, `amrap`, `for-time`, `every`, `for`

### Parameter Prefixes

`@RPE`, `@RIR`, `@Z`, `@pace:`, `rest:`

### Units

- **Duration:** `s`, `sec`, `min`, `h`, `hr`, `hour`
- **Distance:** `m`, `km`, `mi`, `mile`, `miles`, `yd`, `ft`
- **Weight:** `kg`, `lb`, `lbs`
- **Power:** `W`
- **Heart Rate:** `bpm`
- **Pace:** `/km`, `/mi`, `/mile`
