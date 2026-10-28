from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class TripRecord(BaseModel):
    trip_id: str
    route_id: str
    start_min: int
    duration_min: int
    passenger_demand: int
    priority: float
    operating_cost: float
    end_min: Optional[int] = None
    service_value: Optional[float] = None
    normalized_service: Optional[float] = None
    normalized_cost: Optional[float] = None
    utility: Optional[float] = None
    eligible_buses: List[str] = Field(default_factory=list)


class BusRecord(BaseModel):
    bus_id: str
    capacity: int
    available_from_min: int
    available_to_min: int
    total_available_minutes: Optional[int] = None


class ValidationIssue(BaseModel):
    file: str
    row: Optional[int] = None
    column: Optional[str] = None
    level: str  # "ERROR" or "WARNING"
    reason: str


class DataValidationResult(BaseModel):
    is_valid: bool
    trips_received: int
    buses_received: int
    valid_trips_count: int
    unassignable_trips: List[str] = Field(default_factory=list)
    issues: List[ValidationIssue] = Field(default_factory=list)
    trips: List[TripRecord] = Field(default_factory=list)
    buses: List[BusRecord] = Field(default_factory=list)
    eligible_assignments_count: int = 0
    max_service_value: float = 0.0
    max_operating_cost: float = 0.0


class AssignmentItem(BaseModel):
    trip_id: str
    route_id: str
    bus_id: Optional[str] = None
    start_min: int
    end_min: int
    passenger_demand: int
    capacity: Optional[int] = None
    operating_cost: float
    assignment_source: str  # "BASELINE", "RAW_QAOA", "FINAL"
    validation_status: str  # "FEASIBLE", "INFEASIBLE", "UNASSIGNED"
    utility: float = 0.0
    selection_reason: Optional[str] = None


class ConstraintViolation(BaseModel):
    constraint_name: str
    violation_count: int
    affected_ids: List[str] = Field(default_factory=list)
    explanation: str


class ScheduleValidationResult(BaseModel):
    is_feasible: bool
    total_violations: int
    violations: List[ConstraintViolation] = Field(default_factory=list)
    summary_message: str


class SimulationConfig(BaseModel):
    cost_weight: float = Field(default=0.20, ge=0.0, le=1.0)
    qaoa_p: int = Field(default=1, ge=1, le=3)
    shots: int = Field(default=512, ge=100, le=4096)
    max_iter: int = Field(default=25, ge=5, le=100)
    seed: int = Field(default=42)
    p_duplicate: float = Field(default=2.0, ge=0.1)
    p_overlap: float = Field(default=2.0, ge=0.1)
    variable_cap: int = Field(default=16, ge=4, le=32)
    wall_time_limit_sec: float = Field(default=120.0, ge=5.0)


class QUBOTermExplanation(BaseModel):
    variable_name: str
    trip_id: str
    bus_id: str
    linear_coefficient: float
    explanation: str


class QUBOSummary(BaseModel):
    num_variables: int
    variable_names: List[str]
    linear_terms: List[Dict[str, Any]]
    quadratic_terms_count: int
    quadratic_terms_preview: List[Dict[str, Any]]
    matrix_size: int
    penalty_duplicate: float
    penalty_overlap: float


class QAOACandidate(BaseModel):
    candidate_id: int
    bitstring: str
    count: int
    probability: float
    qubo_energy: float
    trips_served_count: int
    passenger_demand_served: int
    operating_cost: float
    service_value: float
    total_utility: float
    is_feasible: bool
    violations_count: int
    validation_summary: str
    assignments: List[AssignmentItem] = Field(default_factory=list)


class ComparisonMetrics(BaseModel):
    trips_served: Any
    passenger_demand_served: Any
    weighted_service_value: Any
    operating_cost: Any
    trip_utility: Any
    coverage_rate: Any  # Eligible-trip selection rate
    passenger_demand_coverage: Any
    fleet_utilization: Any
    constraint_violations: Any
    runtime_seconds: Any
    feasible: str  # "Yes" or "No"


class SimulationRunResult(BaseModel):
    run_id: str
    status: str  # "queued", "running", "succeeded", "partial", "failed"
    current_stage: str
    error_message: Optional[str] = None
    config: SimulationConfig
    data_validation: Optional[DataValidationResult] = None
    qubo_summary: Optional[QUBOSummary] = None
    baseline_schedule: List[AssignmentItem] = Field(default_factory=list)
    baseline_metrics: Optional[ComparisonMetrics] = None
    baseline_validation: Optional[ScheduleValidationResult] = None
    qaoa_candidates: List[QAOACandidate] = Field(default_factory=list)
    best_feasible_qaoa: Optional[QAOACandidate] = None
    best_qaoa_metrics: Optional[ComparisonMetrics] = None
    final_schedule: List[AssignmentItem] = Field(default_factory=list)
    final_metrics: Optional[ComparisonMetrics] = None
    final_validation: Optional[ScheduleValidationResult] = None
    qaoa_skipped_or_failed_reason: Optional[str] = None

