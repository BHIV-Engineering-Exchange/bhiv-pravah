// src/state/agentsReducer.js
// Inferred FSM reducer for Day-4 (cooldown = 3000ms)
export const COOLDOWN_MS = 3000;

export const initialAgentsState = {
  HintAgent: { state: "Idle", lastMessage: null, reason: null, ts: null, cooldownUntil: 0 },
  NavAgent:  { state: "Idle", lastMessage: null, reason: null, ts: null, cooldownUntil: 0 },
  PredictAgent: { state: "Idle", lastMessage: null, reason: null, ts: null, cooldownUntil: 0 },
  RuleAgent: { state: "Idle", lastMessage: null, reason: null, ts: null, cooldownUntil: 0 },
};

function now() { return Date.now(); }

/**
 * normalize incoming orchestrator payload (your orchestrator returns:
 * { agent, message, reason, userId, timestamp })
 */
function normalizePayload(ev) {
  if (!ev || typeof ev !== "object") return null;
  const agent = ev.agent || ev.agentId || ev.agentName;
  const message = ev.message ?? ev.msg ?? null;
  const reason = ev.reason ?? null;
  const ts = ev.timestamp ?? ev.ts ?? Date.now();
  return { agent, message, reason, ts };
}

/**
 * Given previous agent state and an incoming event, produce new agent state.
 * We infer the FSM:
 * - If event arrives -> Triggered
 * - Immediately after triggered -> set cooldownUntil = now + COOLDOWN_MS
 * - If now < cooldownUntil -> state = Cooldown
 * - If now > cooldownUntil and no recent event -> Idle
 */
export function agentsReducer(state, ev) {
  if (!ev) return state;

  // support calling reducer with { agent, payload, _normalized } too
  if (ev._normalized) {
    return { ...state, [ev.agent]: { ...state[ev.agent], ...ev.payload } };
  }

  const incoming = normalizePayload(ev);
  if (!incoming || !incoming.agent) return state;

  const agentId = incoming.agent;
  const prev = state[agentId] || { state: "Idle", lastMessage: null, reason: null, ts: null, cooldownUntil: 0 };

  const nowTs = now();

  // compute base new object
  const newObj = { ...prev };

  // if incoming event is recent, mark Triggered and set cooldown
  newObj.lastMessage = incoming.message;
  newObj.reason = incoming.reason;
  newObj.ts = incoming.ts;
  newObj.state = "Triggered";
  newObj.cooldownUntil = nowTs + COOLDOWN_MS;

  // also mark other agents as Watching or keep them as-is:
  // (we return update only for the triggered agent; caller keeps previous for others)
  return { ...state, [agentId]: newObj };
}

/**
 * Helper to derive presentational state (for UI) given the current reducer state.
 * Optionally call getPresentationalState(state) to compute AgentPanel display fields.
 */
export function getPresentationalAgent(agentState) {
  const nowTs = now();
  const out = { ...agentState };
  if (!agentState) return { state: "Idle", cooldownPct: 0, lastMessage: null, reason: null, ts: null };

  if (agentState.cooldownUntil && nowTs < agentState.cooldownUntil) {
    out.state = (agentState.state === "Triggered") ? "Triggered" : "Cooldown";
    const remaining = Math.max(0, agentState.cooldownUntil - nowTs);
    out.cooldownPct = Math.min(100, Math.round((remaining / COOLDOWN_MS) * 100));
  } else {
    // cooldown expired
    out.state = "Idle";
    out.cooldownPct = 0;
  }
  return out;
}
