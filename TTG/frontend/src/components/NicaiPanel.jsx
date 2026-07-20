import { useState, useEffect } from 'react';
import socket from '../socket/socket';

export default function NicaiPanel() {
  const [data, setData] = useState(null);
  const [traceId, setTraceId] = useState(null);

  useEffect(() => {
    socket.on('sim_result', (payload) => {
      if (payload?.nicai?.intelligence) {
        setData(payload.nicai.intelligence);
        setTraceId(payload.trace_id);
      }
    });
    return () => socket.off('sim_result');
  }, []);

  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-950/90 p-5 flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-slate-200 flex items-center gap-2">
          <span className="text-violet-400">◈</span> NICAI Intelligence
        </h2>
        {traceId && (
          <span className="text-[10px] font-mono text-slate-600 truncate max-w-[160px]">
            {traceId}
          </span>
        )}
      </div>

      {!data ? (
        <div className="flex items-center justify-center py-8 text-slate-600 text-sm">
          Waiting for simulation output…
        </div>
      ) : (
        <>
          {/* Simulation Summary */}
          <div className="grid grid-cols-3 gap-2">
            {[
              ['Ticks',       data.simulation_summary.ticks_run,        'text-cyan-400'],
              ['Events',      data.simulation_summary.event_count,      'text-violet-400'],
              ['Transitions', data.simulation_summary.transition_count, 'text-amber-400'],
              ['Entities',    data.simulation_summary.entity_count,     'text-green-400'],
              ['Collisions',  data.simulation_summary.collision_count,  'text-red-400'],
              ['Zone Entries',data.simulation_summary.zone_entries,     'text-yellow-400'],
            ].map(([label, val, color]) => (
              <div key={label} className="rounded-xl bg-slate-900/60 px-3 py-2 text-center">
                <div className={`text-lg font-bold font-mono ${color}`}>{val}</div>
                <div className="text-[10px] text-slate-500 uppercase tracking-wide">{label}</div>
              </div>
            ))}
          </div>

          {/* Entity Profiles */}
          <div className="rounded-xl bg-slate-900/60 border border-slate-800 overflow-hidden">
            <div className="text-[10px] text-slate-500 uppercase tracking-widest px-3 py-2 border-b border-slate-800">
              Entity Profiles
            </div>
            <div className="divide-y divide-slate-800/50 max-h-40 overflow-y-auto">
              {Object.entries(data.entity_profiles).map(([id, p]) => (
                <div key={id} className="flex items-center justify-between px-3 py-1.5 text-xs">
                  <span className="font-mono text-slate-300 truncate max-w-[100px]">{id}</span>
                  <span className="text-slate-500">{p.type}</span>
                  <span className={`font-mono text-[10px] ${
                    p.final_state === 'active' ? 'text-cyan-400' :
                    p.final_state === 'idle'   ? 'text-violet-400' :
                    p.final_state === 'stopped'? 'text-amber-400' : 'text-red-400'
                  }`}>{p.final_state}</span>
                  <span className="text-slate-600 font-mono text-[10px]">dist:{p.total_distance}</span>
                  {p.is_flagged  && <span className="text-orange-400 text-[10px]">⚑</span>}
                  {p.is_blocked  && <span className="text-red-400 text-[10px]">✕</span>}
                </div>
              ))}
            </div>
          </div>

          {/* Patterns */}
          {data.patterns.length > 0 && (
            <div className="rounded-xl bg-slate-900/60 border border-slate-800 overflow-hidden">
              <div className="text-[10px] text-slate-500 uppercase tracking-widest px-3 py-2 border-b border-slate-800">
                Detected Patterns
              </div>
              <div className="divide-y divide-slate-800/50">
                {data.patterns.map((p, i) => (
                  <div key={i} className="flex items-center justify-between px-3 py-1.5 text-xs">
                    <span className="text-slate-400">{p.pattern_type}</span>
                    <span className="font-mono text-slate-300">{p.event_type || p.entities?.join(', ')}</span>
                    <span className="font-mono text-slate-500">×{p.count}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                      p.significance === 'high'   ? 'bg-red-500/20 text-red-400' :
                      p.significance === 'medium' ? 'bg-amber-500/20 text-amber-400' :
                                                    'bg-slate-700 text-slate-400'
                    }`}>{p.significance}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Anomalies */}
          {data.anomalies.length > 0 && (
            <div className="rounded-xl bg-red-500/10 border border-red-500/30 px-3 py-2">
              <div className="text-[10px] text-red-400 uppercase tracking-widest mb-2">Anomalies</div>
              {data.anomalies.map((a, i) => (
                <div key={i} className="text-xs text-red-300 font-mono">
                  {a.type} — {a.entity_id} — {a.reason}
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
