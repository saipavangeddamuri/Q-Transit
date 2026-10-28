import React from 'react';
import { ComparisonMetrics } from '../types';

interface ComparisonProps {
  baseline?: ComparisonMetrics | null;
  qaoa?: ComparisonMetrics | null;
}

export const ComparisonTable: React.FC<ComparisonProps> = ({ baseline, qaoa }) => {
  const metricsList = [
    { label: 'Trips Served', key: 'trips_served', desc: 'Number of candidate trips scheduled' },
    { label: 'Passenger Demand Served', key: 'passenger_demand_served', desc: 'Total passengers accommodated' },
    { label: 'Weighted Service Value', key: 'weighted_service_value', desc: 'Sum of (demand × priority)' },
    { label: 'Operating Cost', key: 'operating_cost', desc: 'Total cost of operating assigned trips' },
    { label: 'Trip Utility', key: 'trip_utility', desc: 'Balanced reward metric (service vs cost)' },
    { label: 'Coverage Rate (Eligible Trips)', key: 'coverage_rate', desc: 'Selected trips ÷ assignable trips' },
    { label: 'Passenger Demand Coverage', key: 'passenger_demand_coverage', desc: 'Demand served ÷ total eligible demand' },
    { label: 'Fleet Utilization', key: 'fleet_utilization', desc: 'Assigned trip-minutes ÷ available bus-minutes' },
    { label: 'Constraint Violations', key: 'constraint_violations', desc: 'Independent validator hard violations' },
    { label: 'Solver Runtime (s)', key: 'runtime_seconds', desc: 'Wall-clock solver execution time' },
    { label: 'Feasible Schedule', key: 'feasible', desc: 'Passes all 6 independent constraint checks' },
  ];

  return (
    <div className="card">
      <div style={{ marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Fair Comparison Framework</h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Identical inputs, objective formulation, and independent operational constraint validation.
          </p>
        </div>
        <span className="badge badge-info">Side-by-Side</span>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-secondary)' }}>
              <th style={{ padding: '0.75rem 1rem' }}>Metric</th>
              <th style={{ padding: '0.75rem 1rem', width: '220px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#3b82f6' }}></span>
                  <span>Classical Greedy Baseline</span>
                </div>
              </th>
              <th style={{ padding: '0.75rem 1rem', width: '240px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#06b6d4' }}></span>
                  <span>Best Feasible QAOA Candidate</span>
                </div>
              </th>
            </tr>
          </thead>
          <tbody>
            {metricsList.map((m, idx) => {
              const baseVal = baseline ? (baseline as any)[m.key] : 'N/A';
              const qaoaVal = qaoa ? (qaoa as any)[m.key] : 'No feasible QAOA candidate';

              const isFeasibleRow = m.key === 'feasible';
              const isViolationsRow = m.key === 'constraint_violations';

              return (
                <tr
                  key={m.key}
                  style={{
                    borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                    background: idx % 2 === 0 ? 'transparent' : 'rgba(255, 255, 255, 0.01)',
                  }}
                >
                  <td style={{ padding: '0.75rem 1rem' }}>
                    <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{m.label}</div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{m.desc}</div>
                  </td>
                  <td style={{ padding: '0.75rem 1rem', fontFamily: 'monospace' }}>
                    {isFeasibleRow ? (
                      <span className={`badge ${baseVal === 'Yes' ? 'badge-success' : 'badge-danger'}`}>
                        {baseVal}
                      </span>
                    ) : isViolationsRow ? (
                      <span style={{ color: baseVal === 0 ? '#34d399' : '#fb7185', fontWeight: 600 }}>
                        {baseVal}
                      </span>
                    ) : (
                      <span>{baseVal ?? 'N/A'}</span>
                    )}
                  </td>
                  <td style={{ padding: '0.75rem 1rem', fontFamily: 'monospace' }}>
                    {isFeasibleRow ? (
                      qaoa ? (
                        <span className={`badge ${qaoaVal === 'Yes' ? 'badge-success' : 'badge-danger'}`}>
                          {qaoaVal}
                        </span>
                      ) : (
                        <span className="badge badge-warning">No feasible candidate</span>
                      )
                    ) : isViolationsRow ? (
                      <span style={{ color: qaoaVal === 0 ? '#34d399' : '#fb7185', fontWeight: 600 }}>
                        {qaoa ? qaoaVal : '-'}
                      </span>
                    ) : (
                      <span>{qaoaVal ?? 'No feasible candidate'}</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

