# Database Storage for OWF Workouts

## The challenge

The OWF AST is a **recursive tree** with 22 concrete node types:
- 2 containers: `Document`, `Workout`
- 5 step types: `EnduranceStep`, `StrengthStep`, `RestStep`, `RepeatStep`, `IncludeStep`
- 7 block types: `Superset`, `Circuit`, `EMOM`, `AlternatingEMOM`, `CustomInterval`, `AMRAP`, `ForTime`
- 6 param types: `PaceParam`, `PowerParam`, `HeartRateParam`, `WeightParam`, `RPEParam`, `IntensityParam`
- 4 expression types: `Literal`, `VarRef`, `Percentage`, `BinOp` (recursive)

Steps/blocks nest arbitrarily (repeat inside AMRAP inside for-time, etc.). Expressions also form sub-trees (`80% of FTP + 20W`). Order matters everywhere — steps, params, and notes are ordered tuples.

## Three approaches

### Option A: Store raw `.owf` text (simplest)

```
documents
  id          PK
  title       text
  raw_text    text       -- the .owf source
  created_at  timestamp
  updated_at  timestamp
  tags        text[]     -- for search/filtering
```

**How it works:** Store the `.owf` text verbatim. On read, call `owf.parse()` to get the AST. On write, call `owf.dumps()` to serialize back.

**Pros:**
- Zero impedance mismatch — the `.owf` format is the source of truth
- Trivial to implement (one table, one column)
- Round-trips perfectly (store original text, not serialized AST)
- Supports any future syntax additions without schema migration

**Cons:**
- Cannot query workout contents via SQL (e.g. "find all workouts with deadlifts")
- Every read requires parsing; adds ~0.1ms per document (negligible)
- Searching requires parsing all documents or maintaining a separate search index

**Best for:** Personal workout library, small dataset, when querying workout internals isn't needed.

---

### Option B: Hybrid — relational top-level, JSON subtrees (recommended)

```
documents
  id            PK
  raw_text      text           -- original .owf source (optional backup)
  variables     jsonb          -- {"FTP": "250W", "bodyweight": "80kg"}
  created_at    timestamp

workouts
  id            PK
  document_id   FK → documents
  position      int            -- ordering within document
  name          text
  workout_type  text | null    -- "run", "strength", "wod", etc.
  notes         text[]         -- workout-level notes

steps
  id            PK
  workout_id    FK → workouts
  parent_id     FK → steps | null  -- null = top-level step in workout
  position      int                -- ordering among siblings
  node_type     text               -- discriminator: "endurance", "strength",
                                   -- "rest", "repeat", "include", "emom",
                                   -- "amrap", "for_time", "superset", etc.
  data          jsonb              -- type-specific fields (see below)
```

The `data` JSONB column holds everything type-specific:

```jsonb
-- EnduranceStep
{"action": "run", "duration_s": 600, "distance": {"value": 5, "unit": "km"},
 "params": [{"type": "pace", "minutes": 5, "seconds": 0, "unit": "km"}],
 "notes": ["Felt good"]}

-- StrengthStep
{"exercise": "bench press", "sets": 3, "reps": 8,
 "params": [{"type": "weight", "value": {"literal": 80, "unit": "kg"}}],
 "rest_s": 90, "notes": []}

-- RepeatStep / blocks
{"count": 5}  -- children are in the `steps` table via parent_id

-- ForTime
{"time_cap_s": 1200}  -- children via parent_id

-- EMOM
{"duration_s": 600}   -- children via parent_id
```

**Pros:**
- Can query by workout name, type, exercise name, action
- `steps.node_type` enables filtering (e.g. all for-time WoDs)
- JSONB enables GIN-indexed search into params/exercises
- Parent-child via `parent_id` handles arbitrary nesting naturally
- `position` column preserves ordering
- Keeping `raw_text` on document allows perfect round-trip recovery

**Cons:**
- More complex to implement — need serialization/deserialization layer between AST and DB
- Schema migrations needed if top-level structure changes
- JSONB `data` column is semi-structured — need discipline to keep it consistent

**Best for:** Multi-user app, workout search/filtering, analytics (e.g. "total volume this week").

---

### Option C: Fully normalized relational (most complex)

```
documents          (id, created_at)
document_variables (document_id, key, value)
workouts           (id, document_id, position, name, workout_type)
workout_notes      (workout_id, position, text)
steps              (id, workout_id, parent_id, position, node_type)

-- Type-specific tables (one per node type):
endurance_steps    (step_id FK, action, duration_s, distance_value, distance_unit)
strength_steps     (step_id FK, exercise, sets, reps, reps_is_max, duration_s, rest_s)
rest_steps         (step_id FK, duration_s)
repeat_steps       (step_id FK, count)
include_steps      (step_id FK, workout_name, resolved_workout_id FK)
emom_blocks        (step_id FK, duration_s)
amrap_blocks       (step_id FK, duration_s)
for_time_blocks    (step_id FK, time_cap_s)
superset_blocks    (step_id FK, count)
-- ... etc for all 12 step/block types

-- Params (polymorphic):
step_params        (id, step_id FK, position, param_type)
pace_params        (param_id FK, minutes, seconds, unit)
power_params       (param_id FK, expression_id FK)
weight_params      (param_id FK, expression_id FK)
hr_params          (param_id FK, expression_id FK, zone_name)
rpe_params         (param_id FK, value)
intensity_params   (param_id FK, name)

-- Expressions (recursive):
expressions        (id, expr_type, literal_value, literal_unit,
                    var_name, percent, op,
                    left_id FK → expressions, right_id FK → expressions,
                    of_id FK → expressions)
```

**Pros:**
- Full SQL querying power — any field is a column
- Referential integrity everywhere
- Can do complex analytics (e.g. "average rest duration across all strength workouts")
- Clean normalized schema, no JSON ambiguity

**Cons:**
- ~15-20 tables for the full model
- Reconstructing a single workout requires many JOINs (4-6 levels deep)
- High development cost — each new node type needs a new table + migration
- Expression tree as self-referencing rows is awkward to query and reconstruct
- Premature for current project size

**Best for:** Large-scale platform, complex analytics, when every field must be independently queryable.

---

## Recommendation

**Option B (hybrid)** balances queryability with implementation simplicity. The key insight is that the OWF tree has a natural split point:

- **Documents and workouts** are what users browse and search → relational
- **Steps, params, expressions** are what users view as a unit → JSONB or parent-child rows

This lets you write queries like:
```sql
-- Find all WoD workouts with deadlifts
SELECT w.name FROM workouts w
JOIN steps s ON s.workout_id = w.id
WHERE w.workout_type = 'wod'
AND s.data->>'exercise' = 'deadlift';
```

While keeping the recursive nesting manageable via `parent_id` rather than deep joins.

If querying is not a priority yet, **Option A** is the pragmatic starting point — you can always migrate to B later since you have `raw_text` to re-parse.
