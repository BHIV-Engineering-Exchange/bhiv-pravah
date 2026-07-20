/**
 * EMS API Service for Gurukul Frontend
 * Handles all API calls to EMS System through Gurukul backend proxy
 */

import API_BASE_URL from '../config';
import { handleApiError } from '../utils/apiClient';

class EMSApiService {
    /**
     * Make API request with EMS token header
     * @param {string} endpoint - API endpoint
     * @param {object} options - Fetch options
     * @param {string} emsToken - EMS authentication token
     * @returns {Promise<any>} Response data
     */
    async _request(endpoint, options = {}, emsToken) {
        const url = `${API_BASE_URL}${endpoint}`;
        
        const headers = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
            ...(emsToken ? { 'X-EMS-Token': emsToken } : {}),
            ...(options.headers || {})
        };

        const response = await fetch(url, {
            ...options,
            headers
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: response.statusText }));
            throw new Error(errorData.detail || errorData.message || `HTTP ${response.status}`);
        }

        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        }
        
        return await response.text();
    }

    /**
     * Get or create EMS token
     * @param {string} email - Student email
     * @param {string} password - Student password
     * @returns {Promise<string>} EMS token
     */
    async getEMSToken(email, password) {
        try {
            const response = await this._request(
                '/api/v1/ems/student/auth/ems-token',
                {
                    method: 'POST',
                    body: JSON.stringify({ email, password })
                }
            );
            const token = response.ems_token;
            if (token) {
                localStorage.setItem('ems_token', token);
            }
            return token;
        } catch (error) {
            const errorInfo = handleApiError(error, { context: 'EMS Authentication' });
            throw new Error(errorInfo.message || 'Failed to authenticate with EMS');
        }
    }

    /**
     * Get EMS token from localStorage or fetch new one
     * @param {string} email - Student email
     * @param {string} password - Student password (if token doesn't exist)
     * @returns {Promise<string>} EMS token
     */
    async getOrFetchEMSToken(email, password = null) {
        // Check if token exists in localStorage
        const storedToken = localStorage.getItem('ems_token');
        if (storedToken) {
            return storedToken;
        }

        // Fetch new token if password provided
        if (password) {
            return await this.getEMSToken(email, password);
        }

        throw new Error('EMS token not found. Please authenticate with EMS.');
    }

    /**
     * Build query string from params object
     * @param {object} params - Query parameters
     * @returns {string} Query string
     */
    _buildQueryString(params) {
        const searchParams = new URLSearchParams();
        Object.entries(params).forEach(([key, value]) => {
            if (value !== null && value !== undefined) {
                searchParams.append(key, value.toString());
            }
        });
        const queryString = searchParams.toString();
        return queryString ? `?${queryString}` : '';
    }

    /**
     * Get student dashboard statistics
     * @param {string} emsToken - EMS authentication token
     * @returns {Promise<object>} Dashboard stats
     */
    async getDashboardStats(emsToken) {
        try {
            return await this._request('/api/v1/ems/student/dashboard/stats', { method: 'GET' }, emsToken);
        } catch (error) {
            throw handleApiError(error, { context: 'Fetching dashboard stats' });
        }
    }

    /**
     * Get student's classes
     * @param {string} emsToken - EMS authentication token
     * @returns {Promise<Array>} List of classes
     */
    async getClasses(emsToken) {
        try {
            return await this._request('/api/v1/ems/student/classes', { method: 'GET' }, emsToken);
        } catch (error) {
            throw handleApiError(error, { context: 'Fetching classes' });
        }
    }

    /**
     * Get student's lessons
     * @param {string} emsToken - EMS authentication token
     * @param {number|null} classId - Optional class ID filter
     * @returns {Promise<Array>} List of lessons
     */
    async getLessons(emsToken, classId = null) {
        try {
            const queryString = this._buildQueryString({ class_id: classId });
            return await this._request(`/api/v1/ems/student/lessons${queryString}`, { method: 'GET' }, emsToken);
        } catch (error) {
            throw handleApiError(error, { context: 'Fetching lessons' });
        }
    }

    /**
     * Get student's timetable/schedule
     * @param {string} emsToken - EMS authentication token
     * @returns {Promise<Array>} List of timetable slots
     */
    async getTimetable(emsToken) {
        try {
            return await this._request('/api/v1/ems/student/timetable', { method: 'GET' }, emsToken);
        } catch (error) {
            throw handleApiError(error, { context: 'Fetching timetable' });
        }
    }

    /**
     * Get student announcements
     * @param {string} emsToken - EMS authentication token
     * @returns {Promise<Array>} List of announcements
     */
    async getAnnouncements(emsToken) {
        try {
            return await this._request('/api/v1/ems/student/announcements', { method: 'GET' }, emsToken);
        } catch (error) {
            throw handleApiError(error, { context: 'Fetching announcements' });
        }
    }

    /**
     * Get student's attendance records
     * @param {string} emsToken - EMS authentication token
     * @param {number|null} classId - Optional class ID filter
     * @param {string|null} date - Optional date filter (YYYY-MM-DD)
     * @returns {Promise<Array>} List of attendance records
     */
    async getAttendance(emsToken, classId = null, date = null) {
        try {
            const queryString = this._buildQueryString({ class_id: classId, attendance_date: date });
            return await this._request(`/api/v1/ems/student/attendance${queryString}`, { method: 'GET' }, emsToken);
        } catch (error) {
            throw handleApiError(error, { context: 'Fetching attendance' });
        }
    }

    /**
     * Get student's teachers
     * @param {string} emsToken - EMS authentication token
     * @returns {Promise<Array>} List of teachers
     */
    async getTeachers(emsToken) {
        try {
            return await this._request('/api/v1/ems/student/teachers', { method: 'GET' }, emsToken);
        } catch (error) {
            throw handleApiError(error, { context: 'Fetching teachers' });
        }
    }

    /**
     * Get student's grades
     * @param {string} emsToken - EMS authentication token
     * @param {number|null} classId - Optional class ID filter
     * @returns {Promise<Array>} List of grades
     */
    async getGrades(emsToken, classId = null) {
        try {
            const queryString = this._buildQueryString({ class_id: classId });
            return await this._request(`/api/v1/ems/student/grades${queryString}`, { method: 'GET' }, emsToken);
        } catch (error) {
            throw handleApiError(error, { context: 'Fetching grades' });
        }
    }

    /**
     * Check EMS system health
     * @returns {Promise<object>} Health status
     */
    async checkHealth() {
        try {
            return await this._request('/api/v1/ems/student/health', { method: 'GET' });
        } catch (error) {
            return { ems_status: 'unreachable', error: error.message };
        }
    }
}

// Export singleton instance
export const emsApi = new EMSApiService();
export default emsApi;
