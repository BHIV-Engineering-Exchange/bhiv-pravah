import axios from 'axios';
import { authStorage } from '../utils/authStorage';

// Define types for user and auth response
interface User {
  id: string;
  email: string;
  name?: string;
  role?: string;
}

interface RegisterRequest {
  email: string;
  password: string;
  name: string;
  role?: string; // 'candidate' | 'recruiter' | 'client'
  company?: string; // For recruiter/client
  phone?: string;
}

interface AuthResponse {
  success: boolean;
  token?: string;
  user?: User;
  error?: string;
}

class AuthService {
  private API_BASE_URL: string;
  private TOKEN_KEY = 'auth_token';
  private USER_KEY = 'user_data';

  constructor() {
    // Standardized variable name: VITE_API_BASE_URL (see ENVIRONMENT_VARIABLES.md)
    this.API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  }

  // Login user and store JWT token - supports candidate, recruiter, and client
  async login(email: string, password: string, role?: string): Promise<AuthResponse> {
    try {
      // Get role from parameter, or from localStorage (stored during registration)
      // This ensures we use the role the user registered with
      const storedRole = authStorage.getItem('user_role');
      const userRole = role || storedRole;
      
      let response;
      
      if (!userRole) {
        // If no role is stored and none provided, try to detect by attempting both logins
        // This handles edge cases where localStorage was cleared
        console.log('🔐 No role found, attempting auto-detection...');
        
        // Try client login first
        try {
          const clientResponse = await axios.post(`${this.API_BASE_URL}/v1/client/login`, {
            email: email,
            password: password
          });
          
          if (clientResponse.data.success && clientResponse.data.access_token) {
            const token = clientResponse.data.access_token;
            const userData = {
              id: clientResponse.data.client_id,
              email: email,
              name: clientResponse.data.company_name || '',
              role: 'client',
              company: clientResponse.data.company_name
            };
            
            console.log('🔐 Auto-detected: Client');
            this.setAuthToken(token);
            authStorage.setItem(this.TOKEN_KEY, token);
            authStorage.setItem('auth_token', token);
            authStorage.setItem(this.USER_KEY, JSON.stringify(userData));
            authStorage.setItem('client_id', clientResponse.data.client_id);
            authStorage.setItem('user_role', 'client');
            
            return {
              success: true,
              token: token,
              user: userData
            };
          }
        } catch (clientError: any) {
          // Client login failed, will try candidate/recruiter login below
          console.log('🔐 Client login failed, trying candidate/recruiter login');
        }
      }
      
      // Use stored role to determine which endpoint to call
      // Client uses /v1/client/login, candidate/recruiter use /v1/candidate/login
      if (userRole === 'client') {
        // Try client login with email (backend now supports email-based login)
        try {
          response = await axios.post(`${this.API_BASE_URL}/v1/client/login`, {
            email: email,
            password: password
          });
          
          if (response.data.success && response.data.access_token) {
            const token = response.data.access_token;
            
            // Validate token is not empty
            if (!token || token.trim() === '') {
              console.error('❌ Client login response has empty token!');
              return { success: false, error: 'Invalid token received from server' };
            }
            
            const userData = {
              id: response.data.client_id,
              email: email,
              name: response.data.company_name || '',
              role: 'client',
              company: response.data.company_name
            };
            
            // Store token using multiple methods to ensure it's saved
            console.log('🔐 Storing client auth token after login');
            console.log('🔐 Client token length:', token.length);
            console.log('🔐 Client token first 50 chars:', token.substring(0, 50));
            
            this.setAuthToken(token);
            authStorage.setItem(this.TOKEN_KEY, token);
            authStorage.setItem('auth_token', token);
            
            const storedToken = authStorage.getItem(this.TOKEN_KEY);
            const storedTokenDirect = authStorage.getItem('auth_token');
            
            if (!storedToken && !storedTokenDirect) {
              console.error('❌ CRITICAL: Failed to store client token! Auth storage may be disabled or full.');
              console.error('❌ Available storage keys:', typeof sessionStorage !== 'undefined' ? Object.keys(sessionStorage) : []);
            } else if (storedToken !== token && storedTokenDirect !== token) {
              console.error('❌ Client token stored but value mismatch!');
              console.error('❌ Expected length:', token.length, 'Stored length:', storedToken?.length || storedTokenDirect?.length);
            } else {
              console.log('✅ Client token stored successfully');
              console.log('✅ Client token verification: Stored token matches');
            }
            
            authStorage.setItem(this.USER_KEY, JSON.stringify(userData));
            authStorage.setItem('client_id', response.data.client_id);
            authStorage.setItem('user_role', 'client');
            
            return {
              success: true,
              token: token,
              user: userData
            };
          } else {
            console.error('❌ Client login failed: No access_token in response', response.data);
            return {
              success: false,
              error: response.data.error || 'Client login failed. No token received.'
            };
          }
        } catch (clientError: any) {
          // If client login fails, don't fall back to candidate login
          // Return error so user knows client login failed
          console.error('❌ Client login error:', clientError.response?.data?.error || clientError.message);
          return {
            success: false,
            error: clientError.response?.data?.error || 'Client login failed. Please check your credentials.'
          };
        }
      }
      
      // For recruiter and candidate (or client fallback), use candidate login
      // Backend candidate login works for both candidates and recruiters (stored as candidates)
      try {
        response = await axios.post(`${this.API_BASE_URL}/v1/candidate/login`, {
          email,
          password
        });
      } catch (candidateError: any) {
        // If candidate login fails with "Invalid credentials", try client login as fallback
        // This handles cases where user_role was incorrectly set to 'candidate' for a client
        if (candidateError.response?.status === 401 || 
            candidateError.response?.data?.error?.includes('Invalid credentials') ||
            candidateError.response?.data?.error?.includes('Invalid')) {
          console.log('🔐 Candidate login failed, trying client login as fallback...');
          
          try {
            response = await axios.post(`${this.API_BASE_URL}/v1/client/login`, {
              email: email,
              password: password
            });
            
            if (response.data.success && response.data.access_token) {
              // Client login succeeded - handle it
              const token = response.data.access_token;
              
              if (!token || token.trim() === '') {
                console.error('❌ Client login response has empty token!');
                return { success: false, error: 'Invalid token received from server' };
              }
              
              const userData = {
                id: response.data.client_id,
                email: email,
                name: response.data.company_name || '',
                role: 'client',
                company: response.data.company_name
              };
              
              console.log('🔐 Storing client auth token after fallback login');
              this.setAuthToken(token);
              authStorage.setItem(this.TOKEN_KEY, token);
              authStorage.setItem('auth_token', token);
              authStorage.setItem(this.USER_KEY, JSON.stringify(userData));
              authStorage.setItem('client_id', response.data.client_id);
              authStorage.setItem('user_role', 'client');
              
              return {
                success: true,
                token: token,
                user: userData
              };
            }
          } catch (clientFallbackError: any) {
            // Both logins failed
            console.error('❌ Both candidate and client login failed');
            return {
              success: false,
              error: candidateError.response?.data?.error || 'Invalid credentials'
            };
          }
        }
        
        // Re-throw if it's not an "Invalid credentials" error
        throw candidateError;
      }

      // Backend returns 'candidate' but we need to set correct role
      if (response.data.token && response.data.success) {
        const userData = response.data.candidate || response.data.user;
        const token = response.data.token;
        
        // Validate token is not empty
        if (!token || token.trim() === '') {
          console.error('❌ Login response has empty token!');
          return { success: false, error: 'Invalid token received from server' };
        }
        
        // Override role from localStorage if available (for recruiter)
        const actualRole = userRole === 'recruiter' ? 'recruiter' : (userData.role || 'candidate');
        const userWithRole = { ...userData, role: actualRole };
        
        // Store token FIRST - this is critical
        console.log('🔐 Storing auth token after login');
        console.log('🔐 Token length:', token.length);
        console.log('🔐 Token first 50 chars:', token.substring(0, 50));
        
        this.setAuthToken(token);
        authStorage.setItem(this.TOKEN_KEY, token);
        authStorage.setItem('auth_token', token);
        
        const storedToken = authStorage.getItem(this.TOKEN_KEY);
        const storedTokenDirect = authStorage.getItem('auth_token');
        
        if (!storedToken && !storedTokenDirect) {
          console.error('❌ CRITICAL: Failed to store token! Auth storage may be disabled or full.');
          console.error('❌ Available storage keys:', typeof sessionStorage !== 'undefined' ? Object.keys(sessionStorage) : []);
        } else if (storedToken !== token && storedTokenDirect !== token) {
          console.error('❌ Token stored but value mismatch!');
          console.error('❌ Expected length:', token.length, 'Stored length:', storedToken?.length || storedTokenDirect?.length);
        } else {
          console.log('✅ Token stored successfully');
          console.log('✅ Token verification: Stored token matches');
        }
        
        authStorage.setItem(this.USER_KEY, JSON.stringify(userWithRole));
        authStorage.setItem('user_role', actualRole);
        
        if (response.data.candidate_id) {
          authStorage.setItem('backend_candidate_id', response.data.candidate_id.toString());
          authStorage.setItem('candidate_id', response.data.candidate_id.toString());
        } else if (userData.id) {
          authStorage.setItem('backend_candidate_id', userData.id.toString());
          authStorage.setItem('candidate_id', userData.id.toString());
        }
        
        return {
          success: true,
          token: token,
          user: userWithRole
        };
      }

      // Handle error response
      if (response.data.error) {
        return { success: false, error: response.data.error };
      }

      return { success: false, error: 'Invalid response from server' };
    } catch (error: any) {
      console.error('Login error:', error);
      return { 
        success: false, 
        error: error.response?.data?.error || error.response?.data?.message || error.message || 'Login failed' 
      };
    }
  }

