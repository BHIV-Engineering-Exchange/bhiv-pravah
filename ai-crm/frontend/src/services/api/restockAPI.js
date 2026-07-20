import apiClient from './baseAPI';

// MongoDB Backend Restock API
export const restockAPI = {
  // Get all restock requests
  getRestockRequests: (params = {}) => {
    const { page = 1, limit = 50, status } = params;
    return apiClient.get('/api/restock', {
      params: {
        page,
        limit,
        ...(status && { status })
      }
    });
  },
  
  // Resend restock email
  resendEmail: (id) => apiClient.post(`/api/restock/${id}/resend-email`),

  // Run procurement agent (low stock -> restock request + email)
  runProcurementAgent: () => apiClient.post('/api/restock/run-procurement'),
  
  // Mark restock as completed
  completeRestock: (id, data) => apiClient.put(`/api/restock/${id}/complete`, data),
  
  // Get restock statistics
  getStats: () => apiClient.get('/api/restock/stats/summary')
};

export default restockAPI;
