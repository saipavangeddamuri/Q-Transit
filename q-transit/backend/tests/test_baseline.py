import pytest
from csv_loader import load_and_validate_csvs
from preprocessing import preprocess_data
from baseline import run_greedy_baseline


def test_greedy_baseline_execution():
    trips_csv = """trip_id,route_id,start_min,duration_min,passenger_demand,priority,operating_cost
T001,R1,480,30,42,1.0,500
T002,R2,480,40,35,1.2,600
T003,R3,495,25,22,0.8,350
"""
    buses_csv = """bus_id,capacity,available_from_min,available_to_min
B001,50,420,720
B002,40,420,720
"""
    val = load_and_validate_csvs(trips_csv, buses_csv)
    val = preprocess_data(val, cost_weight=0.20)

    items, runtime = run_greedy_baseline(val.trips, val.buses)
    assert len(items) == 3
    assert runtime >= 0.0

    # Ensure assigned items have a valid bus
    assigned = [i for i in items if i.bus_id is not None]
    assert len(assigned) > 0

    # Ensure no two assigned items on same bus overlap
    bus_assignments = {}
    for a in assigned:
        bus_assignments.setdefault(a.bus_id, []).append(a)

    for bus_id, b_items in bus_assignments.items():
        for i in range(len(b_items)):
            for j in range(i + 1, len(b_items)):
                t1, t2 = b_items[i], b_items[j]
                overlaps = (t1.start_min < t2.end_min) and (t2.start_min < t1.end_min)
                assert not overlaps, f"Overlap detected on bus {bus_id} between {t1.trip_id} and {t2.trip_id}"

