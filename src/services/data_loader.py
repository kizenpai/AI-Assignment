"""Dataset loader service.

Parses input JSON files/strings/dicts into the Dataset dataclass tree.
Expands weekly requirement specifications into individual RequiredSession instances
per DD-008. Integrates with data_validator to verify structural and referential integrity.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

from src.csp.models import (
    Class,
    Dataset,
    RequiredSession,
    RequirementInput,
    Room,
    Subject,
    Teacher,
)
from src.services.data_validator import (
    DatasetValidationException,
    DatasetValidationReport,
    validate_dataset_dict,
)


class DatasetParseError(Exception):
    """Raised when the dataset file cannot be read or parsed as JSON."""

    pass


def expand_requirements(requirements: List[RequirementInput]) -> List[RequiredSession]:
    """Expand weekly requirements into atomic RequiredSession objects per DD-008.

    A requirement with weekly_periods=4, duration_periods=1 expands into 4 RequiredSessions:
    REQ-{class_id}-{subject_id}-01 .. REQ-{class_id}-{subject_id}-04.

    A requirement with weekly_periods=2, duration_periods=2 (e.g. lab) expands into
    1 RequiredSession of duration 2:
    REQ-{class_id}-{subject_id}-01.
    """
    sessions: List[RequiredSession] = []

    for req in requirements:
        duration = max(1, req.duration_periods)
        num_sessions = max(1, req.weekly_periods // duration)

        for occ_idx in range(1, num_sessions + 1):
            req_id = f"REQ-{req.class_id}-{req.subject_id}-{occ_idx:02d}"
            sessions.append(
                RequiredSession(
                    requirement_id=req_id,
                    class_id=req.class_id,
                    subject_id=req.subject_id,
                    teacher_id=req.teacher_id,
                    duration_periods=duration,
                    consecutive_required=req.consecutive_required,
                    occurrence_index=occ_idx,
                    occurrence_total=num_sessions,
                )
            )

    return sessions


def load_dataset_from_dict(
    raw: Dict[str, Any],
    validate: bool = True,
    strict: bool = False,
) -> Tuple[Dataset, DatasetValidationReport]:
    """Build a Dataset dataclass instance from a dictionary.

    Args:
        raw: Raw dictionary from parsed JSON.
        validate: Whether to run dataset validation.
        strict: If True and validation finds blocking errors, raise DatasetValidationException.

    Returns:
        Tuple of (Dataset, DatasetValidationReport).
    """
    report = validate_dataset_dict(raw) if validate else DatasetValidationReport(is_valid=True)

    if strict and not report.is_valid:
        report.raise_if_invalid()

    # Parse entities
    classes = [Class.from_dict(c) for c in raw.get("classes", []) if isinstance(c, dict)]
    teachers = [Teacher.from_dict(t) for t in raw.get("teachers", []) if isinstance(t, dict)]
    subjects = [Subject.from_dict(s) for s in raw.get("subjects", []) if isinstance(s, dict)]
    rooms = [Room.from_dict(r) for r in raw.get("rooms", []) if isinstance(r, dict)]
    requirements = [
        RequirementInput.from_dict(req)
        for req in raw.get("requirements", [])
        if isinstance(req, dict)
    ]

    # Expand requirements into atomic RequiredSessions per DD-008
    required_sessions = expand_requirements(requirements)

    dataset = Dataset(
        dataset_id=str(raw.get("dataset_id", "unnamed")).strip(),
        description=str(raw.get("description", "")).strip(),
        days=int(raw.get("days", 5)),
        periods_per_day=int(raw.get("periods_per_day", 6)),
        lunch_period=(
            int(raw["lunch_period"])
            if raw.get("lunch_period") is not None
            else None
        ),
        classes=classes,
        teachers=teachers,
        subjects=subjects,
        rooms=rooms,
        requirements=requirements,
        required_sessions=required_sessions,
    )

    return dataset, report


def load_dataset_from_json(
    json_str: str,
    validate: bool = True,
    strict: bool = False,
) -> Tuple[Dataset, DatasetValidationReport]:
    """Parse JSON string into a Dataset."""
    try:
        raw = json.loads(json_str)
    except Exception as e:
        raise DatasetParseError(f"Failed to parse JSON string: {e}") from e

    return load_dataset_from_dict(raw, validate=validate, strict=strict)


def load_dataset_from_file(
    file_path: Union[str, Path],
    validate: bool = True,
    strict: bool = False,
) -> Tuple[Dataset, DatasetValidationReport]:
    """Read a JSON file from disk into a Dataset."""
    p = Path(file_path)
    if not p.is_file():
        raise DatasetParseError(f"Dataset file does not exist: {p}")

    try:
        content = p.read_text(encoding="utf-8")
        raw = json.loads(content)
    except json.JSONDecodeError as e:
        raise DatasetParseError(f"Invalid JSON in file '{p.name}': {e}") from e
    except Exception as e:
        raise DatasetParseError(f"Error reading file '{p.name}': {e}") from e

    return load_dataset_from_dict(raw, validate=validate, strict=strict)
