import React, { useState, useEffect } from 'react';
import {
  fetchHealth,
  fetchSampleData,
  validateCsvData,
  startSimulation,
  fetchRunResults,
} from './api/client';
import {
  DataValidationResult,
  SimulationConfig,
  SimulationRunResult,
} from './types';
import { GanttTimeline } from './components/GanttTimeline';
import { ComparisonTable } from './components/ComparisonTable';
import { QUBOInspector } from './components/QUBOInspector';
import { CandidateDistribution } from './components/CandidateDistribution';
import { ValidatorReportCard } from './components/ValidatorReportCard';
import { ExportPanel } from './components/ExportPanel';

export const App: React.FC = () => {
  // Navigation tabs
  const [activeTab, setActiveTab] = useState<'upload' | 'config' | 'results' | 'export'>('upload');

  // Backend Health
  const [backendStatus, setBackendStatus] = useState<string>('connecting');

  // Input Data States
  const [tripsCsv, setTripsCsv] = useState<string>('');
  const [busesCsv, setBusesCsv] = useState<string>('');
  const [validationResult, setValidationResult] = useState<DataValidationResult | null>(null);
  const [isValidating, setIsValidating] = useState<boolean>(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  // Simulation Configuration
  const [config, setConfig] = useState<SimulationConfig>({
    cost_weight: 0.20,
    qaoa_p: 1,
    shots: 512,
    max_iter: 25,
    seed: 42,
    p_duplicate: 2.0,
    p_overlap: 2.0,
    variable_cap: 16,
    wall_time_limit_sec: 120.0,
  });

  // Simulation Execution & Progress
  const [currentRunId, setCurrentRunId] = useState<string | null>(null);
  const [runResult, setRunResult] = useState<SimulationRunResult | null>(null);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [simError, setSimError] = useState<string | null>(null);

  // Results View Sub-Tab
  const [resultsSubTab, setResultsSubTab] = useState<'timeline' | 'comparison' | 'qubo' | 'qaoa' | 'validation'>('timeline');

  // Check health on mount
  useEffect(() => {
    fetchHealth()
      .then(() => setBackendStatus('online'))
      .catch(() => setBackendStatus('offline'));
  }, []);

  // Handle loading sample dataset
  const handleLoadSampleData = async () => {
    try {
      setIsValidating(true);
      setValidationError(null);
      const data = await fetchSampleData();
      setTripsCsv(data.trips_csv);
      setBusesCsv(data.buses_csv);
      const val = await validateCsvData(data.trips_csv, data.buses_csv, config.cost_weight);
      setValidationResult(val);
    } catch (err: any) {
      setValidationError(err.message || 'Failed to load sample dataset');
    } finally {
      setIsValidating(false);
    }
  };

  // Handle manual validation
  const handleValidate = async () => {
    if (!tripsCsv.trim() || !busesCsv.trim()) {
      setValidationError('Please provide both trips.csv and buses.csv content.');
      return;
    }
    try {
      setIsValidating(true);
      setValidationError(null);
      const val = await validateCsvData(tripsCsv, busesCsv, config.cost_weight);
      setValidationResult(val);
    } catch (err: any) {
      setValidationError(err.message || 'Validation failed');
    } finally {
      setIsValidating(false);
    }
  };

  // Handle file uploads
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>, type: 'trips' | 'buses') => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      if (type === 'trips') setTripsCsv(content);
      else setBusesCsv(content);
    };
    reader.readAsText(file);
  };

  // Handle starting simulation
  const handleStartSimulation = async () => {
    if (!validationResult || !validationResult.is_valid) {
      setSimError('Please validate valid CSV datasets before launching optimization.');
      return;
    }

    try {
      setIsSimulating(true);
      setSimError(null);
      const { run_id } = await startSimulation(tripsCsv, busesCsv, config);
      setCurrentRunId(run_id);
      setActiveTab('results');

      // Poll for simulation completion
      const pollInterval = setInterval(async () => {
        try {
          const res = await fetchRunResults(run_id);
          setRunResult(res);
          if (res.status === 'succeeded' || res.status === 'partial' || res.status === 'failed') {
            clearInterval(pollInterval);
            setIsSimulating(false);
            if (res.status === 'failed') {
              setSimError(res.error_message || 'Optimization pipeline failed.');
            }
          }
        } catch (pollErr: any) {
          clearInterval(pollInterval);
          setIsSimulating(false);
          setSimError(pollErr.message);
        }
      }, 600);
    } catch (err: any) {
      setIsSimulating(false);
      setSimError(err.message || 'Failed to launch simulation');
    }
  };

  const stagesList = [
    'Validating data',
    'Preprocessing trips',
    'Building baseline',
    'Constructing QUBO',
    'Running QAOA',
    'Validating candidates',
    'Comparing results',
    'Preparing reports',
  ];

  return (
    <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '1.5rem 1rem' }}>
      {/* SCREEN 1: HEADER & DASHBOARD OVERVIEW */}
      <header style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.25rem' }}>
            <h1 style={{ fontSize: '1.75rem', fontWeight: 800, background: 'linear-gradient(135deg, #22d3ee, #3b82f6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              Q-TRANSIT
            </h1>
            <span className="badge badge-info font-mono">UC-053</span>
            <span className="badge badge-info">HYPERQUBITS</span>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Quantum-Enhanced Intelligent Bus Scheduling & Route Optimization Decision-Support Prototype
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            <span
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: backendStatus === 'online' ? '#10b981' : '#f43f5e',
              }}
            />
            <span>Backend: {backendStatus}</span>
          </div>

          <button
            onClick={handleLoadSampleData}
            disabled={isValidating || isSimulating}
            className="btn btn-secondary"
            title="Load synthetic 6-trip, 3-bus sample dataset"
          >
            ⚡ Load Sample Dataset
          </button>
        </div>
      </header>

      {/* WORKFLOW NAVIGATION TABS */}
      <nav style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid var(--border-color)', marginBottom: '1.5rem', overflowX: 'auto' }}>
        <button
          onClick={() => setActiveTab('upload')}
          style={{
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'upload' ? '2.5px solid var(--accent-cyan)' : '2.5px solid transparent',
            color: activeTab === 'upload' ? 'var(--text-primary)' : 'var(--text-muted)',
            padding: '0.75rem 1.25rem',
            cursor: 'pointer',
            fontWeight: 600,
            fontSize: '0.9rem',
          }}
        >
          1. Data Ingestion & Validation
        </button>

        <button
          onClick={() => setActiveTab('config')}
          style={{
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'config' ? '2.5px solid var(--accent-cyan)' : '2.5px solid transparent',
            color: activeTab === 'config' ? 'var(--text-primary)' : 'var(--text-muted)',
            padding: '0.75rem 1.25rem',
            cursor: 'pointer',
            fontWeight: 600,
            fontSize: '0.9rem',
          }}
        >
          2. Optimization Configuration
        </button>

        <button
          onClick={() => setActiveTab('results')}
          style={{
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'results' ? '2.5px solid var(--accent-cyan)' : '2.5px solid transparent',
            color: activeTab === 'results' ? 'var(--text-primary)' : 'var(--text-muted)',
            padding: '0.75rem 1.25rem',
            cursor: 'pointer',
            fontWeight: 600,
            fontSize: '0.9rem',
          }}
        >
          3. Simulation & Results Dashboard
        </button>

        <button
          onClick={() => setActiveTab('export')}
          disabled={!runResult}
          style={{
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'export' ? '2.5px solid var(--accent-cyan)' : '2.5px solid transparent',
            color: activeTab === 'export' ? 'var(--text-primary)' : 'var(--text-muted)',
            padding: '0.75rem 1.25rem',
            cursor: runResult ? 'pointer' : 'not-allowed',
            opacity: runResult ? 1 : 0.4,
            fontWeight: 600,
            fontSize: '0.9rem',
          }}
        >
          4. Export CSV Reports
        </button>
      </nav>

      {/* SCREEN 2 & 3: DATA UPLOAD & VALIDATION */}
      {activeTab === 'upload' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1.25rem' }}>
            {/* trips.csv card */}
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>trips.csv</h3>
                <label className="btn btn-secondary" style={{ padding: '0.3rem 0.75rem', fontSize: '0.75rem', cursor: 'pointer' }}>
                  Browse File
                  <input type="file" accept=".csv" onChange={(e) => handleFileUpload(e, 'trips')} style={{ display: 'none' }} />
                </label>
              </div>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                Required columns: trip_id, route_id, start_min, duration_min, passenger_demand, priority, operating_cost
              </p>
              <textarea
                value={tripsCsv}
                onChange={(e) => setTripsCsv(e.target.value)}
                placeholder="Paste or upload trips.csv content here..."
                style={{
                  width: '100%',
                  height: '180px',
                  background: 'var(--bg-secondary)',
                  color: 'var(--text-primary)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '6px',
                  padding: '0.5rem',
                  fontFamily: 'monospace',
                  fontSize: '0.75rem',
                  resize: 'vertical',
                }}
              />
            </div>

            {/* buses.csv card */}
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>buses.csv</h3>
                <label className="btn btn-secondary" style={{ padding: '0.3rem 0.75rem', fontSize: '0.75rem', cursor: 'pointer' }}>
                  Browse File
                  <input type="file" accept=".csv" onChange={(e) => handleFileUpload(e, 'buses')} style={{ display: 'none' }} />
                </label>
              </div>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                Required columns: bus_id, capacity, available_from_min, available_to_min
              </p>
              <textarea
                value={busesCsv}
                onChange={(e) => setBusesCsv(e.target.value)}
                placeholder="Paste or upload buses.csv content here..."
                style={{
                  width: '100%',
                  height: '180px',
                  background: 'var(--bg-secondary)',
                  color: 'var(--text-primary)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '6px',
                  padding: '0.5rem',
                  fontFamily: 'monospace',
                  fontSize: '0.75rem',
                  resize: 'vertical',
                }}
              />
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              Times are in minutes after midnight (e.g. 480 = 08:00, 540 = 09:00). Max 1440 min.
            </div>
            <button
              onClick={handleValidate}
              disabled={isValidating || !tripsCsv.trim() || !busesCsv.trim()}
              className="btn btn-primary"
            >
              {isValidating ? 'Validating Data...' : 'Verify & Inspect CSVs'}
            </button>
          </div>

          {validationError && (
            <div style={{ background: 'rgba(244, 63, 94, 0.1)', border: '1px solid rgba(244, 63, 94, 0.3)', borderRadius: '8px', padding: '0.75rem 1rem', color: '#fb7185', fontSize: '0.85rem' }}>
              <strong>Error:</strong> {validationError}
            </div>
          )}

          {/* Data Validation Report Screen */}
          {validationResult && (
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <div>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Data Quality & Eligibility Inspection</h3>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    Validation rules enforced before optimization pipeline starts.
                  </p>
                </div>
                <span className={`badge ${validationResult.is_valid ? 'badge-success' : 'badge-danger'}`}>
                  {validationResult.is_valid ? 'Valid Dataset' : 'Errors Detected'}
                </span>
              </div>

              {/* KPI metrics */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '0.75rem', marginBottom: '1.25rem' }}>
                <div style={{ background: 'var(--bg-secondary)', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Trips Received</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{validationResult.trips_received}</div>
                </div>
                <div style={{ background: 'var(--bg-secondary)', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Buses Available</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{validationResult.buses_received}</div>
                </div>
                <div style={{ background: 'var(--bg-secondary)', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Eligible (Trip, Bus) Pairs</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>{validationResult.eligible_assignments_count}</div>
                </div>
                <div style={{ background: 'var(--bg-secondary)', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Unassignable Trips</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700, color: validationResult.unassignable_trips.length > 0 ? '#fbbf24' : 'var(--text-muted)' }}>
                    {validationResult.unassignable_trips.length}
                  </div>
                </div>
              </div>

              {/* Warnings or Errors */}
              {validationResult.issues.length > 0 && (
                <div style={{ marginBottom: '1.25rem' }}>
                  <h4 style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>
                    Reported Issues & Warnings
                  </h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                    {validationResult.issues.map((iss, i) => (
                      <div
                        key={i}
                        style={{
                          background: iss.level === 'ERROR' ? 'rgba(244, 63, 94, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                          border: `1px solid ${iss.level === 'ERROR' ? 'rgba(244, 63, 94, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`,
                          borderRadius: '6px',
                          padding: '0.5rem 0.75rem',
                          fontSize: '0.8rem',
                          color: iss.level === 'ERROR' ? '#fb7185' : '#fbbf24',
                        }}
                      >
                        <strong>[{iss.file}{iss.row ? ` Row ${iss.row}` : ''}{iss.column ? ` Col ${iss.column}` : ''}]:</strong> {iss.reason}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Data Preview Table */}
              <h4 style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>
                Valid Trips & Evaluated Utility Values
              </h4>
              <div style={{ overflowX: 'auto', maxHeight: '240px' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
                  <thead>
                    <tr style={{ color: 'var(--text-muted)', borderBottom: '1px solid var(--border-color)' }}>
                      <th style={{ padding: '0.5rem' }}>Trip ID</th>
                      <th style={{ padding: '0.5rem' }}>Route</th>
                      <th style={{ padding: '0.5rem' }}>Interval</th>
                      <th style={{ padding: '0.5rem' }}>Demand</th>
                      <th style={{ padding: '0.5rem' }}>Priority</th>
                      <th style={{ padding: '0.5rem' }}>Cost</th>
                      <th style={{ padding: '0.5rem' }}>Utility (r_i)</th>
                      <th style={{ padding: '0.5rem' }}>Eligible Buses</th>
                    </tr>
                  </thead>
                  <tbody>
                    {validationResult.trips.map((t) => (
                      <tr key={t.trip_id} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                        <td style={{ padding: '0.5rem', fontWeight: 600, color: 'var(--accent-cyan)' }}>{t.trip_id}</td>
                        <td style={{ padding: '0.5rem' }}>{t.route_id}</td>
                        <td style={{ padding: '0.5rem', fontFamily: 'monospace' }}>[{t.start_min}, {t.end_min})</td>
                        <td style={{ padding: '0.5rem' }}>{t.passenger_demand}</td>
                        <td style={{ padding: '0.5rem' }}>{t.priority}</td>
                        <td style={{ padding: '0.5rem' }}>${t.operating_cost}</td>
                        <td style={{ padding: '0.5rem', fontFamily: 'monospace', color: (t.utility ?? 0) > 0 ? '#34d399' : '#fb7185' }}>
                          {t.utility?.toFixed(4) ?? '0.0000'}
                        </td>
                        <td style={{ padding: '0.5rem' }}>
                          {t.eligible_buses.length > 0 ? (
                            <span style={{ color: '#22d3ee' }}>{t.eligible_buses.join(', ')}</span>
                          ) : (
                            <span className="badge badge-warning">Unassignable</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div style={{ marginTop: '1.25rem', textAlign: 'right' }}>
                <button
                  onClick={() => setActiveTab('config')}
                  disabled={!validationResult.is_valid}
                  className="btn btn-primary"
                >
                  Configure Simulation →
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* SCREEN 4: SIMULATION CONFIGURATION */}
      {activeTab === 'config' && (
        <div className="card" style={{ maxWidth: '800px', margin: '0 auto' }}>
          <div style={{ marginBottom: '1.5rem' }}>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 600 }}>Simulation & Solver Configuration</h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Adjust classical baseline utility weights, QAOA circuit depth, measurement shots, and penalty terms.
            </p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {/* Cost weight slider */}
            <div style={{ background: 'var(--bg-secondary)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <label style={{ fontWeight: 600, fontSize: '0.85rem' }}>
                  Operating Cost Weight (cost_weight): <span style={{ color: 'var(--accent-cyan)' }}>{config.cost_weight.toFixed(2)}</span>
                </label>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Default: 0.20</span>
              </div>
              <input
                type="range"
                min="0.0"
                max="1.0"
                step="0.05"
                value={config.cost_weight}
                onChange={(e) => setConfig({ ...config, cost_weight: parseFloat(e.target.value) })}
                style={{ width: '100%', accentColor: 'var(--accent-cyan)' }}
              />
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.5rem', fontFamily: 'monospace' }}>
                utility = (1 - {config.cost_weight.toFixed(2)}) × norm_service - {config.cost_weight.toFixed(2)} × norm_cost
              </div>
            </div>

            {/* QAOA Parameters */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.3rem' }}>
                  QAOA Circuit Depth (p)
                </label>
                <select
                  value={config.qaoa_p}
                  onChange={(e) => setConfig({ ...config, qaoa_p: parseInt(e.target.value) })}
                  style={{ width: '100%', padding: '0.6rem', background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: '6px', color: 'var(--text-primary)' }}
                >
                  <option value={1}>p = 1 (Standard Laptop Demo)</option>
                  <option value={2}>p = 2 (Deeper Ansatz)</option>
                  <option value={3}>p = 3 (High Precision)</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.3rem' }}>
                  Measurement Shots
                </label>
                <select
                  value={config.shots}
                  onChange={(e) => setConfig({ ...config, shots: parseInt(e.target.value) })}
                  style={{ width: '100%', padding: '0.6rem', background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: '6px', color: 'var(--text-primary)' }}
                >
                  <option value={256}>256 Shots</option>
                  <option value={512}>512 Shots (Default)</option>
                  <option value={1024}>1024 Shots</option>
                  <option value={2048}>2048 Shots</option>
                </select>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.3rem' }}>
                  Max Classical Iterations (COBYLA)
                </label>
                <input
                  type="number"
                  min="5"
                  max="100"
                  value={config.max_iter}
                  onChange={(e) => setConfig({ ...config, max_iter: parseInt(e.target.value) || 25 })}
                  style={{ width: '100%', padding: '0.6rem', background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: '6px', color: 'var(--text-primary)' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.3rem' }}>
                  Random Simulation Seed
                </label>
                <input
                  type="number"
                  value={config.seed}
                  onChange={(e) => setConfig({ ...config, seed: parseInt(e.target.value) || 42 })}
                  style={{ width: '100%', padding: '0.6rem', background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: '6px', color: 'var(--text-primary)' }}
                />
              </div>
            </div>

            {/* QUBO Penalty Weights */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.3rem' }}>
                  Duplicate Trip Penalty (P_duplicate)
                </label>
                <input
                  type="number"
                  step="0.5"
                  min="0.5"
                  value={config.p_duplicate}
                  onChange={(e) => setConfig({ ...config, p_duplicate: parseFloat(e.target.value) || 2.0 })}
                  style={{ width: '100%', padding: '0.6rem', background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: '6px', color: 'var(--text-primary)' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.3rem' }}>
                  Schedule Overlap Penalty (P_overlap)
                </label>
                <input
                  type="number"
                  step="0.5"
                  min="0.5"
                  value={config.p_overlap}
                  onChange={(e) => setConfig({ ...config, p_overlap: parseFloat(e.target.value) || 2.0 })}
                  style={{ width: '100%', padding: '0.6rem', background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: '6px', color: 'var(--text-primary)' }}
                />
              </div>
            </div>

            {/* Laptop demonstration safety boundary info */}
            <div style={{ background: 'rgba(6, 182, 212, 0.08)', border: '1px solid rgba(6, 182, 212, 0.25)', borderRadius: '8px', padding: '0.75rem 1rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              <strong>Laptop Demonstration Boundary:</strong> Maximum {config.variable_cap} assignment variables. The supplied synthetic dataset contains 14 eligible variables and completes within ~2 seconds on local Qiskit Aer simulator.
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1rem' }}>
              <button onClick={() => setActiveTab('upload')} className="btn btn-secondary">
                ← Back to Data
              </button>
              <button
                onClick={handleStartSimulation}
                disabled={isSimulating}
                className="btn btn-primary"
                style={{ padding: '0.75rem 2rem', fontSize: '0.95rem' }}
              >
                {isSimulating ? 'Running Simulation...' : '🚀 Execute Full Optimization Pipeline'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* SCREEN 5 & 6: RUN PROGRESS & RESULTS DASHBOARD */}
      {activeTab === 'results' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* SCREEN 5: REAL STAGE PROGRESS TRACKER */}
          {isSimulating && (
            <div className="card card-glow">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span className="badge badge-info animate-pulse-glow">Running</span>
                  <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Simulation Pipeline Active</h3>
                </div>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                  {runResult?.current_stage || 'Initializing...'}
                </span>
              </div>

              {/* Real stages stepper */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '0.5rem' }}>
                {stagesList.map((stg) => {
                  const isCurrent = runResult?.current_stage === stg;
                  const isPast = runResult && stagesList.indexOf(runResult.current_stage) > stagesList.indexOf(stg);

                  return (
                    <div
                      key={stg}
                      style={{
                        padding: '0.5rem 0.6rem',
                        borderRadius: '6px',
                        background: isCurrent ? 'rgba(6, 182, 212, 0.2)' : isPast ? 'rgba(16, 185, 129, 0.1)' : 'var(--bg-secondary)',
                        border: `1px solid ${isCurrent ? 'var(--accent-cyan)' : isPast ? 'rgba(16, 185, 129, 0.3)' : 'var(--border-color)'}`,
                        fontSize: '0.7rem',
                        fontWeight: 600,
                        color: isCurrent ? '#22d3ee' : isPast ? '#34d399' : 'var(--text-muted)',
                        textAlign: 'center',
                      }}
                    >
                      {stg}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {simError && (
            <div style={{ background: 'rgba(244, 63, 94, 0.1)', border: '1px solid rgba(244, 63, 94, 0.3)', borderRadius: '8px', padding: '1rem', color: '#fb7185' }}>
              <strong>Execution Note:</strong> {simError}
            </div>
          )}

          {/* SCREEN 6: RESULTS OVERVIEW */}
          {runResult && (
            <>
              {/* Top KPI Cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.75rem' }}>
                <div className="card">
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Trips Scheduled</div>
                  <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>
                    {runResult.final_metrics?.trips_served ?? '-'}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
                    Coverage: {runResult.final_metrics?.coverage_rate ?? '-'}
                  </div>
                </div>

                <div className="card">
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Passengers Served</div>
                  <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#34d399' }}>
                    {runResult.final_metrics?.passenger_demand_served ?? '-'} pax
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
                    Demand Cov: {runResult.final_metrics?.passenger_demand_coverage ?? '-'}
                  </div>
                </div>

                <div className="card">
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Operating Cost</div>
                  <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#fbbf24' }}>
                    ${runResult.final_metrics?.operating_cost ?? '-'}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
                    Utilization: {runResult.final_metrics?.fleet_utilization ?? '-'}
                  </div>
                </div>

                <div className="card">
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Independent Feasibility</div>
                  <div style={{ fontSize: '1.4rem', fontWeight: 700 }}>
                    <span className={`badge ${runResult.final_metrics?.feasible === 'Yes' ? 'badge-success' : 'badge-danger'}`} style={{ fontSize: '0.85rem' }}>
                      {runResult.final_metrics?.feasible === 'Yes' ? '100% Feasible' : 'Infeasible'}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
                    Violations: {runResult.final_metrics?.constraint_violations ?? 0}
                  </div>
                </div>

                <div className="card">
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Solver Runtimes</div>
                  <div style={{ fontSize: '0.95rem', fontWeight: 600, fontFamily: 'monospace', color: 'var(--text-primary)', marginTop: '0.2rem' }}>
                    Base: {runResult.baseline_metrics?.runtime_seconds ?? 0}s
                  </div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 600, fontFamily: 'monospace', color: 'var(--accent-cyan)' }}>
                    QAOA: {runResult.best_qaoa_metrics?.runtime_seconds ?? '-'}s
                  </div>
                </div>
              </div>

              {/* Sub-tab navigation for detailed views */}
              <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.25rem', overflowX: 'auto' }}>
                <button
                  onClick={() => setResultsSubTab('timeline')}
                  className={`btn ${resultsSubTab === 'timeline' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem' }}
                >
                  📅 Visual Timeline (Gantt)
                </button>
                <button
                  onClick={() => setResultsSubTab('comparison')}
                  className={`btn ${resultsSubTab === 'comparison' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem' }}
                >
                  ⚖️ Fair Comparison Table
                </button>
                <button
                  onClick={() => setResultsSubTab('qubo')}
                  className={`btn ${resultsSubTab === 'qubo' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem' }}
                >
                  📐 QUBO Model Inspection
                </button>
                <button
                  onClick={() => setResultsSubTab('qaoa')}
                  className={`btn ${resultsSubTab === 'qaoa' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem' }}
                >
                  ⚛️ QAOA Candidates & Bitstrings
                </button>
                <button
                  onClick={() => setResultsSubTab('validation')}
                  className={`btn ${resultsSubTab === 'validation' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem' }}
                >
                  🛡️ Classical Validator Report
                </button>
              </div>

              {/* Sub-Tab Content Panes */}
              {resultsSubTab === 'timeline' && (
                <GanttTimeline
                  schedule={runResult.final_schedule}
                  buses={runResult.data_validation?.buses || []}
                  title="Final Operable Bus Schedule (Timeline View)"
                />
              )}

              {resultsSubTab === 'comparison' && (
                <ComparisonTable
                  baseline={runResult.baseline_metrics}
                  qaoa={runResult.best_qaoa_metrics}
                />
              )}

              {resultsSubTab === 'qubo' && (
                <QUBOInspector summary={runResult.qubo_summary} />
              )}

              {resultsSubTab === 'qaoa' && (
                <CandidateDistribution
                  candidates={runResult.qaoa_candidates}
                  bestCandidate={runResult.best_feasible_qaoa}
                />
              )}

              {resultsSubTab === 'validation' && (
                <ValidatorReportCard validation={runResult.final_validation} />
              )}

              {/* Selection & Rejection Explanations Table */}
              <div className="card">
                <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '0.5rem' }}>
                  Decision Transparency: Selection & Rejection Explanations
                </h3>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                  Plain-language operational explanations for why each trip was scheduled or rejected.
                </p>
                <div style={{ overflowX: 'auto', maxHeight: '250px' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
                    <thead>
                      <tr style={{ color: 'var(--text-muted)', borderBottom: '1px solid var(--border-color)' }}>
                        <th style={{ padding: '0.5rem' }}>Trip ID</th>
                        <th style={{ padding: '0.5rem' }}>Assigned Bus</th>
                        <th style={{ padding: '0.5rem' }}>Status</th>
                        <th style={{ padding: '0.5rem' }}>Operational Reason</th>
                      </tr>
                    </thead>
                    <tbody>
                      {runResult.final_schedule.map((item) => (
                        <tr key={item.trip_id} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                          <td style={{ padding: '0.5rem', fontWeight: 600, color: 'var(--accent-cyan)' }}>{item.trip_id}</td>
                          <td style={{ padding: '0.5rem' }}>{item.bus_id ?? 'None'}</td>
                          <td style={{ padding: '0.5rem' }}>
                            <span className={`badge ${item.bus_id ? 'badge-success' : 'badge-warning'}`}>
                              {item.bus_id ? 'Scheduled' : 'Unassigned'}
                            </span>
                          </td>
                          <td style={{ padding: '0.5rem', color: 'var(--text-secondary)' }}>
                            {item.selection_reason || 'Feasible schedule assignment.'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Export Button Shortcut */}
              <div style={{ textAlign: 'right', marginTop: '0.5rem' }}>
                <button onClick={() => setActiveTab('export')} className="btn btn-primary">
                  Go to Export & Download Center →
                </button>
              </div>
            </>
          )}

          {!runResult && !isSimulating && (
            <div className="card text-center p-8 text-slate-400">
              No simulation has been run yet. Please go to "1. Data Ingestion & Validation" or click "⚡ Load Sample Dataset" above to start.
            </div>
          )}
        </div>
      )}

      {/* SCREEN 7: EXPORT & DOWNLOAD CENTER */}
      {activeTab === 'export' && runResult && (
        <ExportPanel runId={runResult.run_id} />
      )}
    </div>
  );
};

export default App;

