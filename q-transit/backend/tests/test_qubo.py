import pytest
import numpy as np
from csv_loader import load_and_validate_csvs
from preprocessing import preprocess_data
from qubo_builder import QUBOModel


def test_qubo_model_construction():
    trips_csv = """trip_id,route_id,start_min,duration_min,passenger_demand,priority,operating_cost
T001,R1,480,30,42,1.0,500
T002,R2,480,40,35,1.2,600
"""
    buses_csv = """bus_id,capacity,available_from_min,available_to_min
B001,50,420,720
B002,45,420,720
"""
    val = load_and_validate_csvs(trips_csv, buses_csv)
    val = preprocess_data(val, cost_weight=0.20)

    qubo = QUBOModel(val.trips, val.buses, p_duplicate=2.0, p_overlap=3.0)

    # T001 can fit both B001 and B002.
    # T002 can fit B001 and B002.
    # Total variables = 4
    assert qubo.n_vars == 4

    # All-zeros bitstring has energy 0
    e_zero = qubo.evaluate_energy("0000")
    assert e_zero == 0.0

    # Activating T001 on B001
    idx_T001_B001 = qubo.var_to_idx[("T001", "B001")]
    bstring_single = ["0"] * qubo.n_vars
    bstring_single[idx_T001_B001] = "1"
    e_single = qubo.evaluate_energy("".join(bstring_single))
    t1 = next(t for t in val.trips if t.trip_id == "T001")
    assert abs(e_single - (-t1.utility)) < 1e-6

    # Activating T001 on both B001 and B002 triggers duplicate penalty P_duplicate
    idx_T001_B002 = qubo.var_to_idx[("T001", "B002")]
    bstring_dup = ["0"] * qubo.n_vars
    bstring_dup[idx_T001_B001] = "1"
    bstring_dup[idx_T001_B002] = "1"
    e_dup = qubo.evaluate_energy("".join(bstring_dup))
    expected_e = -2.0 * t1.utility + 2.0  # linear rewards + P_duplicate
    assert abs(e_dup - expected_e) < 1e-6
