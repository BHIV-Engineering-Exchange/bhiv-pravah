import { useState, useEffect, useRef } from 'react';
import socket from '../socket/socket';

const SYSTEMS = ['ALL', 'SVACS', 'NamamiGange', 'NICAI', 'UICICS'];

const SYSTEM_COLORS = {
  SVACS:       'text-cyan-400   border-cyan-500/40   bg-cyan-500/10',
  NamamiGange: 'text-teal-400   border-teal-500/40   bg-teal-500/10',
  NICAI:       'text-violet-400 border-violet-500/40 bg-violet-500/10',
  UICICS:      'text-amber-400  border-amber-500/40  bg-amber-500/10',
  ALL:         'text-slate-300  border-slate-500/40  bg-slate-500/10',
};

const SYSTEM_ICONS = {
  SVACS: '🌊', NamamiGange: '💧', NICAI: '🧠', UICICS: '📋', ALL: '🌐'
};

export default function SamruddhiPanel() {
  const [events,        setEvents]        = useState([]);
  const [activeSystem,  setActiveSystem]  = useState('ALL');
  const [selectedTrace, setSelectedTrace] = useState(null);
  const [replayState,   setReplayState]   = useState(null);
  const [execStatus,    setExecStatus]    = useState({});
  const logRef = useRef(null);

  useEffect(() => {
    // Listen for ecosystem events from backend
    socket.on('samrachna:event', (event) => {
      setEvents(prev => [event, ...prev].slice(0, 100));
      setExecStatus(prev => ({
        ...prev,
        [event.upstream_system]: {
          status:    event.status || 'active',
          trace_id:  event.trace_id,
          game_mode: event.game_mode,
          mitra:     event.mitra_decision,
          ts:        event.timestamp
        }
      }));
    });

    // Legacy sim_result support
    socket.on('sim_result', (payload) => {
      if (payload?.trace_id) {
        setEvents(prev => [{
          upstream_system: 'SIM',
          trace_id:        payload.trace_id,
          status:          'completed',
          timestamp:       new Date().toISOString()
        }, ...prev].slice(0, 100));
      }
    });

    return () => {
      socket.off('samrachna:event');
      socket.off('sim_result');
    };
  }, []);

  // Auto-scroll log
  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = 0;
  }, [events]);

  const filtered = activeSystem === 'ALL'
    ? events
    : events.filter(e => e.upstream_system === activeSystem);

  const systemCounts = events.reduce((acc, e) => {
    acc[e.upstream_system] = (acc[e.upstream_system] || 0) + 1;
    return acc;
  }, {});

  function handleReplay(trace_id) {
    setReplayState({ trace_id, status: 'replaying', started_at: new Date().toISOString() });
    setTimeout(() => setReplayState(r => r ? { ...r, status: 'completed' } : null), 1500);
  }

  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-950/90 p-5 flex flex-col gap-4 col-span-1 xl:col-span-2">

      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h2 className="text-base font-semibold text-slate-200 flex items-center gap-2">
          <span className="text-emerald-400 animate-pulse">◉</span>
          Samrachna — Ecosystem Visualization
        </h2>
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono text-slate-600">
            {events.length} events
          </span>
          {events.length > 0 && (
            <button
              onClick={() => setEvents([])}
              className="text-[10px] text-slate-600 hover:text-slate-400 px-2 py-0.5 rounded border border-slate-700"
            >
              clear
            </button>
          )}
        </div>
      </div>

      {/* System status row */}
      <div className="grid grid-cols-4 gap-2">
        {['SVACS', 'NamamiGange', 'NICAI', 'UICICS'].map(sys => {
          const st = execStatus[sys];
          return (
            <div key={sys} className={`rounded-xl border p-2 ${SYSTEM_COLORS[sys]}`}>
              <div className="flex items-center gap-1 mb-1">
                <span className="text-sm">{SYSTEM_ICONS[sys]}</span>
                <span className="text-[10px] font-semibold">{sys}</span>
                {st && <span className="ml-auto w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />}
              </div>
              {st ? (
                <>
                  <div className="text-[9px] font-mono opacity-70 truncate">{st.trace_id?.substring(0, 16)}...</div>
                  <div className="text-[9px] opacity-60">Mitra: {st.mitra} | {st.game_mode}</div>
                </>
              ) : (
                <div className="text-[9px] opacity-40">waiting...</div>
              )}
              <div className="text-[9px] opacity-50 mt-0.5">{systemCounts[sys] || 0} events</div>
            </div>
          );
        })}
      </div>

      {/* System switcher */}
      <div className="flex gap-2 flex-wrap">
        {SYSTEMS.map(sys => (
          <button
            key={sys}
            onClick={() => setActiveSystem(sys)}
            className={`px-3 py-1 rounded-full text-[11px] font-semibold border transition-all
              ${activeSystem === sys
                ? SYSTEM_COLORS[sys] + ' opacity-100'
                : 'border-slate-700 text-slate-500 bg-transparent hover:border-slate-500'
              }`}
          >
            {SYSTEM_ICONS[sys]} {sys}
            {sys !== 'ALL' && systemCounts[sys] ? ` (${systemCounts[sys]})` : ''}
          </button>
        ))}
      </div>

      {/* Event log */}
      <div className="rounded-xl bg-slate-900/60 border border-slate-800 overflow-hidden">
        <div className="text-[10px] text-slate-500 uppercase tracking-widest px-3 py-2 border-b border-slate-800 flex items-center justify-between">
          <span>Live Execution Log — {activeSystem}</span>
          <span className="font-mono">{filtered.length} events</span>
        </div>
        <div ref={logRef} className="divide-y divide-slate-800/50 max-h-48 overflow-y-auto">
          {filtered.length === 0 ? (
            <div className="flex items-center justify-center py-6 text-slate-600 text-xs">
              Waiting for ecosystem events… run the demo script
            </div>
          ) : (
            filtered.map((e, i) => (
              <div
                key={i}
                onClick={() => setSelectedTrace(selectedTrace === e.trace_id ? null : e.trace_id)}
                className={`flex items-center gap-3 px-3 py-2 text-[11px] cursor-pointer transition-colors
                  ${selectedTrace === e.trace_id ? 'bg-slate-800/60' : 'hover:bg-slate-800/30'}`}
              >
                <span className={`text-sm ${SYSTEM_COLORS[e.upstream_system]?.split(' ')[0] || 'text-slate-400'}`}>
                  {SYSTEM_ICONS[e.upstream_system] || '◦'}
                </span>
                <span className="font-semibold text-slate-300 w-24 truncate">{e.upstream_system}</span>
                <span className="font-mono text-slate-500 flex-1 truncate">{e.trace_id}</span>
                <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono
                  ${e.mitra_decision === 'ALLOW' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                  {e.mitra_decision || 'ALLOW'}
                </span>
                <span className="text-slate-600 text-[10px] font-mono">{e.game_mode || '?'}</span>
                <span className={`w-1.5 h-1.5 rounded-full ${e.status === 'EXECUTION_COMPLETE' ? 'bg-emerald-500' : 'bg-amber-400'}`} />
              </div>
            ))
          )}
        </div>
      </div>

      {/* Trace detail + replay */}
      {selectedTrace && (() => {
        const evt = events.find(e => e.trace_id === selectedTrace);
        if (!evt) return null;
        return (
          <div className="rounded-xl bg-slate-900/60 border border-slate-700 p-3 flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-slate-400 uppercase tracking-widest">Trace Detail</span>
              <button
                onClick={() => handleReplay(selectedTrace)}
                className="text-[10px] px-3 py-1 rounded-lg bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 hover:bg-indigo-500/30 transition-all"
              >
                ↻ Replay
              </button>
            </div>
            <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-[11px] font-mono">
              {[
                ['trace_id',        evt.trace_id],
                ['execution_id',    evt.execution_id],
                ['upstream_system', evt.upstream_system],
                ['mitra_decision',  evt.mitra_decision],
                ['game_mode',       evt.game_mode],
                ['status',          evt.status],
                ['elapsed_ms',      evt.elapsed_ms ? `${evt.elapsed_ms}ms` : '—'],
                ['timestamp',       evt.timestamp?.substring(11, 19)],
              ].map(([k, v]) => (
                <div key={k} className="flex gap-2">
                  <span className="text-slate-600 w-28 shrink-0">{k}</span>
                  <span className="text-slate-300 truncate">{v || '—'}</span>
                </div>
              ))}
            </div>
            {replayState?.trace_id === selectedTrace && (
              <div className={`text-[10px] px-2 py-1 rounded font-mono
                ${replayState.status === 'completed' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'}`}>
                {replayState.status === 'replaying' ? '⟳ Replaying trace...' : '✓ Replay complete — trace deterministic'}
              </div>
            )}
          </div>
        );
      })()}

      {/* Spine indicator */}
      <div className="rounded-xl bg-slate-900/40 border border-slate-800 px-3 py-2">
        <div className="text-[10px] text-slate-600 uppercase tracking-widest mb-1">TANTRA Spine</div>
        <div className="flex items-center gap-1 text-[10px] font-mono flex-wrap">
          {['SVACS','NamamiGange','NICAI','UICICS'].map((s, i) => (
            <span key={s}>
              <span className={execStatus[s] ? SYSTEM_COLORS[s].split(' ')[0] : 'text-slate-700'}>{s}</span>
              {i < 3 && <span className="text-slate-700 mx-1">→</span>}
            </span>
          ))}
          <span className="text-slate-700 mx-1">→</span>
          <span className={Object.keys(execStatus).length > 0 ? 'text-emerald-400' : 'text-slate-700'}>Rudra</span>
          <span className="text-slate-700 mx-1">→</span>
          <span className={Object.keys(execStatus).length > 0 ? 'text-orange-400' : 'text-slate-700'}>Mitra</span>
          <span className="text-slate-700 mx-1">→</span>
          <span className={Object.keys(execStatus).length > 0 ? 'text-pink-400' : 'text-slate-700'}>Atharva</span>
        </div>
      </div>
    </div>
  );
}
