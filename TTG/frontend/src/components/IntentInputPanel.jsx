/**
 * TextToGamePanel - Intent Compiler Dashboard Integration
 * Day 2a: Dashboard Wiring - Enhanced UI
 */

import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { speak, enableTTS, isTTSEnabled } from '../utils/tts';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:3000';

export default function TextToGamePanel({ socket, engineStatus, userId, onSimulate }) {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [compiledSchema, setCompiledSchema] = useState(null);
  const [intent, setIntent] = useState(null);
  const [error, setError] = useState(null);
  const [showJson, setShowJson] = useState(false);
  const [validationStatus, setValidationStatus] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const [lastCompileTime, setLastCompileTime] = useState(0);
  const [executionId, setExecutionId] = useState(null);
  const [executionStatus, setExecutionStatus] = useState(null);
  const [simLoading, setSimLoading] = useState(false);
  const [atharvaStatus, setAtharvaStatus] = useState(null);
  const [atharvaLoading, setAtharvaLoading] = useState(false);

  const navigate = useNavigate();

  const MAX_TEXT_LENGTH = 500;
  const COMPILE_COOLDOWN = 1000; // 1 second

  const isEngineHealthy = engineStatus?.connected && engineStatus?.healthy;
  const prevEngineHealthy = useRef(null);

  useEffect(() => {
    if (prevEngineHealthy.current !== null && prevEngineHealthy.current !== isEngineHealthy) {
      if (isEngineHealthy) {
        speak('Engine connected');
      } else {
        speak('Engine disconnected');
      }
    }
    prevEngineHealthy.current = isEngineHealthy;
  }, [isEngineHealthy]);

  useEffect(() => {
    if (!socket) return;

    const handleJobStatus = (data) => {
      setJobStatus(data);
      if (data.status === 'completed') {
        setTimeout(() => setJobStatus(null), 3000);
      }
    };

    const handleExecutionStarted = (data) => {
      setExecutionStatus({ status: 'running', ...data });
    };

    const handleExecutionCompleted = (data) => {
      setExecutionStatus({ status: 'completed', ...data });
      speak('Execution completed');
      setTimeout(() => setExecutionStatus(null), 5000);
    };

    const handleExecutionFailed = (data) => {
      setExecutionStatus({ status: 'failed', ...data });
      setTimeout(() => setExecutionStatus(null), 5000);
    };

    socket.on('job_status', handleJobStatus);
    socket.on('execution:started', handleExecutionStarted);
    socket.on('execution:completed', handleExecutionCompleted);
    socket.on('execution:failed', handleExecutionFailed);
    
    return () => {
      socket.off('job_status', handleJobStatus);
      socket.off('execution:started', handleExecutionStarted);
      socket.off('execution:completed', handleExecutionCompleted);
      socket.off('execution:failed', handleExecutionFailed);
    };
  }, [socket]);

  const handleCompile = async () => {
    if (!text.trim()) { setError('Please enter a game description'); return; }
    if (text.length > MAX_TEXT_LENGTH) { setError(`Text too long (max ${MAX_TEXT_LENGTH} characters)`); return; }
    const now = Date.now();
    if (now - lastCompileTime < COMPILE_COOLDOWN) { setError('Please wait before compiling again'); return; }
    setLastCompileTime(now);

    setLoading(true);
    setError(null);
    setCompiledSchema(null);
    setIntent(null);
    setExecutionStatus(null);

    try {
      // Try prompt runner first
      const healthRes = await fetch(`${BACKEND_URL}/core/prompt-runner-health`).catch(() => null);
      const health = healthRes ? await healthRes.json().catch(() => null) : null;

      if (health?.healthy) {
        // Use Groq AI via prompt runner — only generate schema, don't dispatch yet
        const res = await fetch(`${BACKEND_URL}/core/prompt-runner-compile`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt: text })
        });
        const data = await res.json();
        if (data.success) {
          const s = data.executionSchema;
          setCompiledSchema({ ...s, _source: 'prompt_runner' });
          setIntent({
            genre: s?.game_mode || 'ai',
            pacing: (s?.spawn_rules?.frequency || 2) <= 1.5 ? 'fast' : 'normal',
            difficulty: (s?.player_params?.health || 3) <= 3 ? 'hard' : 'easy',
            abilities: Array.isArray(s?.tasks) ? s.tasks : [],
            obstacles: (s?.spawn_rules?.obstacles || 0) > 0,
            pickups: Array.isArray(s?.tasks) && s.tasks.includes('pickup_system')
          });
          setShowJson(false);
          setValidationStatus({ valid: true, message: 'AI compiled via Groq — click Execute to send to engine' });
          speak('Schema ready');
        } else {
          throw new Error(data.error || 'Prompt runner failed');
        }
      } else {
        // Fallback: local intent compiler
        const res = await fetch(`${BACKEND_URL}/api/intent/compile`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text })
        });
        const data = await res.json();
        if (data.success) {
          setCompiledSchema(data.schema);
          setIntent(data.intent);
          setShowJson(false);
          setValidationStatus({ valid: true, message: 'Contract validated successfully' });
          speak(`${data.intent.genre} game ready`);
        } else {
          setError(data.explanation || data.error || 'Compilation failed');
          setValidationStatus(null);
        }
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSendToEngine = async () => {
    if (!compiledSchema) return;
    setLoading(true);
    setError(null);
    setExecutionStatus(null);

    try {
      let data;

      if (compiledSchema._source === 'prompt_runner') {
        // Prompt runner schema — send via execute-from-text (no HMAC needed)
        const res = await fetch(`${BACKEND_URL}/core/execute-from-text`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt: text, user_id: userId || 'frontend_user' })
        });
        data = await res.json();
      } else {
        // Local compiled schema — send with HMAC signature
        const execution_id = `exec_${Date.now()}`;
        const trace_id = `trace_${Date.now()}`;
        const timestamp = Date.now();
        const nonce = Math.random().toString(36).substring(2, 18);
        const crypto = await import('crypto-js');
        const message = `${execution_id}|${trace_id}|${JSON.stringify(compiledSchema)}|${timestamp}|${nonce}`;
        const signature = crypto.default.HmacSHA256(message, 'HMAC_SECRET_987654321').toString();
        const res = await fetch(`${BACKEND_URL}/core/execute`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ execution_id, trace_id, executionSchema: compiledSchema, user_id: userId || 'frontend_user', timestamp, nonce, signature, intent: { prompt: text } })
        });
        data = await res.json();
      }

      if (data.success) {
        setExecutionId(data.execution_id);
        setExecutionStatus({ status: 'dispatched', execution_id: data.execution_id });
        speak('Execution dispatched');
        // Auto-open renderer after dispatch
        setTimeout(() => {
          window.open('https://ttg-renderer.onrender.com', '_blank');
        }, 2000);
      } else {
        setError(data.error || 'Execution failed');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLaunchAtharva = async () => {
    if (!compiledSchema) return;
    setAtharvaLoading(true);
    setAtharvaStatus(null);
    try {
      const res = await fetch(`${BACKEND_URL}/core/execute-to-atharva`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ schema: compiledSchema })
      });
      const data = await res.json();
      if (data.success) {
        setAtharvaStatus({ ok: true, message: `🎮 Game launched! Mode: ${data.game_mode} | trace: ${data.trace_id}`, mitra_decision: data.mitra_decision, mitra_trace: data.mitra_trace });
        speak('Game launched on Atharva');
      } else {
        setAtharvaStatus({ ok: false, message: data.error });
      }
    } catch (err) {
      setAtharvaStatus({ ok: false, message: err.message });
    } finally {
      setAtharvaLoading(false);
    }
  };

  const handleSimulate = async () => {
    if (!compiledSchema) return;
    setSimLoading(true);
    setError(null);

    try {
      const res = await fetch(`${BACKEND_URL}/simulate/from-schema`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ schema: compiledSchema, ticks: 20 })
      });
      const data = await res.json();
      if (!data.success) throw new Error(data.error || 'Simulation failed');

      // Open as modal over dashboard instead of navigating away
      if (onSimulate) {
        onSimulate(data.result, text, compiledSchema);
      }
    } catch (err) {
      setError(`Simulate failed: ${err.message}`);
    } finally {
      setSimLoading(false);
    }
  };

  const examplePrompts = [
    { text: "Make a fast runner with jump and obstacles"},
    { text: "Create an easy platform jump game" }
  ];

  return (
    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-50 via-purple-50/30 to-slate-50 dark:from-slate-900 dark:via-purple-900/20 dark:to-slate-900 border-2 border-purple-500/30 shadow-2xl max-h-[800px] overflow-y-auto">
      {/* Animated background */}
      <div className="absolute inset-0 -z-10 overflow-hidden">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
        <div className="absolute top-1/2 left-1/2 w-96 h-96 bg-pink-500/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '2s' }} />
      </div>

      <div className="relative p-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-3 mb-3">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-2xl shadow-lg">
              🎮
            </div>
            <h2 className="text-4xl font-black bg-gradient-to-r from-purple-400 via-pink-400 to-blue-400 bg-clip-text text-transparent drop-shadow-lg">
              Intent Compiler
            </h2>
          </div>
          <p className="text-slate-600 dark:text-slate-400 text-sm">Transform your ideas into playable games</p>
        </div>

        {/* Engine Status */}
        <div className="flex justify-center mb-6 gap-3">
          <button
            onClick={() => { enableTTS(); setVoiceEnabled(true); }}
            disabled={voiceEnabled}
            className={`px-4 py-2 rounded-full text-sm font-semibold transition-all ${
              voiceEnabled 
                ? 'bg-green-500/20 text-green-300 border-2 border-green-500/50 cursor-not-allowed'
                : 'bg-blue-500/20 text-blue-300 border-2 border-blue-500/50 hover:bg-blue-500/30'
            }`}
          >
            {voiceEnabled ? '🔊 Voice On' : '🔇 Enable Voice'}
          </button>
          
          <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold backdrop-blur-sm transition-all ${
            isEngineHealthy
              ? 'bg-green-500/20 text-green-300 border-2 border-green-500/50 shadow-lg shadow-green-500/20' 
              : 'bg-amber-500/20 text-amber-300 border-2 border-amber-500/50 shadow-lg shadow-amber-500/20'
          }`}>
            <span className={`relative flex h-3 w-3`}>
              <span className={`absolute inline-flex h-full w-full rounded-full opacity-75 ${
                isEngineHealthy ? 'bg-green-400 animate-ping' : 'bg-amber-400 animate-ping'
              }`} />
              <span className={`relative inline-flex rounded-full h-3 w-3 ${
                isEngineHealthy ? 'bg-green-500' : 'bg-amber-500'
              }`} />
            </span>
            {isEngineHealthy ? 'Engine Online' : 'Engine Offline'}
          </div>
        </div>

        {/* Text Input */}
        <div className="mb-6">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder={`✨ Describe your game...

Example: 'Make a fast runner with jump and obstacles'

Supported features:
• Genres: runner, platformer, arena
• Abilities: jump, dash, lane_switch
• Entities: obstacles, pickups`}
            rows={3}
            className="w-full px-4 py-3 rounded-xl bg-white/80 dark:bg-slate-800/50 backdrop-blur-sm border-2 border-purple-500/30 text-slate-900 dark:text-slate-100 placeholder-slate-500 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 transition-all resize-none text-sm shadow-lg disabled:opacity-50"
            disabled={loading}
          />
          <div className={`text-xs text-right mt-1 ${
            text.length > MAX_TEXT_LENGTH ? 'text-red-500 font-bold' : 'text-slate-500'
          }`}>
            {text.length}/{MAX_TEXT_LENGTH}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4 mb-6">
          <button
            onClick={handleCompile}
            disabled={loading || !text.trim()}
            className="flex-1 group relative px-8 py-4 rounded-xl font-bold text-white text-lg overflow-hidden transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105 active:scale-95"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-purple-600 via-pink-600 to-blue-600 transition-all group-hover:scale-110" />
            <div className="absolute inset-0 bg-gradient-to-r from-purple-600 via-pink-600 to-blue-600 opacity-0 group-hover:opacity-100 blur-xl transition-all" />
            <span className="relative flex items-center justify-center gap-2">
              {loading ? (
                <><span className="animate-spin">⚙️</span>Compiling...</>
              ) : (
                <><span>🛠️</span>Compile Schema</>
              )}
            </span>
          </button>

          {compiledSchema && (
            <button
              onClick={handleSendToEngine}
              disabled={loading}
              className="flex-1 group relative px-8 py-4 rounded-xl font-bold text-white text-lg overflow-hidden transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105 active:scale-95"
            >
              <div className="absolute inset-0 bg-gradient-to-r from-green-600 via-emerald-600 to-teal-600 transition-all group-hover:scale-110" />
              <div className="absolute inset-0 bg-gradient-to-r from-green-600 via-emerald-600 to-teal-600 opacity-0 group-hover:opacity-100 blur-xl transition-all" />
              <span className="relative flex items-center justify-center gap-2">
                <span>🚀</span>Execute
              </span>
            </button>
          )}

        </div>

        {/* Example Prompts */}
        <div className="mb-6">
          <p className="text-xs text-slate-600 dark:text-slate-400 font-semibold mb-3 text-center">💡 Quick Examples:</p>
          <div className="grid grid-cols-2 gap-3">
            {examplePrompts.map((prompt, index) => (
              <button
                key={index}
                onClick={() => setText(prompt.text)}
                className="group px-4 py-3 bg-white/80 dark:bg-slate-800/50 backdrop-blur-sm border-2 border-slate-300 dark:border-slate-700 rounded-xl text-slate-700 dark:text-slate-300 text-sm hover:bg-purple-100 dark:hover:bg-purple-900/30 hover:border-purple-500 transition-all disabled:opacity-50 hover:scale-105 active:scale-95 shadow-lg"
                disabled={loading}
              >
                <span className="text-xl mr-2">{prompt.icon}</span>
                <span className="group-hover:text-purple-600 dark:group-hover:text-purple-300 transition-colors">{prompt.text}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Execution Status */}
        {executionStatus && (
          <div className={`mb-6 p-4 backdrop-blur-sm border-2 rounded-xl text-sm shadow-xl animate-fadeIn ${
            executionStatus.status === 'completed'
              ? 'bg-green-50 dark:bg-green-500/10 border-green-500 text-green-700 dark:text-green-400'
              : executionStatus.status === 'failed'
              ? 'bg-red-50 dark:bg-red-500/10 border-red-500 text-red-700 dark:text-red-400'
              : 'bg-blue-50 dark:bg-blue-500/10 border-blue-500 text-blue-700 dark:text-blue-400'
          }`}>
            <div className="flex items-start gap-3">
              <span className="text-2xl">
                {executionStatus.status === 'completed' ? '✅' : executionStatus.status === 'failed' ? '❌' : '🚀'}
              </span>
              <div className="flex-1">
                <strong className="block mb-1">Execution {executionStatus.status}</strong>
                {executionStatus.execution_id && (
                  <p className="text-xs font-mono">{executionStatus.execution_id}</p>
                )}
                {executionStatus.duration && (
                  <p className="text-xs mt-1">Duration: {executionStatus.duration}ms</p>
                )}
                {executionStatus.error && (
                  <p className="text-xs mt-1">Error: {executionStatus.error}</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Atharva Launch Status */}
        {atharvaStatus && (
          <div className={`mb-6 p-4 backdrop-blur-sm border-2 rounded-xl text-sm shadow-xl ${
            atharvaStatus.ok
              ? 'bg-orange-50 dark:bg-orange-500/10 border-orange-500 text-orange-700 dark:text-orange-300'
              : 'bg-red-50 dark:bg-red-500/10 border-red-500 text-red-700 dark:text-red-400'
          }`}>
            <div className="flex items-start gap-3">
              <span className="text-2xl">{atharvaStatus.ok ? '🎮' : '❌'}</span>
              <div>
                <strong className="block mb-1">{atharvaStatus.ok ? 'Atharva Renderer' : 'Atharva Error'}</strong>
                <p className="text-xs font-mono">{atharvaStatus.message}</p>
                {atharvaStatus.ok && (
                  <>
                    <p className="text-xs mt-1 font-mono">Mitra: {atharvaStatus.mitra_decision} {atharvaStatus.mitra_trace ? `| trace: ${atharvaStatus.mitra_trace}` : ''}</p>
                    <p className="text-xs mt-1 opacity-70">Check Atharva’s browser window — game should be running</p>
                  </>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-500/10 backdrop-blur-sm border-2 border-red-500 rounded-xl text-red-700 dark:text-red-400 text-sm shadow-xl animate-shake">
            <div className="flex items-start gap-3">
              <span className="text-2xl">⚠️</span>
              <div>
                <strong className="block mb-1">Error:</strong>
                {error}
              </div>
            </div>
          </div>
        )}

        {/* Validation Status */}
        {validationStatus && (
          <div className={`mb-6 p-4 backdrop-blur-sm border-2 rounded-xl text-sm shadow-xl animate-fadeIn ${
            validationStatus.valid
              ? 'bg-green-50 dark:bg-green-500/10 border-green-500 text-green-700 dark:text-green-400'
              : 'bg-red-50 dark:bg-red-500/10 border-red-500 text-red-700 dark:text-red-400'
          }`}>
            <div className="flex items-start gap-3">
              <span className="text-2xl">{validationStatus.valid ? '✅' : '❌'}</span>
              <div>
                <strong className="block mb-1">{validationStatus.valid ? 'Validation Passed' : 'Validation Failed'}</strong>
                {validationStatus.message && <p>{validationStatus.message}</p>}
                {validationStatus.errors && (
                  <ul className="list-disc list-inside mt-2">
                    {validationStatus.errors.map((err, i) => <li key={i}>{err}</li>)}
                  </ul>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Job Status */}
        {jobStatus && (
          <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-500/10 backdrop-blur-sm border-2 border-blue-500 rounded-xl text-blue-700 dark:text-blue-400 text-sm shadow-xl animate-fadeIn">
            <div className="flex items-start gap-3">
              <span className="text-2xl">🚀</span>
              <div className="flex-1">
                <strong className="block mb-1">Engine Status</strong>
                <div className="flex items-center gap-2">
                  <span className="capitalize">{jobStatus.status}</span>
                  {jobStatus.jobType && <span className="text-xs">({jobStatus.jobType})</span>}
                </div>
                {jobStatus.message && <p className="text-xs mt-1">{jobStatus.message}</p>}
              </div>
            </div>
          </div>
        )}

        {/* Intent Display */}
        {intent && (
          <div className="mb-6 p-6 bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-500/10 dark:to-purple-500/10 backdrop-blur-sm border-2 border-blue-500/50 rounded-xl shadow-xl animate-fadeIn">
            <div className="flex items-center gap-2 mb-4">
              <span className="text-2xl">🎯</span>
              <h3 className="text-blue-700 dark:text-blue-300 font-bold text-lg">Extracted Intent</h3>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-white/80 dark:bg-slate-800/50 rounded-lg p-3">
                <div className="text-xs text-slate-600 dark:text-slate-500 mb-1">Genre</div>
                <div className="text-blue-700 dark:text-blue-300 font-bold">{intent.genre || 'default'}</div>
              </div>
              <div className="bg-white/80 dark:bg-slate-800/50 rounded-lg p-3">
                <div className="text-xs text-slate-600 dark:text-slate-500 mb-1">Pacing</div>
                <div className="text-blue-700 dark:text-blue-300 font-bold">{intent.pacing || 'default'}</div>
              </div>
              <div className="bg-white/80 dark:bg-slate-800/50 rounded-lg p-3">
                <div className="text-xs text-slate-600 dark:text-slate-500 mb-1">Difficulty</div>
                <div className="text-blue-700 dark:text-blue-300 font-bold">{intent.difficulty || 'default'}</div>
              </div>
              <div className="bg-white/80 dark:bg-slate-800/50 rounded-lg p-3">
                <div className="text-xs text-slate-600 dark:text-slate-500 mb-1">Abilities</div>
                <div className="text-blue-700 dark:text-blue-300 font-bold">{intent.abilities.join(', ') || 'none'}</div>
              </div>
              <div className="bg-white/80 dark:bg-slate-800/50 rounded-lg p-3">
                <div className="text-xs text-slate-600 dark:text-slate-500 mb-1">Obstacles</div>
                <div className="text-blue-700 dark:text-blue-300 font-bold">{intent.obstacles ? '✅ yes' : '❌ no'}</div>
              </div>
              <div className="bg-white/80 dark:bg-slate-800/50 rounded-lg p-3">
                <div className="text-xs text-slate-600 dark:text-slate-500 mb-1">Pickups</div>
                <div className="text-blue-700 dark:text-blue-300 font-bold">{intent.pickups ? '✅ yes' : '❌ no'}</div>
              </div>
            </div>
          </div>
        )}

        {/* JSON Preview */}
        {compiledSchema && (
          <div className="p-6 bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-500/10 dark:to-emerald-500/10 backdrop-blur-sm border-2 border-green-500/50 rounded-xl shadow-xl animate-fadeIn">
            <div className="flex justify-between items-center mb-4">
              <div className="flex items-center gap-2">
                <span className="text-2xl">✅</span>
                <h3 className="text-green-700 dark:text-green-300 font-bold text-lg">Compiled Schema</h3>
              </div>
              <button
                onClick={() => setShowJson(!showJson)}
                className="px-4 py-2 bg-white/80 dark:bg-slate-800/50 backdrop-blur-sm rounded-lg text-sm font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 hover:text-slate-900 dark:hover:text-white transition-all border border-slate-300 dark:border-slate-600 hover:border-green-500"
              >
                {showJson ? ' Hide JSON' : ' Show JSON'}
              </button>
            </div>
            
            {/* Summary */}
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div className="bg-white/80 dark:bg-slate-800/50 rounded-lg p-3 text-center">
                <div className="text-2xl mb-1">🎮</div>
                <div className="text-xs text-slate-600 dark:text-slate-500">Game Mode</div>
                <div className="text-green-700 dark:text-green-300 font-bold text-sm">{compiledSchema.game_mode}</div>
              </div>
              <div className="bg-white/80 dark:bg-slate-800/50 rounded-lg p-3 text-center">
                <div className="text-2xl mb-1">⚡</div>
                <div className="text-xs text-slate-600 dark:text-slate-500">Speed</div>
                <div className="text-green-700 dark:text-green-300 font-bold text-sm">{compiledSchema.movement.speed}</div>
              </div>
              <div className="bg-white/80 dark:bg-slate-800/50 rounded-lg p-3 text-center">
                <div className="text-2xl mb-1">📦</div>
                <div className="text-xs text-slate-600 dark:text-slate-500">Obstacles</div>
                <div className="text-green-700 dark:text-green-300 font-bold text-sm">{compiledSchema.spawn_rules.obstacles}</div>
              </div>
            </div>
            
            {showJson && (
              <pre className="p-4 bg-white/90 dark:bg-slate-900/80 backdrop-blur-sm border border-green-500/30 rounded-lg text-slate-800 dark:text-green-300 text-xs overflow-auto max-h-96 shadow-inner font-mono">
                {JSON.stringify(compiledSchema, null, 2)}
              </pre>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
