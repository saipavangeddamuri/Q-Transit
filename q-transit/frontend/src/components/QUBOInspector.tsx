import React, { useState } from 'react';
import { QUBOSummary } from '../types';

interface QUBOProps {
  summary?: QUBOSummary | null;
}

export const QUBOInspector: React.FC<QUBOProps> = ({ summary }) => {
  const [activeTab, setActiveTab] = useState<'linear' | 'quadratic'>('linear');

  if (!summary) {
    return (
      <div className="card text-center p-6 text-slate-400">
        QUBO model has not been generated yet.
      </div>
    );
  }

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <div>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>QUBO Mathematical Formulation</h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Quadratic Unconstrained Binary Optimization model mapped to Ising Hamiltonian for QAOA simulation.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <span className="badge badge-info">{summary.num_variables} Binary Variables</span>
          <span className="badge badge-warning">{summary.quadratic_terms_count} Conflict Penalties</span>
        </div>
      </div>

      {/* Model Stats Bar */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.75rem', marginBottom: '1rem' }}>
        <div style={{ background: 'var(--bg-secondary)', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Matrix Dimension</div>
          <div style={{ fontSize: '1.1rem', fontWeight: 700, fontFamily: 'monospace' }}>{summary.matrix_size} × {summary.matrix_size}</div>
        </div>
        <div style={{ background: 'var(--bg-secondary)', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Duplicate Penalty (P_dup)</div>
          <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fbbf24', fontFamily: 'monospace' }}>+{summary.penalty_duplicate}</div>
        </div>
        <div style={{ background: 'var(--bg-secondary)', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Overlap Penalty (P_overlap)</div>
          <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fb7185', fontFamily: 'monospace' }}>+{summary.penalty_overlap}</div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid var(--border-color)', marginBottom: '0.75rem' }}>
        <button
          onClick={() => setActiveTab('linear')}
          style={{
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'linear' ? '2px solid var(--accent-cyan)' : '2px solid transparent',
            color: activeTab === 'linear' ? 'var(--text-primary)' : 'var(--text-muted)',
            padding: '0.5rem 1rem',
            cursor: 'pointer',
            fontWeight: 600,
            fontSize: '0.85rem',
          }}
        >
          Diagonal Terms (Linear Rewards) ({summary.linear_terms.length})
        </button>
        <button
          onClick={() => setActiveTab('quadratic')}
          style={{
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'quadratic' ? '2px solid var(--accent-cyan)' : '2px solid transparent',
            color: activeTab === 'quadratic' ? 'var(--text-primary)' : 'var(--text-muted)',
            padding: '0.5rem 1rem',
            cursor: 'pointer',
            fontWeight: 600,
            fontSize: '0.85rem',
          }}
        >
          Off-Diagonal Terms (Conflict Penalties) ({summary.quadratic_terms_count})
        </button>
      </div>

      {/* Tab Content */}
      <div style={{ maxHeight: '280px', overflowY: 'auto' }}>
        {activeTab === 'linear' ? (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
            <thead>
              <tr style={{ color: 'var(--text-muted)', borderBottom: '1px solid var(--border-color)' }}>
                <th style={{ padding: '0.5rem' }}>Index</th>
                <th style={{ padding: '0.5rem' }}>Variable</th>
                <th style={{ padding: '0.5rem' }}>Trip</th>
                <th style={{ padding: '0.5rem' }}>Bus</th>
                <th style={{ padding: '0.5rem' }}>Trip Utility</th>
                <th style={{ padding: '0.5rem' }}>Q_kk (Energy Coeff)</th>
              </tr>
            </thead>
            <tbody>
              {summary.linear_terms.map(item => (
                <tr key={item.variable} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                  <td style={{ padding: '0.5rem', fontFamily: 'monospace' }}>{item.index}</td>
                  <td style={{ padding: '0.5rem', fontFamily: 'monospace', color: '#22d3ee' }}>{item.variable}</td>
                  <td style={{ padding: '0.5rem' }}>{item.trip_id}</td>
                  <td style={{ padding: '0.5rem' }}>{item.bus_id}</td>
                  <td style={{ padding: '0.5rem', fontFamily: 'monospace' }}>{item.utility.toFixed(4)}</td>
                  <td style={{ padding: '0.5rem', fontFamily: 'monospace', color: item.linear_coeff < 0 ? '#34d399' : '#fb7185' }}>
                    {item.linear_coeff.toFixed(4)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
            <thead>
              <tr style={{ color: 'var(--text-muted)', borderBottom: '1px solid var(--border-color)' }}>
                <th style={{ padding: '0.5rem' }}>Variable 1</th>
                <th style={{ padding: '0.5rem' }}>Variable 2</th>
                <th style={{ padding: '0.5rem' }}>Penalty Type</th>
                <th style={{ padding: '0.5rem' }}>Q_kl Value</th>
                <th style={{ padding: '0.5rem' }}>Constraint Reason</th>
              </tr>
            </thead>
            <tbody>
              {summary.quadratic_terms_preview.map((item, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                  <td style={{ padding: '0.5rem', fontFamily: 'monospace', color: '#22d3ee' }}>{item.var1}</td>
                  <td style={{ padding: '0.5rem', fontFamily: 'monospace', color: '#22d3ee' }}>{item.var2}</td>
                  <td style={{ padding: '0.5rem' }}>
                    <span className={`badge ${item.type === 'DUPLICATE_TRIP_PENALTY' ? 'badge-warning' : 'badge-danger'}`}>
                      {item.type === 'DUPLICATE_TRIP_PENALTY' ? 'Duplicate' : 'Overlap'}
                    </span>
                  </td>
                  <td style={{ padding: '0.5rem', fontFamily: 'monospace', color: '#fbbf24' }}>+{item.penalty.toFixed(1)}</td>
                  <td style={{ padding: '0.5rem', color: 'var(--text-secondary)' }}>{item.explanation}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

