export interface TripRecord {
  trip_id: string;
  route_id: string;
  start_min: number;
  duration_min: number;
  passenger_demand: number;
  priority: number;
  operating_cost: number;
  end_min?: number;
  service_value?: number;
  normalized_service?: number;
  normalized_cost?: number;
  utility?: number;
  eligible_buses: string[];
}

export interface BusRecord {
  bus_id: string;
  capacity: number;
  available_from_min: number;
  available_to_min: number;
  total_available_minutes?: number;
}

export interface ValidationIssue {
  file: string;
  row?: number;
  column?: string;
  level: 'ERROR' | 'WARNING';
  reason: string;
}

export interface DataValidationResult {
  is_valid: boolean;
  trips_received: number;
  buses_received: number;
  valid_trips_count: number;
  unassignable_trips: string[];
  issues: ValidationIssue[];
  trips: TripRecord[];
  buses: BusRecord[];
  eligible_assignments_count: number;
  max_service_value: number;
  max_operating_cost: number;
}

export interface AssignmentItem {
  trip_id: string;
  route_id: string;
  bus_id?: string | null;
  start_min: number;
  end_min: number;
  passenger_demand: number;
  capacity?: number | null;
  operating_cost: number;
  assignment_source: string;
  validation_status: string;
  utility: number;
  selection_reason?: string | null;
}

export interface ConstraintViolation {
  constraint_name: string;
  violation_count: number;
  affected_ids: string[];
  explanation: string;
}

export interface ScheduleValidationResult {
  is_feasible: boolean;
  total_violations: number;
  violations: ConstraintViolation[];
  summary_message: string;
}

export interface SimulationConfig {
  cost_weight: number;
  qaoa_p: number;
  shots: number;
  max_iter: number;
  seed: number;
  p_duplicate: number;
  p_overlap: number;
  variable_cap: number;
  wall_time_limit_sec: number;
}

export interface QUBOSummary {
  num_variables: number;
  variable_names: string[];
  linear_terms: Array<{
    index: number;
    variable: string;
    trip_id: string;
    bus_id: string;
    utility: number;
    linear_coeff: number;
    explanation: string;
  }>;
  quadratic_terms_count: number;
  quadratic_terms_preview: Array<{
    var1: string;
    var2: string;
    type: string;
    penalty: number;
    explanation: string;
  }>;
  matrix_size: number;
  penalty_duplicate: number;
  penalty_overlap: number;
}

export interface QAOACandidate {
  candidate_id: number;
  bitstring: string;
  count: number;
  probability: number;
  qubo_energy: number;
  trips_served_count: number;
  passenger_demand_served: number;
  operating_cost: number;
  service_value: number;
  total_utility: number;
  is_feasible: boolean;
  violations_count: number;
  validation_summary: string;
  assignments: AssignmentItem[];
}

export interface ComparisonMetrics {
  trips_served: number | string;
  passenger_demand_served: number | string;
  weighted_service_value: number | string;
  operating_cost: number | string;
  trip_utility: number | string;
  coverage_rate: string;
  passenger_demand_coverage: string;
  fleet_utilization: string;
  constraint_violations: number | string;
  runtime_seconds: number | string;
  feasible: string;
}

export interface SimulationRunResult {
  run_id: string;
  status: 'queued' | 'running' | 'succeeded' | 'partial' | 'failed';
  current_stage: string;
  error_message?: string | null;
  config: SimulationConfig;
  data_validation?: DataValidationResult | null;
  qubo_summary?: QUBOSummary | null;
  baseline_schedule: AssignmentItem[];
  baseline_metrics?: ComparisonMetrics | null;
  baseline_validation?: ScheduleValidationResult | null;
  qaoa_candidates: QAOACandidate[];
  best_feasible_qaoa?: QAOACandidate | null;
  best_qaoa_metrics?: ComparisonMetrics | null;
  final_schedule: AssignmentItem[];
  final_metrics?: ComparisonMetrics | null;
  final_validation?: ScheduleValidationResult | null;
  qaoa_skipped_or_failed_reason?: string | null;
}

