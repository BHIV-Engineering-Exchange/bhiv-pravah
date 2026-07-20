import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import SimPanel from '../components/SimRenderer/SimPanel';

const BACKEND = import.meta.env.VITE_BACKEND_URL || 'http://localhost:3000';

// ─── Default contract sent to the backend ────────────────────────────────────

// Default simulationContract.v1 input
const DEFAULT_SCHEMA = {
  trace_id:     'trace-sim-001',
  execution_id: 'exec-sim-001',
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

export default function SimPage() {
  const navigate  = useNavigate();
  const location  = useLocation();

  // Accept pre-loaded result from IntentInputPanel navigation
  const navState  = location.state || {};

  const [simResult,  setSimResult]  = useState(navState.simResult || null);
  const [loading,    setLoading]    = useState(false);
  const [error,      setError]      = useState(null);
  // If navigated from prompt, show the real compiled schema in the editor
  const [schema,     setSchema]     = useState(
    navState.compiledSchema
      ? JSON.stringify(navState.compiledSchema, null, 2)
      : JSON.stringify(DEFAULT_SCHEMA, null, 2)
  );
  const [parseErr,   setParseErr]   = useState(null);
  const [fromPrompt, setFromPrompt] = useState(navState.fromPrompt || null);
  const [lastTraceId, setLastTraceId] = useState(navState.simResult?.trace_id || null);
  const [schemaSource, setSchemaSource] = useState(navState.fromPrompt ? 'prompt' : 'manual');

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
      // POST simulationContract.v1 directly to /simulate/run
      const res = await fetch(`${BACKEND}/simulate/run`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(parsed)
      });
      const data = await res.json();
      if (data.status === 'failed') throw new Error(data.error || 'Simulation failed');
      setSimResult(data);
      setLastTraceId(data.trace_id);
      setFromPrompt(null);
      setSchemaSource('manual');
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 px-4 py-8">

      {/* Header */}
      <div className="max-w-[1200px] mx-auto mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-indigo-400 bg-clip-text text-transparent">
            BHIV Simulation Engine
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            {fromPrompt
              ? `Simulating: "${fromPrompt}"`
              : 'Phase 3 + 4 — SumScript runtime · Canvas renderer · Headless mode'
            }
          </p>
        </div>
        <div className="flex gap-3">
          {fromPrompt && (
            <button
              onClick={() => { setSimResult(null); setFromPrompt(null); }}
              className="text-xs text-cyan-400 hover:text-cyan-200 transition-colors"
            >
              ✕ Clear prompt result
            </button>
          )}
          <button
            onClick={() => navigate('/')}
            className="text-xs text-slate-400 hover:text-slate-200 transition-colors"
          >
            ← Dashboard
          </button>
        </div>
      </div>

      <div className="max-w-[1200px] mx-auto grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Left — schema editor */}
        <div className="flex flex-col gap-4">
          <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-5">
            <div className="flex items-center justify-between mb-3">
              <div className="text-xs text-slate-500 uppercase tracking-widest">
                {schemaSource === 'prompt' ? '⬡ Prompt-Generated Schema' : 'Execution Schema'}
              </div>
              {lastTraceId && (
                <span className="text-[10px] font-mono text-slate-600 truncate max-w-[200px]">
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
              className="w-full h-[520px] bg-slate-950 border border-slate-800 rounded-xl
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
  );
}
