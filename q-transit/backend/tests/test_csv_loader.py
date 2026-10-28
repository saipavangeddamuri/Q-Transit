import pytest
from csv_loader import load_and_validate_csvs


SAMPLE_TRIPS = """trip_id,route_id,start_min,duration_min,passenger_demand,priority,operating_cost
T001,R1,480,30,42,1.0,500
T002,R2,480,40,35,1.2,600
"""

SAMPLE_BUSES = """bus_id,capacity,available_from_min,available_to_min
B001,50,420,720
B002,40,420,720
"""


def test_valid_csvs():
    result = load_and_validate_csvs(SAMPLE_TRIPS, SAMPLE_BUSES)
    assert result.is_valid is True
    assert result.trips_received == 2
    assert result.buses_received == 2
    assert len(result.issues) == 0


def test_missing_required_column():
    bad_trips = """trip_id,route_id,start_min,passenger_demand,priority,operating_cost
T001,R1,480,42,1.0,500
"""
    result = load_and_validate_csvs(bad_trips, SAMPLE_BUSES)
    assert result.is_valid is False
    assert any("duration_min" in issue.reason for issue in result.issues)


def test_duplicate_trip_id():
    dup_trips = """trip_id,route_id,start_min,duration_min,passenger_demand,priority,operating_cost
T001,R1,480,30,42,1.0,500
T001,R2,540,30,35,1.2,600
"""
    result = load_and_validate_csvs(dup_trips, SAMPLE_BUSES)
    assert result.is_valid is False
    assert any("Duplicate trip_id 'T001'" in issue.reason for issue in result.issues)


def test_negative_demand():
    bad_demand = """trip_id,route_id,start_min,duration_min,passenger_demand,priority,operating_cost
T001,R1,480,30,-10,1.0,500
"""
    result = load_and_validate_csvs(bad_demand, SAMPLE_BUSES)
    assert result.is_valid is False
    assert any("passenger_demand must be >= 0" in issue.reason for issue in result.issues)


def test_zero_duration():
    bad_dur = """trip_id,route_id,start_min,duration_min,passenger_demand,priority,operating_cost
T001,R1,480,0,42,1.0,500
"""
    result = load_and_validate_csvs(bad_dur, SAMPLE_BUSES)
    assert result.is_valid is False
    assert any("duration_min must be > 0" in issue.reason for issue in result.issues)


def test_overnight_trip():
    overnight = """trip_id,route_id,start_min,duration_min,passenger_demand,priority,operating_cost
T001,R1,1420,30,42,1.0,500
"""
    result = load_and_validate_csvs(overnight, SAMPLE_BUSES)
    assert result.is_valid is False
    assert any("> 1440" in issue.reason for issue in result.issues)


def test_empty_csv():
    result = load_and_validate_csvs("", SAMPLE_BUSES)
    assert result.is_valid is False
    assert any("empty" in issue.reason for issue in result.issues)

