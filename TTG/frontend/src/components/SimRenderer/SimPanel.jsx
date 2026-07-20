import { useState, useCallback } from 'react';
import useSimRenderer from './useSimRenderer';

/**
 * SimPanel
 *
 * Dashboard panel for the BHIV simulation engine.
 * Accepts a simResult from the backend (POST /simulate/run)
 * and renders it via CanvasRenderer.
 *
 * Props:
 *   simResult   {Object|null}  - Output of SimEngine.run()
 *   onRun       {Function}     - Called when user clicks Run — (contract) => void
 *   loading     {boolean}
 *   error       {string|null}
 */
export default function SimPanel({ simResult, onRun, loading = false, error = null }) {
  const [showLog, setShowLog]   = useState(false);
  const [headlessOut, setHeadlessOut] = useState(null);

  const { canvasRef, renderHeadless } = useSimRenderer(simResult, {
    width:       560,
    height:      400,
    interval_ms: 150
  });

  const handleHeadless = useCallback(() => {
    if (!simResult) return;
    const frames = renderHeadless(simResult);
    setHeadlessOut(frames);
  }, [simResult, renderHeadless]);

  return (
    <div className="
      rounded-3xl border
      bg-white/70 border-slate-200
      dark:bg-slate-950/90 dark:border-slate-800
      p-5 flex flex-col gap-4
    ">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-slate-200 flex items-center gap-2">
          <span className="text-cyan-400">⬡</span>
          BHIV Simulation Engine
        </h2>
        {simResult && (
          <span className={`text-xs px-2 py-0.5 rounded-full font-mono ${
            simResult.status === 'completed'
              ? 'bg-emerald-500/20 text-emerald-400'
              : 'bg-red-500/20 text-red-400'
          }`}>
            {simResult.status}
          </span>
        )}
      </div>

      {/* Controls */}
      <div className="flex items-center gap-3 flex-wrap">
        <button
          onClick={() => onRun && onRun()}
          disabled={loading}
          className="px-4 py-1.5 rounded-xl text-xs font-semibold
                     bg-gradient-to-r from-cyan-500 to-indigo-500
                     text-white shadow-md shadow-cyan-500/20
                     disabled:opacity-40 disabled:cursor-not-allowed
                     hover:brightness-110 transition-all"
        >
          {loading ? 'Running…' : '▶ Run Simulation'}
        </button>

        {simResult && (
          <button
            onClick={handleHeadless}
            className="px-4 py-1.5 rounded-xl text-xs font-semibold
                       bg-slate-700 text-slate-300
                       hover:bg-slate-600 transition-all"
          >
            Export Headless
          </button>
        )}

        {simResult && (
          <button
            onClick={() => setShowLog(v => !v)}
            className="px-4 py-1.5 rounded-xl text-xs font-semibold
                       bg-slate-700 text-slate-300
                       hover:bg-slate-600 transition-all"
          >
            {showLog ? 'Hide Log' : 'Event Log'}
          </button>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="text-xs text-red-400 bg-red-500/10 rounded-xl px-3 py-2 font-mono">
          {error}
        </div>
      )}

      {/* Canvas */}
      <div className="relative rounded-2xl overflow-hidden bg-slate-900 border border-slate-800">
        {!simResult && !loading && (
          <div className="absolute inset-0 flex items-center justify-center text-slate-600 text-sm">
            No simulation loaded — click Run
          </div>
        )}
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
          </div>
        )}
        <canvas
          ref={canvasRef}
          width={560}
          height={400}
          className="block w-full"
          style={{ imageRendering: 'pixelated' }}
        />
      </div>

      {/* Stats bar — reads from simulationState.v1 */}
      {simResult && (
        <div className="grid grid-cols-4 gap-2">
          {[
            ['Ticks',       simResult.ticks_run],
            ['Entities',    Object.keys(simResult.entities).length],
            ['Events',      simResult.state_summary?.event_count ?? 0],
            ['Transitions', simResult.transitions.length]
          ].map(([label, val]) => (
            <div key={label} className="rounded-xl bg-slate-800/60 px-3 py-2 text-center">
              <div className="text-lg font-bold text-cyan-400 font-mono">{val}</div>
              <div className="text-[10px] text-slate-500 uppercase tracking-wide">{label}</div>
            </div>
          ))}
        </div>
      )}

      {/* State summary — reads from state_summary, no game_stats */}
      {simResult?.state_summary && (
        <div className="rounded-xl bg-slate-900/80 border border-slate-700 p-3">
          <div className="text-[10px] text-slate-500 uppercase tracking-widest mb-2">State Summary</div>
          <div className="grid grid-cols-3 gap-2">
            {[
              ['Active',    simResult.state_summary.active_count,    'text-cyan-400'],
              ['Flagged',   simResult.state_summary.flagged_count,   simResult.state_summary.flagged_count > 0 ? 'text-orange-400' : 'text-slate-400'],
              ['Collisions',simResult.state_summary.collision_count, simResult.state_summary.collision_count > 0 ? 'text-red-400' : 'text-slate-400']
            ].map(([label, val, color]) => (
              <div key={label} className="rounded-lg bg-slate-800/60 px-2 py-2 text-center">
                <div className={`text-lg font-bold font-mono ${color}`}>{val}</div>
                <div className="text-[10px] text-slate-500 uppercase">{label}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Entity state table — reads from state_summary for flags/blocked */}
      {simResult && (
        <div className="rounded-xl bg-slate-900/60 border border-slate-800 overflow-hidden">
          <div className="text-[10px] text-slate-500 uppercase tracking-widest px-3 py-2 border-b border-slate-800">
            Entity States
          </div>
          <div className="divide-y divide-slate-800/50 max-h-40 overflow-y-auto">
            {Object.entries(simResult.entities).map(([id, e]) => (
              <div key={id} className="flex items-center justify-between px-3 py-1.5 text-xs">
                <span className="font-mono text-slate-300 truncate max-w-[140px]">{id}</span>
                <span className="text-slate-500 font-mono">{e.type}</span>
                <StateChip state={e.state} />
                <span className="text-slate-600 font-mono text-[10px]">
                  [{e.position.map(v => v.toFixed(1)).join(', ')}]
                </span>
                {simResult.state_summary?.flagged_entities?.[id]  && <span className="text-orange-400 text-[10px]">⚑ flagged</span>}
                {simResult.state_summary?.blocked_entities?.[id]  && <span className="text-red-400 text-[10px]">✕ blocked</span>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Event log — reads event_count from state_summary */}
      {showLog && simResult && (
        <div className="rounded-xl bg-slate-900/60 border border-slate-800 overflow-hidden">
          <div className="text-[10px] text-slate-500 uppercase tracking-widest px-3 py-2 border-b border-slate-800">
            Event Log ({simResult.state_summary?.event_count ?? simResult.event_log.length})
          </div>
          <div className="max-h-48 overflow-y-auto divide-y divide-slate-800/30">
            {simResult.event_log.slice(-40).map((evt, i) => (
              <div key={i} className="flex items-center gap-2 px-3 py-1 text-[10px] font-mono">
                <span className="text-slate-600 w-6 text-right">{evt.tick ?? '—'}</span>
                <SourceChip source={evt.source} />
                <span className="text-slate-300 truncate">{evt.type}</span>
                {evt.entity_id && (
                  <span className="text-slate-500 truncate">{evt.entity_id}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Headless output */}
      {headlessOut && (
        <div className="rounded-xl bg-slate-900/60 border border-slate-800 overflow-hidden">
          <div className="flex items-center justify-between px-3 py-2 border-b border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase tracking-widest">
              Headless Frames ({headlessOut.length})
            </span>
            <button
              onClick={() => setHeadlessOut(null)}
              className="text-slate-600 hover:text-slate-400 text-xs"
            >✕</button>
          </div>
          <pre className="text-[9px] text-slate-400 font-mono p-3 max-h-40 overflow-auto">
            {JSON.stringify(headlessOut[0], null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function StateChip({ state }) {
  const colors = {
    active:    'bg-cyan-500/20 text-cyan-400',
    idle:      'bg-violet-500/20 text-violet-400',
    stopped:   'bg-amber-500/20 text-amber-400',
    destroyed: 'bg-red-500/20 text-red-400'
  };
  return (
    <span className={`px-1.5 py-0.5 rounded-full text-[9px] font-semibold ${colors[state] || 'bg-slate-700 text-slate-400'}`}>
      {state}
    </span>
  );
}

function SourceChip({ source }) {
  const colors = {
    behavior:   'text-cyan-500',
    rule:       'text-violet-400',
    transition: 'text-amber-400',
    collision:  'text-red-400',
    zone:       'text-yellow-400',
    engine:     'text-slate-500'
  };
  return (
    <span className={`w-16 truncate ${colors[source] || 'text-slate-500'}`}>
      {source}
    </span>
  );
}
