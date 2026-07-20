import apiClient from './baseAPI';

// MongoDB Backend Orders API
export const orderAPI = {
  // Get all orders
  getOrders: (params = {}) => {
    const { page = 1, limit = 50, status, customerId } = params;
    return apiClient.get('/api/orders', {
      params: {
        page,
        limit,
        ...(status && { status }),
        ...(customerId && { customerId })
      }
    });
  },
  
  // Get single order
  getOrder: (id) => apiClient.get(`/api/orders/${id}`),
  
  // Create order (customer)
  createOrder: (orderData) => apiClient.post('/api/orders', orderData),
  
  // Dispatch order (admin/manager)
  dispatchOrder: (id) => apiClient.put(`/api/orders/${id}/dispatch`),
  
  // Confirm delivery (customer)
  confirmDelivery: (id) => apiClient.put(`/api/orders/${id}/deliver`),
  
  // Get order statistics
  getStats: () => apiClient.get('/api/orders/stats/summary')
};

export default orderAPI;
