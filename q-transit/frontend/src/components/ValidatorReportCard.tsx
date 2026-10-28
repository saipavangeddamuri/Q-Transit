import React from 'react';
import { ScheduleValidationResult } from '../types';

interface ValidatorProps {
  validation?: ScheduleValidationResult | null;
  title?: string;
}

export const ValidatorReportCard: React.FC<ValidatorProps> = ({
  validation,
  title = "Independent Classical Validation Report",
}) => {
  if (!validation) {
    return (
      <div className="card text-center p-6 text-slate-400">
        No validation results available.
      </div>
    );
  }

  const rules = [
    { name: "TRIP_EXISTENCE", label: "Trip Existence Check", desc: "Every assigned trip exists in uploaded trips.csv" },
    { name: "BUS_EXISTENCE", label: "Bus Existence Check", desc: "Every assigned bus exists in uploaded buses.csv" },
    { name: "NO_DUPLICATE_ASSIGNMENT", label: "Single Assignment Rule", desc: "No trip is assigned to multiple buses simultaneously" },
    { name: "BUS_CAPACITY", label: "Fleet Capacity Limit", desc: "Trip passenger demand ≤ assigned bus capacity" },
    { name: "BUS_AVAILABILITY_WINDOW", label: "Time Window Compliance", desc: "Trip duration falls entirely within bus availability window" },
    { name: "NO_BUS_OVERLAP", label: "No Schedule Conflicts", desc: "No two overlapping trips assigned to the same bus [start, end)" },
  ];

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <div>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>{title}</h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Strict independent classical verification without reusing optimizer assumptions.
          </p>
        </div>
        <span className={`badge ${validation.is_feasible ? 'badge-success' : 'badge-danger'}`}>
          {validation.is_feasible ? '100% FEASIBLE' : `${validation.total_violations} VIOLATION(S)`}
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '0.75rem', marginBottom: '1rem' }}>
        {rules.map((rule) => {
          const violation = validation.violations.find((v) => v.constraint_name === rule.name);
          const passed = !violation;

          return (
            <div
              key={rule.name}
              style={{
                background: 'var(--bg-secondary)',
                padding: '0.75rem 1rem',
                borderRadius: '8px',
                border: `1px solid ${passed ? 'var(--border-color)' : 'rgba(244, 63, 94, 0.4)'}`,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <div>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {rule.label}
                </div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{rule.desc}</div>
              </div>
              <span className={`badge ${passed ? 'badge-success' : 'badge-danger'}`}>
                {passed ? 'Passed' : `${violation?.violation_count} Failed`}
              </span>
            </div>
          );
        })}
      </div>

      {validation.violations.length > 0 && (
        <div style={{ background: 'rgba(244, 63, 94, 0.1)', border: '1px solid rgba(244, 63, 94, 0.25)', borderRadius: '8px', padding: '0.75rem 1rem' }}>
          <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: '#fb7185', marginBottom: '0.5rem' }}>
            Violation Details
          </h4>
          <ul style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', paddingLeft: '1.25rem' }}>
            {validation.violations.map((v, i) => (
              <li key={i} style={{ marginBottom: '0.35rem' }}>
                <strong style={{ color: 'var(--text-primary)' }}>{v.constraint_name}:</strong> {v.explanation} (Affected: {v.affected_ids.join(', ')})
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

