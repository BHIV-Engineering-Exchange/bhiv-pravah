import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001';

const getAuthHeader = () => {
  const token = localStorage.getItem('token');
  return { 'x-auth-token': token };
};

/**
 * Enhanced Salary API Service
 * Handles all API calls for enhanced salary management with live attendance
 */

export const enhancedSalaryAPI = {
  /**
   * Upload biometric data file
   */
  uploadBiometric: async (file, onProgress) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await axios.post(
      `${API_URL}/api/enhanced-salary/upload-biometric`,
      formData,
      {
        headers: {
          ...getAuthHeader(),
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: onProgress
      }
    );
    return response.data;
  },

  /**
   * Get salary dashboard for all employees
   */
  getDashboard: async (year, month, filters = {}) => {
    const response = await axios.get(
      `${API_URL}/api/enhanced-salary/dashboard/${year}/${month}`,
      {
        headers: getAuthHeader(),
        params: filters
      }
    );
    return response.data;
  },

  /**
   * Calculate salary for specific employee
   */
  calculateEmployeeSalary: async (userId, year, month) => {
    const response = await axios.get(
      `${API_URL}/api/enhanced-salary/calculate/${userId}/${year}/${month}`,
      {
        headers: getAuthHeader()
      }
    );
    return response.data;
  },

  /**
   * Get detailed hours breakdown for an employee
   */
  getHoursBreakdown: async (userId, year, month) => {
    const response = await axios.get(
      `${API_URL}/api/enhanced-salary/hours-breakdown/${userId}/${year}/${month}`,
      {
        headers: getAuthHeader()
      }
    );
    return response.data;
  },

  /**
   * Get WFH vs Office analysis
   */
  getWFHAnalysis: async (userId, year, month) => {
    const response = await axios.get(
      `${API_URL}/api/enhanced-salary/wfh-analysis/${userId}/${year}/${month}`,
      {
        headers: getAuthHeader()
      }
    );
    return response.data;
  }
};

export default enhancedSalaryAPI;
