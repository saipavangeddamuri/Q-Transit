import pytest
from schemas import TripRecord, BusRecord, AssignmentItem
from validator import IndependentValidator


@pytest.fixture
def test_setup():
    trips = [
        TripRecord(
            trip_id="T001",
            route_id="R1",
            start_min=480,
            duration_min=30,
            passenger_demand=45,
            priority=1.0,
            operating_cost=500.0,
            end_min=510,
        ),
        TripRecord(
            trip_id="T002",
            route_id="R2",
            start_min=500,
            duration_min=30,
            passenger_demand=35,
            priority=1.0,
            operating_cost=500.0,
            end_min=530,
        ),
    ]
    buses = [
        BusRecord(
            bus_id="B001",
            capacity=50,
            available_from_min=420,
            available_to_min=720,
        ),
        BusRecord(
            bus_id="B002",
            capacity=40,
            available_from_min=420,
            available_to_min=720,
        ),
    ]
    validator = IndependentValidator(trips, buses)
    return validator, trips, buses


def test_validator_valid_schedule(test_setup):
    validator, trips, buses = test_setup
    schedule = [
        AssignmentItem(
            trip_id="T001",
            route_id="R1",
            bus_id="B001",
            start_min=480,
            end_min=510,
            passenger_demand=45,
            capacity=50,
            operating_cost=500.0,
            assignment_source="BASELINE",
            validation_status="FEASIBLE",
        ),
        AssignmentItem(
            trip_id="T002",
            route_id="R2",
            bus_id="B002",
            start_min=500,
            end_min=530,
            passenger_demand=35,
            capacity=40,
            operating_cost=500.0,
            assignment_source="BASELINE",
            validation_status="FEASIBLE",
        ),
    ]
    result = validator.validate_schedule(schedule)
    assert result.is_feasible is True
    assert result.total_violations == 0


def test_validator_capacity_violation(test_setup):
    validator, trips, buses = test_setup
    # T001 demand is 45. B002 capacity is 40.
    schedule = [
        AssignmentItem(
            trip_id="T001",
            route_id="R1",
            bus_id="B002",
            start_min=480,
            end_min=510,
            passenger_demand=45,
            capacity=40,
            operating_cost=500.0,
            assignment_source="RAW_QAOA",
            validation_status="FEASIBLE",
        ),
    ]
    result = validator.validate_schedule(schedule)
    assert result.is_feasible is False
    assert any(v.constraint_name == "BUS_CAPACITY" for v in result.violations)


def test_validator_overlap_violation(test_setup):
    validator, trips, buses = test_setup
    # T001 is [480, 510) and T002 is [500, 530). Both assigned to B001!
    schedule = [
        AssignmentItem(
            trip_id="T001",
            route_id="R1",
            bus_id="B001",
            start_min=480,
            end_min=510,
            passenger_demand=45,
            capacity=50,
            operating_cost=500.0,
            assignment_source="RAW_QAOA",
            validation_status="FEASIBLE",
        ),
        AssignmentItem(
            trip_id="T002",
            route_id="R2",
            bus_id="B001",
            start_min=500,
            end_min=530,
            passenger_demand=35,
            capacity=50,
            operating_cost=500.0,
            assignment_source="RAW_QAOA",
            validation_status="FEASIBLE",
        ),
    ]
    result = validator.validate_schedule(schedule)
    assert result.is_feasible is False
    assert any(v.constraint_name == "NO_BUS_OVERLAP" for v in result.violations)


def test_validator_duplicate_assignment(test_setup):
    validator, trips, buses = test_setup
    # T001 assigned to both B001 and B002
    schedule = [
        AssignmentItem(
            trip_id="T001",
            route_id="R1",
            bus_id="B001",
            start_min=480,
            end_min=510,
            passenger_demand=45,
            capacity=50,
            operating_cost=500.0,
            assignment_source="RAW_QAOA",
            validation_status="FEASIBLE",
        ),
        AssignmentItem(
            trip_id="T001",
            route_id="R1",
            bus_id="B002",
            start_min=480,
            end_min=510,
            passenger_demand=45,
            capacity=40,
            operating_cost=500.0,
            assignment_source="RAW_QAOA",
            validation_status="FEASIBLE",
        ),
    ]
    result = validator.validate_schedule(schedule)
    assert result.is_feasible is False
    assert any(v.constraint_name == "NO_DUPLICATE_ASSIGNMENT" for v in result.violations)

