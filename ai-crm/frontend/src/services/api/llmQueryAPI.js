import apiClient from './baseAPI';

export const llmQueryAPI = {
  // Process natural language query
  processQuery: (query, context = {}) => apiClient.post('/api/llm-query', {
    query,
    context
  }),
  
  // Get query examples
  getExamples: () => apiClient.get('/api/llm-query/examples'),
};

export default llmQueryAPI;

