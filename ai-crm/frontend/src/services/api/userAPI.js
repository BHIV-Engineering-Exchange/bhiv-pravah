import apiClient from './baseAPI';

// MongoDB Backend User API
export const userAPI = {
  // Get all users
  getUsers: (params = {}) => {
    const { page = 1, limit = 50, role, search } = params;
    return apiClient.get('/api/users', {
      params: {
        page,
        limit,
        ...(role && { role }),
        ...(search && { search })
      }
    });
  },
  
  // Get single user
  getUser: (id) => apiClient.get(`/api/users/${id}`),
  
  // Get current user
  getCurrentUser: () => apiClient.get('/api/auth/me'),
  
  // Create user (admin only)
  createUser: (data) => apiClient.post('/api/users', data),
  
  // Update user
  updateUser: (id, data) => apiClient.put(`/api/users/${id}`, data),
  
  // Delete user
  deleteUser: (id) => apiClient.delete(`/api/users/${id}`),
  
  // Get user statistics
  getStats: () => apiClient.get('/api/users/stats/summary'),
  
  // Legacy aliases
  getUserProfile: (id) => apiClient.get(`/api/users/${id}`),
  updateUserProfile: (id, data) => apiClient.put(`/api/users/${id}`, data),
  updateUserRole: (id, role) => apiClient.put(`/api/users/${id}`, { role }),
  updateUserPermissions: (id, permissions) => apiClient.put(`/api/users/${id}`, { permissions })
};

export default userAPI;

