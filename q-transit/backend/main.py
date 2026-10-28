import os
import uuid
import threading
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse, FileResponse
from pydantic import BaseModel

from schemas import (
    SimulationConfig,
    DataValidationResult,
    SimulationRunResult,
    ComparisonMetrics,
    ScheduleValidationResult,
)
from csv_loader import load_and_validate_csvs
from preprocessing import preprocess_data
from baseline import run_greedy_baseline
from qubo_builder import QUBOModel
from qaoa_solver import run_qaoa_simulation
from validator import IndependentValidator
from comparison import compute_metrics
from reporting import save_run_reports
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="Q-TRANSIT API",
    description="Quantum-Enhanced Intelligent Bus Scheduling and Route Optimization Prototype API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_DIR = os.path.join(BASE_DIR, "sample_data")
RUNS_DIR = os.path.join(BASE_DIR, "runs")
os.makedirs(RUNS_DIR, exist_ok=True)

# In-memory storage for active runs
RUN_STORE: Dict[str, SimulationRunResult] = {}
SIMULATION_LOCK = threading.Lock()


class RunSimulationRequest(BaseModel):
    trips_csv: str
    buses_csv: str
    config: SimulationConfig = SimulationConfig()


class ValidateCsvRequest(BaseModel):
    trips_csv: str
    buses_csv: str
    cost_weight: float = 0.20


@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "service": "Q-TRANSIT Backend",
        "problem_id": "UC-053",
        "team": "HYPERQUBITS",
    }


@app.get("/api/sample-data")
def get_sample_data():
    trips_path = os.path.join(SAMPLE_DIR, "trips.csv")
    buses_path = os.path.join(SAMPLE_DIR, "buses.csv")

    trips_content = ""
    buses_content = ""

    if os.path.exists(trips_path):
        with open(trips_path, "r", encoding="utf-8") as f:
            trips_content = f.read()

    if os.path.exists(buses_path):
        with open(buses_path, "r", encoding="utf-8") as f:
            buses_content = f.read()

    return {
        "trips_csv": trips_content,
        "buses_csv": buses_content,
    }


@app.post("/api/validate-csv", response_model=DataValidationResult)
def validate_csv(payload: ValidateCsvRequest):
    val_res = load_and_validate_csvs(payload.trips_csv, payload.buses_csv)
    if val_res.is_valid:
        val_res = preprocess_data(val_res, cost_weight=payload.cost_weight)
    return val_res


def execute_pipeline(run_id: str, trips_csv: str, buses_csv: str, config: SimulationConfig):
    run_res = RUN_STORE[run_id]

    try:
        # Stage 1: Validating data
        run_res.status = "running"
        run_res.current_stage = "Validating data"

        val_res = load_and_validate_csvs(trips_csv, buses_csv)
        if not val_res.is_valid:
            run_res.status = "failed"
            run_res.current_stage = "Validation failed"
            run_res.error_message = "Input CSV data failed schema or domain validation."
            run_res.data_validation = val_res
            return

        # Stage 2: Preprocessing trips
        run_res.current_stage = "Preprocessing trips"
        val_res = preprocess_data(val_res, cost_weight=config.cost_weight)
        run_res.data_validation = val_res

        validator = IndependentValidator(val_res.trips, val_res.buses)

        # Stage 3: Building baseline
        run_res.current_stage = "Building baseline"
        baseline_items, baseline_runtime = run_greedy_baseline(val_res.trips, val_res.buses)
        baseline_val = validator.validate_schedule(baseline_items)
        baseline_metrics = compute_metrics(
            baseline_items, val_res.trips, val_res.buses, baseline_val, baseline_runtime
        )

        run_res.baseline_schedule = baseline_items
        run_res.baseline_validation = baseline_val
        run_res.baseline_metrics = baseline_metrics

        # Stage 4: Constructing QUBO
        run_res.current_stage = "Constructing QUBO"
        qubo_model = QUBOModel(
            trips=val_res.trips,
            buses=val_res.buses,
            p_duplicate=config.p_duplicate,
            p_overlap=config.p_overlap,
        )
        run_res.qubo_summary = qubo_model.to_summary()

        # Stage 5: Running QAOA
        run_res.current_stage = "Running QAOA"
        candidates, best_qaoa, qaoa_runtime, skip_reason = run_qaoa_simulation(
            qubo_model=qubo_model,
            trips=val_res.trips,
            buses=val_res.buses,
            validator=validator,
            config=config,
        )

        run_res.qaoa_candidates = candidates
        run_res.best_feasible_qaoa = best_qaoa
        run_res.qaoa_skipped_or_failed_reason = skip_reason

        # Stage 6: Validating candidates
        run_res.current_stage = "Validating candidates"
        best_qaoa_metrics = None
        if best_qaoa is not None:
            best_qaoa_val = validator.validate_schedule(best_qaoa.assignments)
            best_qaoa_metrics = compute_metrics(
                best_qaoa.assignments,
                val_res.trips,
                val_res.buses,
                best_qaoa_val,
                qaoa_runtime,
            )
            run_res.best_qaoa_metrics = best_qaoa_metrics

        # Stage 7: Comparing results
        run_res.current_stage = "Comparing results"
        # Determine final schedule: best feasible QAOA if present, else baseline
        if best_qaoa is not None:
            final_schedule = [
                itm.model_copy(update={"assignment_source": "FINAL"})
                for itm in best_qaoa.assignments
            ]
            final_val = validator.validate_schedule(final_schedule)
            final_metrics = best_qaoa_metrics
        else:
            final_schedule = [
                itm.model_copy(update={"assignment_source": "FINAL"})
                for itm in baseline_items
            ]
            final_val = baseline_val
            final_metrics = baseline_metrics

        run_res.final_schedule = final_schedule
        run_res.final_validation = final_val
        run_res.final_metrics = final_metrics

        # Stage 8: Preparing reports
        run_res.current_stage = "Preparing reports"
        run_dir = os.path.join(RUNS_DIR, run_id)
        warnings = [issue.reason for issue in val_res.issues if issue.level == "WARNING"]
        if skip_reason:
            warnings.append(skip_reason)

        from reporting import generate_run_metadata
        metadata = generate_run_metadata(
            run_id=run_id,
            status="succeeded" if not skip_reason else "partial",
            config=config,
            data_val=val_res,
            baseline_runtime=baseline_runtime,
            qaoa_runtime=qaoa_runtime,
            warnings=warnings,
        )

        save_run_reports(
            run_dir=run_dir,
            run_id=run_id,
            final_schedule=final_schedule,
            baseline_schedule=baseline_items,
            qaoa_candidates=candidates,
            validation_res=final_val,
            baseline_metrics=baseline_metrics,
            qaoa_metrics=best_qaoa_metrics,
            metadata=metadata,
        )

        if skip_reason:
            run_res.status = "partial"
            run_res.current_stage = "Partial (Baseline ready, QAOA limited)"
        else:
            run_res.status = "succeeded"
            run_res.current_stage = "Completed"

    except Exception as e:
        run_res.status = "failed"
        run_res.current_stage = "Pipeline error"
        run_res.error_message = str(e)


