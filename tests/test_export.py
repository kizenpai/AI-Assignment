"""Unit tests for timetable export service (CSV and Excel).

Tests TRD TC-EXP-1, TC-EXP-2, DD-031, and DD-037.
"""

import io
from pathlib import Path
import pandas as pd
import pytest

from src.algorithms.backtracking import solve_backtracking
from src.algorithms.base import AlgorithmConfig
from src.csp.models import Dataset, ScheduledSession, Timetable
from src.services.data_loader import load_dataset_from_file
from src.services.export import ExportError, _sanitize_cell, to_csv, to_excel


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture
def valid_timetable_and_dataset():
    path = DATA_DIR / "small_dataset.json"
    dataset, _ = load_dataset_from_file(path)
    config = AlgorithmConfig(algorithm="backtracking", max_search_nodes=50000)
    result = solve_backtracking(dataset, config)
    assert result.status == "Valid"
    return result.timetable, dataset


def test_tc_exp_1_export_valid_timetable_to_csv_and_xlsx(valid_timetable_and_dataset):
    """TRD TC-EXP-1: Export a valid timetable to CSV and XLSX.

    Row counts match len(scheduled_sessions); both formats contain identical session data.
    """
    timetable, dataset = valid_timetable_and_dataset
    total_sessions = len(timetable.scheduled_sessions)

    # 1. Test CSV export
    csv_str = to_csv(timetable, dataset)
    df_csv = pd.read_csv(io.StringIO(csv_str))
    assert len(df_csv) == total_sessions
    assert "Class Name" in df_csv.columns
    assert "Teacher Name" in df_csv.columns
    assert "Room ID" in df_csv.columns

    # 2. Test Excel export
    xlsx_bytes = to_excel(timetable, dataset)
    excel_file = io.BytesIO(xlsx_bytes)
    df_excel = pd.read_excel(excel_file, sheet_name="Master Timetable")
    assert len(df_excel) == total_sessions

    # Cross-check session IDs between CSV and Excel
    assert set(df_csv["Requirement ID"]) == set(df_excel["Requirement ID"])


def test_tc_exp_2_attempt_export_of_invalid_timetable_rejected(valid_timetable_and_dataset):
    """TRD TC-EXP-2: Attempt export of invalid timetable without override flag.

    Expected: Export rejected with ExportError.
    """
    timetable, dataset = valid_timetable_and_dataset

    # Create an invalid timetable by changing status
    invalid_tt = Timetable(
        timetable_id="invalid_tt",
        dataset_id=dataset.dataset_id,
        scheduled_sessions=list(timetable.scheduled_sessions),
        status="Invalid",
    )

    with pytest.raises(ExportError):
        to_csv(invalid_tt, dataset, allow_invalid_export=False)

    with pytest.raises(ExportError):
        to_excel(invalid_tt, dataset, allow_invalid_export=False)

    # Allowed with override flag
    csv_override = to_csv(invalid_tt, dataset, allow_invalid_export=True)
    assert len(csv_override) > 0


def test_formula_injection_sanitization():
    """DD-037: Protect against spreadsheet formula injection."""
    assert _sanitize_cell("=1+1") == "'=1+1"
    assert _sanitize_cell("+SUM(A1:A10)") == "'+SUM(A1:A10)"
    assert _sanitize_cell("-20") == "'-20"
    assert _sanitize_cell("@mention") == "'@mention"
    assert _sanitize_cell("Normal Text") == "Normal Text"
