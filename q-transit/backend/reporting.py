import os
import csv
import io
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from schemas import (
    AssignmentItem,
    QAOACandidate,
    ScheduleValidationResult,
    ComparisonMetrics,
    SimulationConfig,
    DataValidationResult,
)


def generate_schedule_csv(items: List[AssignmentItem]) -> str:
    output = io.StringIO()
    fieldnames = [
        "trip_id",
        "route_id",
        "bus_id",
        "start_min",
        "end_min",
        "passenger_demand",
        "capacity",
        "operating_cost",
        "assignment_source",
        "validation_status",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for item in items:
        writer.writerow({
            "trip_id": item.trip_id,
            "route_id": item.route_id,
            "bus_id": item.bus_id if item.bus_id is not None else "UNASSIGNED",
            "start_min": item.start_min,
            "end_min": item.end_min,
            "passenger_demand": item.passenger_demand,
            "capacity": item.capacity if item.capacity is not None else "N/A",
            "operating_cost": item.operating_cost,
            "assignment_source": item.assignment_source,
            "validation_status": item.validation_status,
        })
    return output.getvalue()


def generate_candidates_csv(candidates: List[QAOACandidate]) -> str:
    output = io.StringIO()
    fieldnames = [
        "candidate_id",
        "bitstring",
        "count",
        "probability",
        "qubo_energy",
        "trips_served_count",
        "passenger_demand_served",
        "operating_cost",
        "service_value",
        "total_utility",
        "is_feasible",
        "violations_count",
        "validation_summary",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for c in candidates:
        writer.writerow({
            "candidate_id": c.candidate_id,
            "bitstring": c.bitstring,
            "count": c.count,
            "probability": c.probability,
            "qubo_energy": c.qubo_energy,
            "trips_served_count": c.trips_served_count,
            "passenger_demand_served": c.passenger_demand_served,
            "operating_cost": c.operating_cost,
            "service_value": c.service_value,
            "total_utility": c.total_utility,
            "is_feasible": "Yes" if c.is_feasible else "No",
            "violations_count": c.violations_count,
            "validation_summary": c.validation_summary,
        })
    return output.getvalue()


def generate_validation_csv(val_res: ScheduleValidationResult) -> str:
    output = io.StringIO()
    fieldnames = [
        "constraint_name",
        "violation_count",
        "affected_identifiers",
        "explanation",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    if not val_res.violations:
        writer.writerow({
            "constraint_name": "ALL_CONSTRAINTS",
            "violation_count": 0,
            "affected_identifiers": "None",
            "explanation": "Schedule passed all capacity, availability, duplication, and overlap checks.",
        })
    else:
        for v in val_res.violations:
            writer.writerow({
                "constraint_name": v.constraint_name,
                "violation_count": v.violation_count,
                "affected_identifiers": ", ".join(v.affected_ids),
                "explanation": v.explanation,
            })
    return output.getvalue()


def generate_comparison_csv(
    baseline_metrics: Optional[ComparisonMetrics],
    qaoa_metrics: Optional[ComparisonMetrics],
) -> str:
    output = io.StringIO()
    fieldnames = ["metric", "greedy_baseline", "best_feasible_qaoa"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    metric_names = [
        ("Trips served", "trips_served"),
        ("Passenger demand served", "passenger_demand_served"),
        ("Weighted service value", "weighted_service_value"),
        ("Operating cost", "operating_cost"),
        ("Trip utility", "trip_utility"),
        ("Coverage rate (eligible trips)", "coverage_rate"),
        ("Passenger demand coverage", "passenger_demand_coverage"),
        ("Fleet utilization", "fleet_utilization"),
        ("Constraint violations", "constraint_violations"),
        ("Runtime (seconds)", "runtime_seconds"),
        ("Feasible", "feasible"),
    ]

    for label, attr in metric_names:
        base_val = getattr(baseline_metrics, attr, "N/A") if baseline_metrics else "N/A"
        qaoa_val = getattr(qaoa_metrics, attr, "No feasible candidate") if qaoa_metrics else "No feasible candidate"
        writer.writerow({
            "metric": label,
            "greedy_baseline": base_val,
            "best_feasible_qaoa": qaoa_val,
        })

    return output.getvalue()


def generate_run_metadata(
    run_id: str,
    status: str,
    config: SimulationConfig,
    data_val: Optional[DataValidationResult],
    baseline_runtime: float,
    qaoa_runtime: float,
    warnings: List[str],
) -> Dict[str, Any]:
    return {
        "run_id": run_id,
        "status": status,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "solver_settings": {
            "cost_weight": config.cost_weight,
            "qaoa_p": config.qaoa_p,
            "shots": config.shots,
            "max_iter": config.max_iter,
            "seed": config.seed,
            "p_duplicate": config.p_duplicate,
            "p_overlap": config.p_overlap,
            "variable_cap": config.variable_cap,
            "wall_time_limit_sec": config.wall_time_limit_sec,
        },
        "normalization": {
            "max_service_value": data_val.max_service_value if data_val else 0.0,
            "max_operating_cost": data_val.max_operating_cost if data_val else 0.0,
        },
        "execution_runtimes_sec": {
            "baseline_runtime": baseline_runtime,
            "qaoa_runtime": qaoa_runtime,
        },
        "warnings": warnings,
        "disclaimer": (
            "Simulated quantum computation prototype for decision support. "
            "Simulator runtime does not establish physical quantum advantage."
        ),
    }


def save_run_reports(
    run_dir: str,
    run_id: str,
    final_schedule: List[AssignmentItem],
    baseline_schedule: List[AssignmentItem],
    qaoa_candidates: List[QAOACandidate],
    validation_res: ScheduleValidationResult,
    baseline_metrics: Optional[ComparisonMetrics],
    qaoa_metrics: Optional[ComparisonMetrics],
    metadata: Dict[str, Any],
):
    os.makedirs(run_dir, exist_ok=True)

    with open(os.path.join(run_dir, "final_schedule.csv"), "w", newline="", encoding="utf-8") as f:
        f.write(generate_schedule_csv(final_schedule))

    with open(os.path.join(run_dir, "baseline_schedule.csv"), "w", newline="", encoding="utf-8") as f:
        f.write(generate_schedule_csv(baseline_schedule))

    with open(os.path.join(run_dir, "qaoa_candidates.csv"), "w", newline="", encoding="utf-8") as f:
        f.write(generate_candidates_csv(qaoa_candidates))

    with open(os.path.join(run_dir, "validation_report.csv"), "w", newline="", encoding="utf-8") as f:
        f.write(generate_validation_csv(validation_res))

    with open(os.path.join(run_dir, "comparison_metrics.csv"), "w", newline="", encoding="utf-8") as f:
        f.write(generate_comparison_csv(baseline_metrics, qaoa_metrics))

    with open(os.path.join(run_dir, "run_metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

