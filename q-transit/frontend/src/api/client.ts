import {
  DataValidationResult,
  SimulationConfig,
  SimulationRunResult,
} from '../types';

const API_BASE = '/api';

export async function fetchHealth(): Promise<{ status: string; service: string }> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export async function fetchSampleData(): Promise<{ trips_csv: string; buses_csv: string }> {
  const res = await fetch(`${API_BASE}/sample-data`);
  if (!res.ok) throw new Error('Failed to load sample data');
  return res.json();
}

export async function validateCsvData(
  trips_csv: string,
  buses_csv: string,
  cost_weight: number = 0.20
): Promise<DataValidationResult> {
  const res = await fetch(`${API_BASE}/validate-csv`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ trips_csv, buses_csv, cost_weight }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Validation endpoint failed');
  }
  return res.json();
}

export async function startSimulation(
  trips_csv: string,
  buses_csv: string,
  config: SimulationConfig
): Promise<{ run_id: string; status: string; current_stage: string }> {
  const res = await fetch(`${API_BASE}/run-simulation`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ trips_csv, buses_csv, config }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Simulation start failed');
  }
  return res.json();
}

export async function fetchRunResults(run_id: string): Promise<SimulationRunResult> {
  const res = await fetch(`${API_BASE}/results/${run_id}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to fetch run results');
  }
  return res.json();
}

export function getDownloadUrl(run_id: string, reportType: string): string {
  return `${API_BASE}/results/${run_id}/download/${reportType}`;
}

