import apiClient from './baseAPI';

export const employeeAPI = {
  // Employee Metrics
  getEmployeeMetrics: (employeeId) => apiClient.get(`/api/employee/${employeeId}/metrics`),
  
  // Employee Reviews
  requestEmployeeReview: (employeeId, data) => apiClient.post(`/api/employee/${employeeId}/review-request`, data),
  
  // Employee Attendance
  getEmployeeAttendance: (employeeId) => apiClient.get(`/api/employee/${employeeId}/attendance`),
  getAttendanceRecords: (employeeId) => apiClient.get(`/api/attendance/${employeeId}`),
  checkIn: (data) => apiClient.post('/api/attendance/checkin', data),
  checkOut: (data) => apiClient.post('/api/attendance/checkout', data),
  
  // Employee Privacy
  updateEmployeePrivacy: (employeeId, settings) => apiClient.put(`/api/employee/${employeeId}/privacy`, settings),
};

export default employeeAPI;

