import csv
import io
import pytest
from schemas import AssignmentItem, ScheduleValidationResult
from reporting import generate_schedule_csv, generate_validation_csv


def test_schedule_csv_generation():
    items = [
        AssignmentItem(
            trip_id="T001",
            route_id="R1",
            bus_id="B001",
            start_min=480,
            end_min=510,
            passenger_demand=42,
            capacity=50,
            operating_cost=500.0,
            assignment_source="FINAL",
            validation_status="FEASIBLE",
        )
    ]
    csv_text = generate_schedule_csv(items)
    reader = csv.DictReader(io.StringIO(csv_text))
    rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["trip_id"] == "T001"
    assert rows[0]["bus_id"] == "B001"
    assert rows[0]["validation_status"] == "FEASIBLE"


def test_validation_csv_generation():
    val_res = ScheduleValidationResult(
        is_feasible=True,
        total_violations=0,
        violations=[],
        summary_message="All passed.",
    )
    csv_text = generate_validation_csv(val_res)
    reader = csv.DictReader(io.StringIO(csv_text))
    rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["constraint_name"] == "ALL_CONSTRAINTS"
    assert rows[0]["violation_count"] == "0"

