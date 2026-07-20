import apiClient from './baseAPI';

export const unifiedAPI = {
  // Dashboard Overview
  getDashboardData: () => apiClient.get('/dashboard/crm'),
  getKPIs: () => apiClient.get('/api/dashboard/kpis'),
  getAlerts: () => apiClient.get('/api/dashboard/alerts'),
  getCharts: () => apiClient.get('/api/dashboard/charts'),
  getActivity: () => apiClient.get('/api/dashboard/activity'),
  getSystemStatus: () => apiClient.get('/api/dashboard/system-status'),
  
  // Orders & Logistics
  getOrders: (params) => apiClient.get('/orders', { params }),
  createOrder: (data) => apiClient.post('/orders', data),
  getOrder: (id) => apiClient.get(`/orders/${id}`),
  getShipments: (params) => apiClient.get('/shipments', { params }),
  getShipment: (id) => apiClient.get(`/shipments/${id}`),
  
  // Inventory
  getInventory: (params) => apiClient.get('/inventory', { params }),
  getLowStock: (threshold) => apiClient.get('/inventory/low-stock', { 
    params: { threshold } 
  }),
  getStockAlerts: () => apiClient.get('/inventory/alerts'),
  
  // Suppliers
  getSuppliers: () => apiClient.get('/suppliers'),
  createSupplier: (data) => apiClient.post('/suppliers', data),
  getSupplier: (id) => apiClient.get(`/suppliers/${id}`),
  
  // Products
  getProducts: (params) => apiClient.get('/products', { params }),
  getProduct: (id) => apiClient.get(`/products/${id}`),
  uploadProductImage: (productId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post(`/products/${productId}/image`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
};

export default unifiedAPI;

