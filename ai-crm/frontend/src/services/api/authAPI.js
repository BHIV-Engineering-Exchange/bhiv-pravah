import apiClient from './baseAPI';

// MongoDB Backend API Service
export const authAPI = {
  // Login
  login: (credentials) => apiClient.post('/api/auth/login', credentials),
  
  // Register (only for first admin)
  register: (userData) => apiClient.post('/api/auth/register', userData),
  
  // Get current user
  getCurrentUser: () => apiClient.get('/api/auth/me'),
  
  // Logout (client-side only)
  logout: () => {
    localStorage.removeItem('token');
    return Promise.resolve();
  }
};

export default authAPI;
