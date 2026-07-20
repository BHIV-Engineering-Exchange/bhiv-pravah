import apiClient from './baseAPI';

export const supplierAPI = {
  // Suppliers
  getSuppliers: (params) => apiClient.get('/suppliers', { params }),
  getSupplier: (id) => apiClient.get(`/suppliers/${id}`),
  createSupplier: (data) => apiClient.post('/suppliers', data),
  updateSupplier: (id, data) => apiClient.put(`/suppliers/${id}`, data),
  deleteSupplier: (id) => apiClient.delete(`/suppliers/${id}`),
  
  // Supplier Contacts
  getSupplierContacts: (supplierId) => apiClient.get(`/suppliers/${supplierId}/contacts`),
  addContact: (supplierId, data) => apiClient.post(`/suppliers/${supplierId}/contacts`, data),
  updateContact: (supplierId, contactId, data) => apiClient.put(`/suppliers/${supplierId}/contacts/${contactId}`, data),
  
  // Supplier Products
  getSupplierProducts: (supplierId) => apiClient.get(`/suppliers/${supplierId}/products`),
  
  // Supplier Performance
  getSupplierMetrics: (supplierId) => apiClient.get(`/suppliers/${supplierId}/metrics`),
};

export default supplierAPI;

