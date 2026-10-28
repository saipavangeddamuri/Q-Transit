import React from 'react';
import { QAOACandidate } from '../types';

interface CandidateProps {
  candidates: QAOACandidate[];
  bestCandidate?: QAOACandidate | null;
}

export const CandidateDistribution: React.FC<CandidateProps> = ({ candidates, bestCandidate }) => {
  if (!candidates || candidates.length === 0) {
    return (
      <div className="card text-center p-6 text-slate-400">
        No QAOA candidate solutions measured.
      </div>
    );
  }

  const maxCount = Math.max(...candidates.map(c => c.count), 1);

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <div>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>QAOA Candidate Solutions</h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Quantum circuit measurement bitstrings, QUBO energy values, and independent feasibility status.
          </p>
        </div>
        <span className="badge badge-info">{candidates.length} Unique Bitstrings</span>
      </div>

      <div style={{ maxHeight: '360px', overflowY: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
          <thead>
            <tr style={{ color: 'var(--text-muted)', borderBottom: '1px solid var(--border-color)' }}>
              <th style={{ padding: '0.5rem 0.75rem' }}>#</th>
              <th style={{ padding: '0.5rem 0.75rem' }}>Measured Bitstring</th>
              <th style={{ padding: '0.5rem 0.75rem', width: '160px' }}>Frequency & Probability</th>
              <th style={{ padding: '0.5rem 0.75rem' }}>QUBO Energy</th>
              <th style={{ padding: '0.5rem 0.75rem' }}>Trips</th>
              <th style={{ padding: '0.5rem 0.75rem' }}>Utility</th>
              <th style={{ padding: '0.5rem 0.75rem' }}>Feasibility</th>
            </tr>
          </thead>
          <tbody>
            {candidates.map((cand) => {
              const isBest = bestCandidate?.candidate_id === cand.candidate_id;
              const barWidth = Math.max((cand.count / maxCount) * 100, 4);

              return (
                <tr
                  key={cand.candidate_id}
                  style={{
                    borderBottom: '1px solid rgba(255,255,255,0.03)',
                    background: isBest ? 'rgba(6, 182, 212, 0.08)' : 'transparent',
                  }}
                >
                  <td style={{ padding: '0.5rem 0.75rem', fontWeight: 600 }}>
                    {cand.candidate_id}
                    {isBest && <span style={{ color: '#22d3ee', marginLeft: '4px' }}>★</span>}
                  </td>
                  <td style={{ padding: '0.5rem 0.75rem', fontFamily: 'monospace', color: '#22d3ee', fontSize: '0.75rem' }}>
                    {cand.bitstring}
                  </td>
                  <td style={{ padding: '0.5rem 0.75rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <div
                        style={{
                          flexGrow: 1,
                          height: '6px',
                          background: 'rgba(255,255,255,0.05)',
                          borderRadius: '3px',
                          overflow: 'hidden',
                        }}
                      >
                        <div
                          style={{
                            width: `${barWidth}%`,
                            height: '100%',
                            background: isBest ? 'var(--accent-cyan)' : 'var(--accent-blue)',
                          }}
                        />
                      </div>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', minWidth: '45px', textAlign: 'right' }}>
                        {(cand.probability * 100).toFixed(1)}% ({cand.count})
                      </span>
                    </div>
                  </td>
                  <td style={{ padding: '0.5rem 0.75rem', fontFamily: 'monospace', color: cand.qubo_energy < 0 ? '#34d399' : '#fbbf24' }}>
                    {cand.qubo_energy.toFixed(4)}
                  </td>
                  <td style={{ padding: '0.5rem 0.75rem' }}>
                    {cand.trips_served_count}
                  </td>
                  <td style={{ padding: '0.5rem 0.75rem', fontFamily: 'monospace' }}>
                    {cand.total_utility.toFixed(4)}
                  </td>
                  <td style={{ padding: '0.5rem 0.75rem' }}>
                    {cand.is_feasible ? (
                      <span className="badge badge-success">Feasible</span>
                    ) : (
                      <span
                        className="badge badge-danger"
                        title={cand.validation_summary}
                        style={{ cursor: 'help' }}
                      >
                        {cand.violations_count} Violations
                      </span>
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

