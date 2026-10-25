"""CSP core package: models, variables, domains, constraints, soft constraints, cost function, and validator."""

from src.csp.constraints import (
    ALL_HARD_CONSTRAINTS,
    ClassNonOverlapConstraint,
    Constraint,
    LabContiguityConstraint,
    LunchBreakConstraint,
    RoomCapacityConstraint,
    RoomNonOverlapConstraint,
    RoomTypeConstraint,
    TeacherAvailabilityConstraint,
    TeacherNonOverlapConstraint,
    TeacherWorkloadConstraint,
    Violation,
    WeeklyHoursConstraint,
    is_assignment_consistent,
)
from src.csp.cost_function import WEIGHT_HARD, total_cost
from src.csp.domains import DomainWipeoutAtBuildError, SlotValue, build_domains
from src.csp.models import (
    Class,
    Dataset,
    RequiredSession,
    RequirementInput,
    Room,
    ScheduledSession,
    SlotRef,
    Subject,
    Teacher,
    Timetable,
    TimetableStatus,
)
from src.csp.soft_constraints import DEFAULT_SOFT_WEIGHTS, evaluate_soft_penalties
from src.csp.validator import ValidationReport, validate
from src.csp.variables import SessionVariable, build_variables

__all__ = [
    # Models
    "SlotRef",
    "Class",
    "Teacher",
    "Room",
    "Subject",
    "RequirementInput",
    "RequiredSession",
    "ScheduledSession",
    "Timetable",
    "TimetableStatus",
    "Dataset",
    # Variables
    "SessionVariable",
    "build_variables",
    # Domains
    "SlotValue",
    "DomainWipeoutAtBuildError",
    "build_domains",
    # Constraints
    "Violation",
    "Constraint",
    "ALL_HARD_CONSTRAINTS",
    "TeacherNonOverlapConstraint",
    "ClassNonOverlapConstraint",
    "RoomNonOverlapConstraint",
    "RoomCapacityConstraint",
    "RoomTypeConstraint",
    "TeacherAvailabilityConstraint",
    "WeeklyHoursConstraint",
    "TeacherWorkloadConstraint",
    "LunchBreakConstraint",
    "LabContiguityConstraint",
    "is_assignment_consistent",
    # Soft constraints
    "DEFAULT_SOFT_WEIGHTS",
    "evaluate_soft_penalties",
    # Cost function
    "WEIGHT_HARD",
    "total_cost",
    # Validator
    "ValidationReport",
    "validate",
]
