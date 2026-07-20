import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';
import { jwtDecode } from 'jwt-decode';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('token');
    const storedUser = localStorage.getItem('user');
    
    if (token && storedUser) {
      try {
        const decoded = jwtDecode(token);
        // Check if token is expired
        if (decoded.exp * 1000 > Date.now()) {
          const userData = JSON.parse(storedUser);
          // Ensure session_id is available (extract from token if missing)
          if (!userData.session_id) {
            userData.session_id = decoded.session_id || decoded.jti || null;
            if (userData.session_id) {
              sessionStorage.setItem('session_id', userData.session_id);
            }
          }
          
          // Fetch fresh user details if email/name is missing
          if (!userData.email || !userData.name) {
            authAPI.getMe()
              .then(meResponse => {
                const updatedUserData = {
                  ...userData,
                  email: meResponse.email || userData.email,
                  name: meResponse.name || userData.name,
                };
                localStorage.setItem('user', JSON.stringify(updatedUserData));
                setUser(updatedUserData);
                window.EMSUserContext = updatedUserData;
              })
              .catch(() => {
                // If /me fails, use stored data
                setUser(userData);
                window.EMSUserContext = userData;
              });
          } else {
            setUser(userData);
            // Update window context
            window.EMSUserContext = userData;
          }
        } else {
          // Token expired, clear it
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          sessionStorage.removeItem('session_id');
        }
      } catch (error) {
        console.error('Error decoding token:', error);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        sessionStorage.removeItem('session_id');
      }
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    try {
      const response = await authAPI.login(email, password);
      const { access_token } = response;
      
      // Decode token to get user info
      const decoded = jwtDecode(access_token);
      
      // Fetch full user details including email and name
      let userDetails = {
        id: decoded.sub,
        role: decoded.role,
        school_id: decoded.school_id,
        session_id: decoded.session_id || decoded.jti || null,
        email: email, // Store email from login input as fallback
      };
      
      // Try to fetch full user details from /me endpoint
      try {
        const meResponse = await authAPI.getMe();
        userDetails = {
          ...userDetails,
          email: meResponse.email,
          name: meResponse.name,
        };
      } catch (meError) {
        // If /me fails, use email from login input
        console.warn('Failed to fetch user details, using email from login:', meError);
      }
      
      // Store token and user data
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(userDetails));
      
      // Store session_id separately for PRANA
      if (userDetails.session_id) {
        sessionStorage.setItem('session_id', userDetails.session_id);
      }
      
      setUser(userDetails);
      // Expose minimal context for PRANA-E (actor id + role + school + session_id)
      window.EMSUserContext = userDetails;
      return { success: true };
    } catch (error) {
      console.error('Login error:', error);
      // Extract error message properly
      let errorMessage = 'Login failed. Please check your credentials.';
      if (error.response?.data?.detail) {
        errorMessage = typeof error.response.data.detail === 'string' 
          ? error.response.data.detail 
          : JSON.stringify(error.response.data.detail);
      } else if (error.message) {
        errorMessage = error.message;
      }
      return {
        success: false,
        message: errorMessage,
      };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    sessionStorage.removeItem('session_id');
    setUser(null);
    window.EMSUserContext = null;
  };

  const value = {
    user,
    login,
    logout,
    loading,
    isAuthenticated: !!user,
    isSuperAdmin: user?.role === 'SUPER_ADMIN',
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
