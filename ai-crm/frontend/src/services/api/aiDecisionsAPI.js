import apiClient from './baseAPI';

export const aiDecisionsAPI = {
  // Decision Making
  makeDecision: (decisionType, params) => apiClient.post('/api/ai-decisions/make', { 
    decision_type: decisionType, 
    parameters: params 
  }),
  
  // Workflows
  getWorkflows: () => apiClient.get('/api/ai-decisions/workflows'),
  getWorkflow: (id) => apiClient.get(`/api/ai-decisions/workflows/${id}`),
  createWorkflow: (data) => apiClient.post('/api/ai-decisions/workflows', data),
  updateWorkflow: (id, data) => apiClient.put(`/api/ai-decisions/workflows/${id}`, data),
  executeWorkflow: (id, data) => apiClient.post(`/api/ai-decisions/workflows/${id}/execute`, data),
  
  // Analytics
  getDecisionAnalytics: () => apiClient.get('/api/ai-decisions/analytics'),
  getDecisionHistory: (params) => apiClient.get('/api/ai-decisions/history', { params }),
  getDecision: (id) => apiClient.get(`/api/ai-decisions/${id}`),
  
  // Settings
  getSettings: () => apiClient.get('/api/ai-decisions/settings'),
  updateSettings: (data) => apiClient.put('/api/ai-decisions/settings', data),
};

export default aiDecisionsAPI;

