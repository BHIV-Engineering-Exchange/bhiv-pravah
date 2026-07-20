import apiClient from './baseAPI';

export const rlAPI = {
  // Analytics
  getAnalytics: () => apiClient.get('/api/rl/analytics'),
  getAgentRankings: () => apiClient.get('/api/rl/rankings'),
  
  // Agent Recommendations
  getAgentRecommendations: (agentName) => apiClient.get(`/api/rl/agents/${agentName}/recommendations`),
  getAgentPerformance: (agentName) => apiClient.get(`/api/rl/agents/${agentName}/performance`),
  
  // Actions
  recordAction: (data) => apiClient.post('/api/rl/actions', data),
  recordOutcome: (actionId, data) => apiClient.post(`/api/rl/actions/${actionId}/outcome`, data),
  getActions: (params) => apiClient.get('/api/rl/actions', { params }),
  getAction: (id) => apiClient.get(`/api/rl/actions/${id}`),
  
  // Learning Control
  runRLWorkflow: (data) => apiClient.post('/api/rl/workflow', data),
  getLearningProgress: () => apiClient.get('/api/rl/progress'),
  
  // Data Management
  saveLearningData: () => apiClient.post('/api/rl/save'),
  resetLearningData: () => apiClient.post('/api/rl/reset'),
  exportLearningData: () => apiClient.get('/api/rl/export'),
};

export default rlAPI;