@app.post("/api/run-simulation")
def run_simulation(
    payload: RunSimulationRequest, background_tasks: BackgroundTasks
):
    if not SIMULATION_LOCK.acquire(blocking=False):
        raise HTTPException(
            status_code=429,
            detail="A simulation is already in progress. Please wait for it to complete.",
        )

    run_id = f"run_{uuid.uuid4().hex[:8]}"
    initial_res = SimulationRunResult(
        run_id=run_id,
        status="queued",
        current_stage="Queued",
        config=payload.config,
    )
    RUN_STORE[run_id] = initial_res

    def run_worker():
        try:
            execute_pipeline(run_id, payload.trips_csv, payload.buses_csv, payload.config)
        finally:
            SIMULATION_LOCK.release()

    background_tasks.add_task(run_worker)

    return {
        "run_id": run_id,
        "status": "queued",
        "current_stage": "Queued",
    }


@app.get("/api/results/{run_id}", response_model=SimulationRunResult)
def get_results(run_id: str):
    if run_id not in RUN_STORE:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    return RUN_STORE[run_id]


@app.get("/api/results/{run_id}/download/{report_type}")
def download_report(run_id: str, report_type: str):
    run_dir = os.path.join(RUNS_DIR, run_id)
    if not os.path.exists(run_dir):
        raise HTTPException(status_code=404, detail="Run output directory not found.")

    valid_reports = {
        "final_schedule": ("final_schedule.csv", "text/csv"),
        "baseline_schedule": ("baseline_schedule.csv", "text/csv"),
        "qaoa_candidates": ("qaoa_candidates.csv", "text/csv"),
        "validation_report": ("validation_report.csv", "text/csv"),
        "comparison_metrics": ("comparison_metrics.csv", "text/csv"),
        "run_metadata": ("run_metadata.json", "application/json"),
    }

    if report_type not in valid_reports:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid report type. Allowed types: {list(valid_reports.keys())}",
        )

    filename, media_type = valid_reports[report_type]
    file_path = os.path.join(run_dir, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Report file '{filename}' has not been generated.")

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename,
    )


# Serve frontend build if dist directory exists (e.g. for Render or unified deployment)
FRONTEND_DIST = os.environ.get(
    "FRONTEND_DIST_DIR",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")),
)
if not os.path.exists(FRONTEND_DIST):
    alt_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "dist"))
    if os.path.exists(alt_dist):
        FRONTEND_DIST = alt_dist

if os.path.exists(FRONTEND_DIST) and os.path.exists(os.path.join(FRONTEND_DIST, "index.html")):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="static")
else:
    @app.get("/")
    def root():
        return {
            "status": "online",
            "service": "Q-TRANSIT Backend API",
            "health_check": "/api/health",
            "docs": "/docs",
            "problem_id": "UC-053",
            "team": "HYPERQUBITS",
        }


