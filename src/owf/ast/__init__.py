"""AST node types for the OpenWorkoutFormat."""

from owf.ast.base import (
    DeloadRule,
    Document,
    Program,
    ProgressionRule,
    Week,
    Workout,
    WorkoutDate,
)
from owf.ast.blocks import (
    AMRAP,
    ForTime,
    Interval,
)
from owf.ast.params import (
    BodyweightPlusParam,
    HeartRateParam,
    PaceParam,
    Param,
    PercentOfParam,
    PowerParam,
    RIRParam,
    RPEParam,
    SetTypeParam,
    TempoParam,
    TypedPercentParam,
    WeightParam,
    ZoneParam,
)
from owf.ast.steps import (
    RepeatBlock,
    Step,
)

# Full union including block types (steps.py can't import blocks.py due to
# circular import constraints, so we define the complete union here).
StepUnion = Step | RepeatBlock | Interval | AMRAP | ForTime

__all__ = [
    "AMRAP",
    "BodyweightPlusParam",
    "DeloadRule",
    "Document",
    "ForTime",
    "HeartRateParam",
    "Interval",
    "PaceParam",
    "Param",
    "PercentOfParam",
    "PowerParam",
    "Program",
    "ProgressionRule",
    "RIRParam",
    "RPEParam",
    "RepeatBlock",
    "SetTypeParam",
    "Step",
    "StepUnion",
    "TempoParam",
    "TypedPercentParam",
    "Week",
    "WeightParam",
    "Workout",
    "WorkoutDate",
    "ZoneParam",
]
