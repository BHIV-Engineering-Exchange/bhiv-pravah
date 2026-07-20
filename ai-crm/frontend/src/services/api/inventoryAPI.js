import apiClient from './baseAPI';

// MongoDB Backend Inventory API
export const inventoryAPI = {
  // Get inventory logs
  getInventoryLogs: (params = {}) => {
    const { page = 1, limit = 50, productId, changeType } = params;
    return apiClient.get('/api/inventory/logs', {
      params: {
        page,
        limit,
        ...(productId && { productId }),
        ...(changeType && { changeType })
      }
    });
  },
  
  // Adjust inventory manually
  adjustInventory: (data) => apiClient.post('/api/inventory/adjust', data),
  
  // Get low stock products
  getLowStockProducts: () => apiClient.get('/api/inventory/low-stock'),
  getLowStock: () => apiClient.get('/api/inventory/low-stock'),
  
  // Get inventory statistics
  getInventoryStats: () => apiClient.get('/api/inventory/stats'),
  
  // Legacy aliases for compatibility
  getInventory: (params) => {
    return apiClient.get('/api/products', { params: { ...params, lowStock: true } });
  },
  adjustStock: (data) => apiClient.post('/api/inventory/adjust', data),
  getInventoryHistory: (productId) => {
    return apiClient.get('/api/inventory/logs', { params: { productId } });
  },
  getAnalytics: () => apiClient.get('/api/inventory/stats')
};

export default inventoryAPI;
