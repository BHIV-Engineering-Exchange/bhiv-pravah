import { useState } from 'react';
import SimPanel from './SimPanel';

const BACKEND = import.meta.env.VITE_BACKEND_URL || 'http://localhost:3000';

// Default simulationContract.v1 input
const DEFAULT_SCHEMA = {
  trace_id:     'trace-modal-001',
  execution_id: 'exec-modal-001',
  domain:       'general',
  scenario:     'default_patrol',
  entities: [
    { id: 'agent_1', type: 'vessel',   position: [0,0,0],   behaviors: ['b_move'], meta: {} },
    { id: 'zone_a',  type: 'zone',     position: [30,0,0],  behaviors: [],         meta: { radius: 8 } }
  ],
  behaviors: [
    { id: 'b_move', script: 'move_to', params: { target: [30,0,0], speed: 3, threshold: 1 } }
  ],
  rules: [
    { id: 'r_zone', trigger: 'on_zone_enter', condition: { field: 'state', op: 'eq', value: 'active' }, action: { type: 'log', params: { message: 'entity entered zone' } }, enabled: true }
  ],
  constraints: { movement: { speed: 3 }, physics: { gravity: [0,-9.8,0] } },
  ticks: 15
};

export default function SimModal({ simResult: initialResult, fromPrompt, compiledSchema, onClose }) {
  const [simResult,   setSimResult]   = useState(initialResult || null);
  const [loading,     setLoading]     = useState(false);
  const [error,       setError]       = useState(null);
  const [schema,      setSchema]      = useState(
    compiledSchema
      ? JSON.stringify(compiledSchema, null, 2)
      : JSON.stringify(DEFAULT_SCHEMA, null, 2)
  );
  const [parseErr,    setParseErr]    = useState(null);
  const [lastTraceId, setLastTraceId] = useState(initialResult?.trace_id || null);
  const [schemaSource, setSchemaSource] = useState(fromPrompt ? 'prompt' : 'manual');

  async function handleRun() {
    setError(null);
    setParseErr(null);

    let parsed;
    try {
      parsed = JSON.parse(schema);
    } catch (e) {
      setParseErr(`Schema JSON error: ${e.message}`);
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${BACKEND}/simulate/run`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(parsed)
      });
      const data = await res.json();
      if (data.status === 'failed') throw new Error(data.error || 'Simulation failed');
      setSimResult(data);
      setLastTraceId(data.trace_id);
      setSchemaSource('manual');
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative z-10 w-full max-w-[1200px] max-h-[90vh] mx-4 overflow-y-auto
                      rounded-3xl border border-slate-700 bg-slate-950 shadow-2xl shadow-black/50">

        {/* Header */}
        <div className="sticky top-0 z-10 flex items-center justify-between
                        px-6 py-4 border-b border-slate-800 bg-slate-950/95 backdrop-blur-sm">
          <div>
            <h2 className="text-lg font-bold bg-gradient-to-r from-cyan-400 to-indigo-400
                           bg-clip-text text-transparent">
              ⬡ BHIV Simulation Engine
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              {fromPrompt && schemaSource === 'prompt'
                ? `Simulating: "${fromPrompt}"`
                : 'SumScript runtime · Canvas renderer · Headless mode'
              }
            </p>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-slate-800 hover:bg-slate-700
                       text-slate-400 hover:text-white transition-all
                       flex items-center justify-center text-sm"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="p-6 grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* Left — schema editor */}
          <div className="flex flex-col gap-4">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="text-xs text-slate-500 uppercase tracking-widest">
                  {schemaSource === 'prompt' ? '⬡ Prompt-Generated Schema' : 'Execution Schema'}
                </div>
                {lastTraceId && (
                  <span className="text-[10px] font-mono text-slate-600 truncate max-w-[180px]">
                    trace: {lastTraceId}
                  </span>
                )}
              </div>
              {parseErr && (
                <div className="text-xs text-red-400 bg-red-500/10 rounded-xl px-3 py-2 mb-3 font-mono">
                  {parseErr}
                </div>
              )}
              <textarea
                value={schema}
                onChange={e => setSchema(e.target.value)}
                className="w-full h-[420px] bg-slate-950 border border-slate-800 rounded-xl
                           text-xs font-mono text-slate-300 p-3 resize-none
                           focus:outline-none focus:border-cyan-700"
                spellCheck={false}
              />
            </div>

            {/* Legend */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
              <div className="text-[10px] text-slate-500 uppercase tracking-widest mb-3">
                Renderer Legend
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                {[
                  ['●', '#22d3ee', 'active'],
                  ['●', '#a78bfa', 'idle'],
                  ['●', '#f59e0b', 'stopped'],
                  ['●', '#ef4444', 'destroyed'],
                  ['→', '#22d3ee', 'velocity arrow'],
                  ['○', '#fbbf24', 'zone boundary'],
                  ['⚑', '#f97316', 'flagged'],
                  ['✕', '#dc2626', 'blocked'],
                ].map(([icon, color, label]) => (
                  <div key={label} className="flex items-center gap-2">
                    <span style={{ color }} className="font-bold">{icon}</span>
                    <span className="text-slate-400">{label}</span>
                  </div>
                ))}
              </div>
              <div className="mt-3 text-[10px] text-slate-600 border-t border-slate-800 pt-3">
                Shapes: ● vessel · ■ obstacle · ◇ marker · ▲ agent · ○ zone
              </div>
            </div>
          </div>

          {/* Right — SimPanel */}
          <SimPanel
            simResult={simResult}
            onRun={handleRun}
            loading={loading}
            error={error}
          />
        </div>
      </div>
    </div>
  );
}
