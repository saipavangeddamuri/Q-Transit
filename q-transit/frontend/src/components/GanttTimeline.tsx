import React from 'react';
import { AssignmentItem, BusRecord } from '../types';

interface GanttProps {
  schedule: AssignmentItem[];
  buses: BusRecord[];
  title?: string;
}

export const GanttTimeline: React.FC<GanttProps> = ({ schedule, buses, title = "Visual Bus Schedule Timeline" }) => {
  // Find global min and max start/end times among assigned trips and buses
  const activeAssignments = schedule.filter(item => item.bus_id !== null && item.bus_id !== undefined);

  if (activeAssignments.length === 0) {
    return (
      <div className="card text-center p-6 text-slate-400">
        No trips assigned to display on the timeline.
      </div>
    );
  }

  // Calculate timeline bounds
  const minTime = Math.min(
    ...buses.map(b => b.available_from_min),
    ...activeAssignments.map(a => a.start_min)
  );
  const maxTime = Math.max(
    ...buses.map(b => b.available_to_min),
    ...activeAssignments.map(a => a.end_min)
  );
  const totalDuration = Math.max(maxTime - minTime, 60);

  // Helper to format minutes to HH:MM
  const formatTime = (mins: number) => {
    const h = Math.floor(mins / 60);
    const m = mins % 60;
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
  };

  // Color generator for route IDs
  const getRouteColor = (routeId: string) => {
    const colors: Record<string, { bg: string; border: string; text: string }> = {
      R1: { bg: 'rgba(6, 182, 212, 0.25)', border: '#06b6d4', text: '#22d3ee' },
      R2: { bg: 'rgba(139, 92, 246, 0.25)', border: '#8b5cf6', text: '#c084fc' },
      R3: { bg: 'rgba(245, 158, 11, 0.25)', border: '#f59e0b', text: '#fbbf24' },
      R4: { bg: 'rgba(16, 185, 129, 0.25)', border: '#10b981', text: '#34d399' },
    };
    return colors[routeId] || { bg: 'rgba(59, 130, 246, 0.25)', border: '#3b82f6', text: '#60a5fa' };
  };

  // Generate hour markers
  const startHour = Math.floor(minTime / 60);
  const endHour = Math.ceil(maxTime / 60);
  const timeMarkers = [];
  for (let h = startHour; h <= endHour; h++) {
    const mins = h * 60;
    if (mins >= minTime && mins <= maxTime) {
      timeMarkers.push(mins);
    }
  }

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)' }}>{title}</h3>
        <span className="badge badge-info">{activeAssignments.length} Assigned Trips</span>
      </div>

      <div style={{ overflowX: 'auto', paddingBottom: '1rem' }}>
        <div style={{ minWidth: '700px' }}>
          {/* Timeline Header Time Ticks */}
          <div style={{ display: 'flex', marginLeft: '90px', position: 'relative', height: '24px', borderBottom: '1px solid var(--border-color)', marginBottom: '0.75rem' }}>
            {timeMarkers.map(mins => {
              const leftPercent = ((mins - minTime) / totalDuration) * 100;
              return (
                <div
                  key={mins}
                  style={{
                    position: 'absolute',
                    left: `${leftPercent}%`,
                    transform: 'translateX(-50%)',
                    fontSize: '0.75rem',
                    color: 'var(--text-muted)',
                    fontFamily: 'monospace',
                  }}
                >
                  {formatTime(mins)}
                </div>
              );
            })}
          </div>

          {/* Bus Rows */}
          {buses.map(bus => {
            const busTrips = activeAssignments.filter(a => a.bus_id === bus.bus_id);
            const availLeft = ((bus.available_from_min - minTime) / totalDuration) * 100;
            const availWidth = ((bus.available_to_min - bus.available_from_min) / totalDuration) * 100;

            return (
              <div
                key={bus.bus_id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  marginBottom: '1rem',
                  position: 'relative',
                  height: '48px',
                }}
              >
                {/* Bus Label Column */}
                <div
                  style={{
                    width: '90px',
                    flexShrink: 0,
                    fontWeight: 600,
                    fontSize: '0.85rem',
                    color: 'var(--text-secondary)',
                    display: 'flex',
                    flexDirection: 'column',
                  }}
                >
                  <span>{bus.bus_id}</span>
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Cap: {bus.capacity}</span>
                </div>

                {/* Track Area */}
                <div
                  style={{
                    flexGrow: 1,
                    position: 'relative',
                    height: '100%',
                    background: 'rgba(17, 24, 39, 0.6)',
                    borderRadius: '6px',
                    border: '1px dashed var(--border-color)',
                  }}
                >
                  {/* Availability Window Indicator */}
                  <div
                    style={{
                      position: 'absolute',
                      left: `${availLeft}%`,
                      width: `${availWidth}%`,
                      height: '100%',
                      background: 'rgba(255, 255, 255, 0.02)',
                      borderLeft: '1px solid var(--border-light)',
                      borderRight: '1px solid var(--border-light)',
                      pointerEvents: 'none',
                    }}
                  />

                  {/* Trip Blocks */}
                  {busTrips.map(trip => {
                    const tripLeft = ((trip.start_min - minTime) / totalDuration) * 100;
                    const tripWidth = Math.max(((trip.end_min - trip.start_min) / totalDuration) * 100, 2);
                    const color = getRouteColor(trip.route_id);

                    return (
                      <div
                        key={trip.trip_id}
                        title={`Trip: ${trip.trip_id} (${trip.route_id})\nTime: ${formatTime(trip.start_min)} - ${formatTime(trip.end_min)} (${trip.end_min - trip.start_min} min)\nDemand: ${trip.passenger_demand} pax\nCost: $${trip.operating_cost}`}
                        style={{
                          position: 'absolute',
                          left: `${tripLeft}%`,
                          width: `${tripWidth}%`,
                          top: '4px',
                          bottom: '4px',
                          background: color.bg,
                          border: `1.5px solid ${color.border}`,
                          borderRadius: '6px',
                          padding: '0 6px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          overflow: 'hidden',
                          cursor: 'pointer',
                          transition: 'transform 0.15s, box-shadow 0.15s',
                          zIndex: 10,
                        }}
                      >
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: color.text, whiteSpace: 'nowrap' }}>
                          {trip.trip_id}
                        </span>
                        <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginLeft: '4px', whiteSpace: 'nowrap' }}>
                          {trip.passenger_demand}p
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Legend */}
      <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', borderTop: '1px solid var(--border-color)', paddingTop: '0.75rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ width: '12px', height: '12px', borderRadius: '3px', background: 'rgba(6, 182, 212, 0.25)', border: '1.5px solid #06b6d4' }}></span>
          <span>Route R1</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ width: '12px', height: '12px', borderRadius: '3px', background: 'rgba(139, 92, 246, 0.25)', border: '1.5px solid #8b5cf6' }}></span>
          <span>Route R2</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ width: '12px', height: '12px', borderRadius: '3px', background: 'rgba(245, 158, 11, 0.25)', border: '1.5px solid #f59e0b' }}></span>
          <span>Route R3</span>
        </div>
        <span style={{ marginLeft: 'auto', color: 'var(--text-muted)' }}>* Hover any block to view full trip parameters</span>
      </div>
    </div>
  );
};

