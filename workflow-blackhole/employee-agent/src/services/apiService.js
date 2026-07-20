const axios = require('axios');
const fs = require('fs');
const path = require('path');

class ApiService {
  constructor() {
    this.baseURL = this.loadApiBaseUrl();
    this.authToken = null;
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json'
      }
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        if (this.authToken) {
          // Backend expects x-auth-token header, not Authorization Bearer
          config.headers['x-auth-token'] = this.authToken;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response) {
          // Server responded with error status
          console.error('API Error:', error.response.data);
        } else if (error.request) {
          // Request made but no response
          console.error('Network Error:', error.message);
        } else {
          // Something else happened
          console.error('Error:', error.message);
        }
        return Promise.reject(error);
      }
    );
  }

  loadApiBaseUrl() {
    try {
      // Try to load from .env file
      const envPath = path.join(__dirname, '../../.env');
      if (fs.existsSync(envPath)) {
        const envContent = fs.readFileSync(envPath, 'utf-8');
        const match = envContent.match(/AGENT_API_BASE_URL=(.+)/);
        if (match && match[1]) {
          const url = match[1].trim();
          console.log('✓ Loaded backend URL from .env:', url);
          return url;
        }
      } else {
        console.log('⚠ .env file not found at:', envPath);
      }
    } catch (error) {
      console.error('Error loading .env file:', error);
    }

    // Fallback to default or environment variable
    const fallbackUrl = process.env.AGENT_API_BASE_URL || 'http://127.0.0.1:5001';
    console.log('Using fallback backend URL:', fallbackUrl);
    return fallbackUrl;
  }

  setAuthToken(token) {
    this.authToken = token;
  }

  /**
   * Login to the backend
   * @param {Object} credentials - { email, password }
   * @returns {Promise<Object>} - { success, token, user, error }
   */
  async login(credentials) {
    try {
      console.log('🔐 Attempting login with:', { 
        email: credentials.email, 
        passwordLength: credentials.password?.length,
        url: `${this.baseURL}/api/auth/login`
      });
      
      const response = await this.client.post('/api/auth/login', credentials);
      
      console.log('✅ Login response:', { 
        hasToken: !!response.data?.token,
        hasUser: !!response.data?.user 
      });
      
      if (response.data && response.data.token) {
        return {
          success: true,
          token: response.data.token,
          user: response.data.user || { email: credentials.email }
        };
      }

      return {
        success: false,
        error: 'Invalid response from server'
      };
    } catch (error) {
      console.error('❌ Login error:', {
        status: error.response?.status,
        message: error.response?.data?.error || error.message
      });
      
      return {
        success: false,
        error: error.response?.data?.error || error.message || 'Login failed'
      };
    }
  }

  /**
   * Start the work day
   * @returns {Promise<Object>} - { success, attendanceId, error }
   */
  async startDay() {
    try {
      // Get user ID from stored token
      const userId = this.getUserIdFromToken();
      if (!userId) {
        return {
          success: false,
          error: 'User not authenticated'
        };
      }

      // Use sample location data for desktop agent (work from home mode)
      // Using generic coordinates - can be replaced with actual geolocation API later
      const locationData = {
        latitude: 40.7128,  // Sample latitude (New York City)
        longitude: -74.0060, // Sample longitude (New York City)
        address: 'Work From Home - Desktop Agent',
        accuracy: 10,
        workFromHome: true,
        homeLocation: { 
          latitude: 40.7128, 
          longitude: -74.0060 
        }
      };

      const response = await this.client.post(`/api/attendance/start-day/${userId}`, locationData);
      
      if (response.data && (response.data.success !== false)) {
        return {
          success: true,
          attendanceId: response.data.attendanceId || response.data.attendance?._id || response.data._id
        };
      }

      return {
        success: false,
        error: response.data?.message || 'Failed to start day'
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || error.message || 'Failed to start day'
      };
    }
  }

  /**
   * Extract user ID from JWT token
   */
  getUserIdFromToken() {
    if (!this.authToken) return null;
    
    try {
      // JWT tokens have 3 parts: header.payload.signature
      const parts = this.authToken.split('.');
      if (parts.length !== 3) return null;
      
      // Decode the payload (base64)
      const payload = JSON.parse(Buffer.from(parts[1], 'base64').toString());
      
      // Backend JWT structure: { user: { id: "..." } }
      return payload.user?.id || payload.id || payload.userId || payload.sub;
    } catch (error) {
      console.error('Error decoding token:', error);
      return null;
    }
  }

  /**
   * End the work day
   * @returns {Promise<Object>} - { success, error }
   */
  async endDay() {
    try {
      // Get user ID from stored token
      const userId = this.getUserIdFromToken();
      if (!userId) {
        return {
          success: false,
          error: 'User not authenticated'
        };
      }

      // Use sample location data for desktop agent (work from home mode)
      const locationData = {
        latitude: 40.7128,  // Sample latitude (New York City)
        longitude: -74.0060, // Sample longitude (New York City)
        address: 'Work From Home - Desktop Agent',
        accuracy: 10
      };

      const response = await this.client.post(`/api/attendance/end-day/${userId}`, locationData);
      
      if (response.data && (response.data.success !== false || response.status === 200)) {
        return {
          success: true
        };
      }

      return {
        success: false,
        error: response.data?.message || 'Failed to end day'
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || error.message || 'Failed to end day'
      };
    }
  }

  /**
   * Check attendance status for today (POLLING ENDPOINT)
   * This is called every 30 seconds by the attendance poller
   * @returns {Promise<Object>} - { dayStarted, attendanceId, startTime, workLocation }
   */
  async checkAttendanceStatus() {
    try {
      const response = await this.client.get('/api/attendance/status');
      
      return {
        dayStarted: response.data.dayStarted || false,
        attendanceId: response.data.attendanceId || null,
        startTime: response.data.startTime || null,
        workLocation: response.data.workLocation || null
      };
    } catch (error) {
      console.error('❌ Failed to check attendance status:', error.response?.data || error.message);
      return { 
        dayStarted: false,
        attendanceId: null,
        startTime: null
      };
    }
  }

  /**
   * Send activity data to the backend
   * @param {Object} activityData - Activity tracking data
   * @returns {Promise<Object>} - { success, error }
   */
  async ingestActivity(activityData) {
    try {
      const response = await this.client.post('/api/agent/activity/ingest', activityData);
      
      if (response.data && (response.data.success || response.status === 200)) {
        return {
          success: true
        };
      }

      return {
        success: false,
        error: response.data?.error || response.data?.message || 'Failed to ingest activity'
      };
    } catch (error) {
      // If the server rejects activity (e.g., day not started), log but don't crash
      console.error('Activity ingestion failed:', error.response?.data?.error || error.message);
      
      return {
        success: false,
        error: error.response?.data?.error || error.response?.data?.message || error.message || 'Failed to ingest activity'
      };
    }
  }

  /**
   * Verify authentication token
   * @returns {Promise<Object>} - { valid, user, error }
   */
  async verifyToken() {
    try {
      const response = await this.client.get('/api/agent/verify');
      
      if (response.data && response.data.valid) {
        return {
          valid: true,
          user: response.data.user
        };
      }

      return {
        valid: false
      };
    } catch (error) {
      return {
        valid: false,
        error: error.response?.data?.message || error.message
      };
    }
  }
}

module.exports = ApiService;
