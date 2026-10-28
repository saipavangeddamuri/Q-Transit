import React from 'react';
import { getDownloadUrl } from '../api/client';

interface ExportProps {
  runId: string;
}

export const ExportPanel: React.FC<ExportProps> = ({ runId }) => {
  const reports = [
    {
      type: 'final_schedule',
      title: 'Final Schedule Report',
      filename: 'final_schedule.csv',
      format: 'CSV',
      desc: 'Selected trip-to-bus assignments, times, passenger demand, capacity, and operational status.',
      color: '#06b6d4',
    },
    {
      type: 'baseline_schedule',
      title: 'Classical Greedy Baseline',
      filename: 'baseline_schedule.csv',
      format: 'CSV',
      desc: 'Initial deterministic heuristic schedule with unassigned trip explanations.',
      color: '#3b82f6',
    },
    {
      type: 'qaoa_candidates',
      title: 'QAOA Measured Candidates',
      filename: 'qaoa_candidates.csv',
      format: 'CSV',
      desc: 'All unique measured bitstrings, QUBO energies, probabilities, and independent feasibility.',
      color: '#8b5cf6',
    },
    {
      type: 'validation_report',
      title: 'Constraint Validation Log',
      filename: 'validation_report.csv',
      format: 'CSV',
      desc: 'Rule-by-rule independent classical verification log with violation details.',
      color: '#10b981',
    },
    {
      type: 'comparison_metrics',
      title: 'Fair Comparison Metrics',
      filename: 'comparison_metrics.csv',
      format: 'CSV',
      desc: 'Side-by-side performance metrics between Greedy Baseline and Best Feasible QAOA.',
      color: '#f59e0b',
    },
    {
      type: 'run_metadata',
      title: 'Run Metadata & Settings',
      filename: 'run_metadata.json',
      format: 'JSON',
      desc: 'Complete configuration, weights, random seed, runtimes, and reproducibility audit trail.',
      color: '#ec4899',
    },
  ];

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
        <div>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Downloadable Simulation Reports</h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Export verified CSV and JSON run artifacts for analysis and demonstration presentation.
          </p>
        </div>
        <span className="badge badge-info">Run ID: {runId}</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
        {reports.map((r) => (
          <div
            key={r.type}
            style={{
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-color)',
              borderRadius: '10px',
              padding: '1rem',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
            }}
          >
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)' }}>{r.title}</h4>
                <span style={{ fontSize: '0.7rem', padding: '0.15rem 0.5rem', borderRadius: '4px', background: 'rgba(255,255,255,0.08)', fontFamily: 'monospace' }}>
                  {r.format}
                </span>
              </div>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '1rem', minHeight: '40px' }}>
                {r.desc}
              </p>
            </div>

            <a
              href={getDownloadUrl(runId, r.type)}
              download={r.filename}
              className="btn btn-secondary"
              style={{ width: '100%', fontSize: '0.8rem', borderLeft: `3px solid ${r.color}` }}
            >
              Download {r.filename}
            </a>
          </div>
        ))}
      </div>
    </div>
  );
};

