import apiClient from './baseAPI';

export const agentAPI = {
  // Agents
  getAgents: () => apiClient.get('/api/agents'),
  getAgent: (id) => apiClient.get(`/api/agents/${id}`),
  updateAgentStatus: (id, status) => apiClient.patch(`/api/agents/${id}/status`, { status }),
  updateAgentConfig: (id, config) => apiClient.put(`/api/agents/${id}/config`, config),
  
  // Performance
  getAgentMetrics: (id) => apiClient.get(`/api/agents/${id}/metrics`),
  getPerformanceChart: (id, params) => apiClient.get(`/api/agents/${id}/performance`, { params }),
  getEfficiencyReport: (id) => apiClient.get(`/api/agents/${id}/efficiency`),
  
  // Configuration
  getTriggerRules: (agentId) => apiClient.get(`/api/agents/${agentId}/triggers`),
  updateTriggerRules: (agentId, rules) => apiClient.put(`/api/agents/${agentId}/triggers`, { rules }),
  getConfidenceThresholds: (agentId) => apiClient.get(`/api/agents/${agentId}/thresholds`),
  updateConfidenceThresholds: (agentId, thresholds) => apiClient.put(`/api/agents/${agentId}/thresholds`, thresholds),
  
  // Actions
  triggerAgent: (id, data) => apiClient.post(`/api/agents/${id}/trigger`, data),
  pauseAgent: (id) => apiClient.post(`/api/agents/${id}/pause`),
  resumeAgent: (id) => apiClient.post(`/api/agents/${id}/resume`),
  
  // Dashboard
  getDashboardMetrics: () => apiClient.get('/api/agents/dashboard/metrics'),
  getAgentActivity: (params) => apiClient.get('/api/agents/activity', { params }),
  getAgentLogs: (params) => apiClient.get('/api/agents/logs', { params }),
};

export default agentAPI;
