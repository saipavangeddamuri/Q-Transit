import os
import pytest
from csv_loader import load_and_validate_csvs
from preprocessing import preprocess_data
from baseline import run_greedy_baseline
from qubo_builder import QUBOModel
from qaoa_solver import run_qaoa_simulation
from validator import IndependentValidator
from comparison import compute_metrics
from schemas import SimulationConfig


def test_full_sample_pipeline():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    trips_path = os.path.join(base_dir, "sample_data", "trips.csv")
    buses_path = os.path.join(base_dir, "sample_data", "buses.csv")

    with open(trips_path, "r", encoding="utf-8") as f:
        trips_csv = f.read()
    with open(buses_path, "r", encoding="utf-8") as f:
        buses_csv = f.read()

    # 1. Validation & Preprocessing
    data = load_and_validate_csvs(trips_csv, buses_csv)
    assert data.is_valid is True
    assert len(data.trips) == 6
    assert len(data.buses) == 3

    data = preprocess_data(data, cost_weight=0.20)
    # The technical document mentions 14 eligible assignment variables for the 6-trip 3-bus sample dataset
    assert data.eligible_assignments_count == 14

    validator = IndependentValidator(data.trips, data.buses)

    # 2. Greedy Baseline
    baseline_items, baseline_runtime = run_greedy_baseline(data.trips, data.buses)
    baseline_val = validator.validate_schedule(baseline_items)
    assert baseline_val.is_feasible is True
    assert baseline_val.total_violations == 0

    baseline_metrics = compute_metrics(
        baseline_items, data.trips, data.buses, baseline_val, baseline_runtime
    )
    assert baseline_metrics.feasible == "Yes"
    assert baseline_metrics.trips_served > 0

    # 3. QUBO Model
    qubo = QUBOModel(data.trips, data.buses, p_duplicate=2.0, p_overlap=2.0)
    assert qubo.n_vars == 14

    # 4. QAOA Simulation
    config = SimulationConfig(
        cost_weight=0.20,
        qaoa_p=1,
        shots=128,  # small shot count for fast test
        max_iter=5,  # small iteration for fast test
        seed=42,
        variable_cap=16,
    )
    candidates, best_qaoa, qaoa_runtime, skip_reason = run_qaoa_simulation(
        qubo, data.trips, data.buses, validator, config
    )
    assert skip_reason is None
    assert len(candidates) > 0

    # Ensure all candidates are validated
    for c in candidates:
        assert isinstance(c.is_feasible, bool)
        assert c.violations_count >= 0

