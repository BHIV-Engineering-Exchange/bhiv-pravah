import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const dashboardAPI = {
  getKPIs: () => api.get('/api/dashboard/kpis'),
  getAlerts: () => api.get('/api/dashboard/alerts'),
  getCharts: () => api.get('/api/dashboard/charts'),
  getRecentActivity: () => api.get('/api/dashboard/activity'),
  getSystemStatus: () => api.get('/api/dashboard/system-status'),
};

export const employeeAPI = {
  getPersonalMetrics: (employeeId) => api.get(`/api/employee/${employeeId}/metrics`),
  requestReview: (employeeId, data) => api.post(`/api/employee/${employeeId}/review-request`, data),
  getAttendanceHistory: (employeeId) => api.get(`/api/employee/${employeeId}/attendance`),
};

export const attendanceAPI = {
  checkIn: (data) => api.post('/api/attendance/checkin', data),
  checkOut: (data) => api.post('/api/attendance/checkout', data),
  getAttendanceRecords: (employeeId) => api.get(`/api/attendance/${employeeId}`),
  updatePrivacySettings: (employeeId, settings) => api.put(`/api/employee/${employeeId}/privacy`, settings),
};

export default api;