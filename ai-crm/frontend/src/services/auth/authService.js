import { API_BASE_URL } from '@/utils/constants';

/**
 * Authentication service using MongoDB backend
 * All authentication is handled via the MongoDB backend API
 */
export const authService = {
  // Sign up - MongoDB backend handles user creation
  async signUp({ email, password, firstName, lastName, companyName }) {
    const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email,
        password,
        name: `${firstName} ${lastName}`,
        role: 'customer'
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Registration failed');
    }

    const data = await response.json();
    return {
      user: data.user,
      session: { access_token: data.token }
    };
  },

  // Sign in with email and password
  async signIn({ email, password }) {
    const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email,
        password
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Login failed');
    }

    const data = await response.json();
    return {
      user: data.user,
      session: { access_token: data.token }
    };
  },

  // OAuth not implemented for MongoDB backend
  async signInWithOAuth(provider) {
    throw new Error('OAuth login is not implemented in this version.');
  },

  // Sign out
  async signOut() {
    localStorage.removeItem('token');
    return { error: null };
  },

  // Password reset not implemented yet
  async resetPassword(email) {
    throw new Error('Password reset is not implemented yet.');
  },

  // Update password not implemented yet
  async updatePassword(newPassword) {
    throw new Error('Password update is not implemented yet.');
  },

  // Get current session from localStorage
  async getSession() {
    const token = localStorage.getItem('token');
    return token ? { access_token: token } : null;
  },

  // Get current user from backend
  async getCurrentUser() {
    const token = localStorage.getItem('token');
    if (!token) return null;

    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) return null;
      
      const data = await response.json();
      return data.user;
    } catch (error) {
      console.error('Error fetching current user:', error);
      return null;
    }
  },

  // Profile methods not needed with MongoDB backend
  async createUserProfile(userId, profileData) {
    return null;
  },

  async updateUserProfile(userId, updates) {
    return null;
  },

  async getUserProfile(userId) {
    return null;
  },

  // Email verification not implemented
  async resendVerificationEmail(email) {
    throw new Error('Email verification is not implemented yet.');
  }
}

export default authService
