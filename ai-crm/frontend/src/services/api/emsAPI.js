import apiClient from './baseAPI';

export const emsAPI = {
  // Email Triggers
  sendRestockAlert: (data) => apiClient.post('/api/ems/restock-alert', data),
  sendPurchaseOrder: (data) => apiClient.post('/api/ems/purchase-order', data),
  sendShipmentNotification: (data) => apiClient.post('/api/ems/shipment-notification', data),
  sendDeliveryDelay: (data) => apiClient.post('/api/ems/delivery-delay', data),
  
  // Scheduled Emails
  getScheduledEmails: () => apiClient.get('/api/ems/scheduled'),
  scheduleEmail: (data) => apiClient.post('/api/ems/schedule', data),
  cancelScheduledEmail: (id) => apiClient.delete(`/api/ems/scheduled/${id}`),
  processScheduledEmails: () => apiClient.post('/api/ems/process-scheduled'),
  
  // Email Activity
  getEmailActivity: (params) => apiClient.get('/api/ems/activity', { params }),
  getEmailStats: () => apiClient.get('/api/ems/stats'),
  
  // Email Templates
  getTemplates: () => apiClient.get('/api/ems/templates'),
  getTemplate: (id) => apiClient.get(`/api/ems/templates/${id}`),
  createTemplate: (data) => apiClient.post('/api/ems/templates', data),
  updateTemplate: (id, data) => apiClient.put(`/api/ems/templates/${id}`, data),
  
  // Settings
  getSettings: () => apiClient.get('/api/ems/settings'),
  updateSettings: (data) => apiClient.put('/api/ems/settings', data),
};

export default emsAPI;