  // Register new user - supports candidate, recruiter, and client
  async register(userData: RegisterRequest): Promise<AuthResponse> {
    try {
      const role = userData.role || 'candidate';
      
      let response;
      
      if (role === 'client') {
        // Client registration requires client_id and company_name
        const client_id = userData.email.split('@')[0] + '_' + Date.now(); // Generate client_id from email
        
        response = await axios.post(`${this.API_BASE_URL}/v1/client/register`, {
          client_id: client_id,
          company_name: userData.company || userData.name + "'s Company",
          contact_email: userData.email,
          password: userData.password
        });
        
        // Client registration successful - don't auto-login, just return success
        if (response.data.success) {
          const final_client_id = response.data.client_id || client_id;
          
          authStorage.setItem('client_id', final_client_id);
          
          // Store role for later login
          const userObj = {
            id: final_client_id,
            email: userData.email,
            name: userData.name,
            role: 'client',
            company: userData.company
          };
          
          return {
            success: true,
            user: userObj,
            // Note: Client login uses client_id, not email - stored in localStorage
          };
        }
      } else if (role === 'recruiter') {
        // Recruiter registration - use candidate endpoint with role field
        response = await axios.post(`${this.API_BASE_URL}/v1/candidate/register`, {
          email: userData.email,
          password: userData.password,
          name: userData.name,
          phone: userData.phone || '',
          location: '',
          experience_years: 0,
          technical_skills: '',
          education_level: '',
          seniority_level: '',
          role: 'recruiter'  // Send role field to backend
        });
        
        // Registration successful - store role but don't auto-login
        if (response.data.success) {
          const userObj = {
            id: response.data.candidate_id || '',
            email: userData.email,
            name: userData.name,
            role: 'recruiter' // Override role from candidate registration
          };
          
          return {
            success: true,
            user: userObj
          };
        }
      } else {
        // Candidate registration (default)
        response = await axios.post(`${this.API_BASE_URL}/v1/candidate/register`, {
          email: userData.email,
          password: userData.password,
          name: userData.name,
          phone: userData.phone || '',
          location: '',
          experience_years: 0,
          technical_skills: '',
          education_level: '',
          seniority_level: ''
        });
        
        // Registration successful - store role but don't auto-login
        if (response.data.success) {
          const userObj = {
            id: response.data.candidate_id || '',
            email: userData.email,
            name: userData.name,
            role: 'candidate'
          };
          
          return {
            success: true,
            user: userObj
          };
        }
      }

      // Handle error response
      if (response.data.error || !response.data.success) {
        const errorMsg = response.data.error || 'Registration failed';
        return { success: false, error: errorMsg };
      }

      return { success: false, error: 'Invalid response from server' };
    } catch (error: any) {
      console.error('Registration error:', error);
      // Handle duplicate email error
      const errorMsg = error.response?.data?.error || error.response?.data?.message || error.message || 'Registration failed';
      
      // Check for email already registered error
      if (errorMsg.includes('already registered') || 
          errorMsg.includes('Email already registered') ||
          errorMsg.includes('already exists')) {
        return { success: false, error: 'This email is already registered. Please use a different email or login instead.' };
      }
      
      return { 
        success: false, 
        error: errorMsg
      };
    }
  }

  logout(): void {
    this.removeAuthToken();
    authStorage.removeItem(this.USER_KEY);
  }

  getAuthToken(): string | null {
    return authStorage.getItem(this.TOKEN_KEY);
  }

  setAuthToken(token: string): void {
    authStorage.setItem(this.TOKEN_KEY, token);
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  removeAuthToken(): void {
    authStorage.removeItem(this.TOKEN_KEY);
    delete axios.defaults.headers.common['Authorization'];
  }

  // Check if user is authenticated
  isAuthenticated(): boolean {
    const token = this.getAuthToken();
    if (!token) return false;

    // Check if token is expired
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const currentTime = Math.floor(Date.now() / 1000);
      return payload.exp > currentTime;
    } catch (error) {
      console.error('Error decoding token:', error);
      return false;
    }
  }

  getUserData(): User | null {
    const userData = authStorage.getItem(this.USER_KEY);
    return userData ? JSON.parse(userData) : null;
  }


}

export default new AuthService();