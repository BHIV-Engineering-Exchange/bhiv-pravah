import axios from 'axios';
import { 
  LiveDashboardResponse, 
  AutonomousStatus, 
  Decision, 
  EvidenceBundle, 
  ObservedService, 
  TelemetryEvent,
  ActionScope,
  RuntimeState
} from '../types';

const DECISION_BRAIN_URL = process.env.NEXT_PUBLIC_DECISION_BRAIN_URL || 'http://localhost:8000';
const CONTROL_PLANE_URL = process.env.NEXT_PUBLIC_CONTROL_PLANE_URL || 'http://localhost:7000';
const OBSERVER_URL = process.env.NEXT_PUBLIC_OBSERVER_URL || 'http://localhost:8600';

// Axios clients
export const decisionBrainApi = axios.create({
  baseURL: DECISION_BRAIN_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const controlPlaneApi = axios.create({
  baseURL: CONTROL_PLANE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const observerApi = axios.create({
  baseURL: OBSERVER_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API Functions
export const api = {
  // === DECISION BRAIN ENDPOINTS (Port 8000) ===
  getLiveDashboard: async (): Promise<LiveDashboardResponse> => {
    const res = await decisionBrainApi.get<LiveDashboardResponse>('/live-dashboard');
    return res.data;
  },

  getAutonomousStatus: async (): Promise<AutonomousStatus> => {
    const res = await decisionBrainApi.get<AutonomousStatus>('/autonomous-status');
    return res.data;
  },

  getRecentActivity: async (): Promise<{ items: Decision[] }> => {
    const res = await decisionBrainApi.get<{ items: Decision[] }>('/recent-activity');
    return res.data;
  },

  getDecisionSummary: async (): Promise<{
    total_decisions: number;
    last_action: string;
    success_rate: number;
    demo_frozen: boolean;
    stateless: boolean;
  }> => {
    const res = await decisionBrainApi.get('/decision-summary');
    return res.data;
  },

  getActionScope: async (): Promise<ActionScope> => {
    const res = await decisionBrainApi.get<ActionScope>('/action-scope');
    return res.data;
  },

  getOrchestrationMetrics: async (): Promise<{
    rl_brain: Record<string, any>;
    control_plane: Record<string, any>;
    unified: Record<string, any>;
  }> => {
    const res = await decisionBrainApi.get('/orchestration/metrics');
    return res.data;
  },

  getLineageReplay: async (
    executionId: string, 
    params?: { state?: string; start_ts?: number; end_ts?: number }
  ): Promise<{
    execution_id: string;
    valid: boolean;
    final_state: string | null;
    execution_state_history: string[];
    events: any[];
    execution_hash: string | null;
    runtime_attestation: Record<string, any> | null;
  }> => {
    const res = await decisionBrainApi.get(`/api/lineage/${executionId}`, { params });
    return res.data;
  },

  verifyLineage: async (executionId: string): Promise<{
    execution_id: string;
    valid: boolean;
    hash_chain_valid: boolean;
    fsm_valid: boolean;
    error: string | null;
    runtime_attestation_valid: boolean | null;
    runtime_attestation_error: string | null;
  }> => {
    const res = await decisionBrainApi.get(`/api/lineage/${executionId}/verify`);
    return res.data;
  },

  ingestLink: async (link: string): Promise<{ success: boolean; message?: string; error?: string; ingested_link?: any }> => {
    const res = await decisionBrainApi.post('/ingest-link', { link });
    return res.data;
  },

  removeLink: async (link: string): Promise<{ success: boolean; message?: string; error?: string }> => {
    const res = await decisionBrainApi.post('/remove-link', { link });
    return res.data;
  },

  // === CONTROL PLANE ENDPOINTS (Port 7000) ===
  getAppRegistry: async (): Promise<{ status: string; apps: string[] }> => {
    const res = await controlPlaneApi.get<{ status: string; apps: string[] }>('/api/control-plane/apps');
    return res.data;
  },

  getHealthOverview: async (): Promise<{ status: string; overview: Record<string, any> }> => {
    const res = await controlPlaneApi.get<{ status: string; overview: Record<string, any> }>('/api/control-plane/health');
    return res.data;
  },

  getDecisionHistory: async (appName: string, limit = 50): Promise<{ status: string; app_name: string; timeline: Decision[] }> => {
    const res = await controlPlaneApi.get<{ status: string; app_name: string; timeline: Decision[] }>(
      `/api/control-plane/history/${appName}`,
      { params: { limit } }
    );
    return res.data;
  },

  postOverride: async (payload: {
    app_name: string;
    action: 'freeze' | 'clear_freeze';
    duration?: number;
    reason?: string;
  }): Promise<{ status: string; result: any }> => {
    const res = await controlPlaneApi.post<{ status: string; result: any }>('/api/control-plane/override', payload);
    return res.data;
  },

  getUnifiedRegistryTrace: async (traceId: string): Promise<any> => {
    const res = await controlPlaneApi.get(`/registry/trace/${traceId}`);
    return res.data;
  },

  // === OBSERVER ENDPOINTS (Port 8600) ===
  getObserverStatus: async (): Promise<{
    started_at: string;
    poll_count: number;
    services: Record<string, ObservedService>;
  }> => {
    const res = await observerApi.get('/api/status');
    return res.data;
  },

  getObserverEvents: async (limit = 100): Promise<{
    events: TelemetryEvent[];
    total: number;
  }> => {
    const res = await observerApi.get('/api/events', { params: { limit } });
    return res.data;
  },

  getObserverLineage: async (): Promise<{
    lineages: EvidenceBundle[];
  }> => {
    const res = await observerApi.get('/api/lineage');
    return res.data;
  },
};
