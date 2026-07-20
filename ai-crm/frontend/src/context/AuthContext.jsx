import React, { createContext, useState, useContext, useEffect } from 'react';
import { authService } from '@/services/auth/authService';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Initialize auth from localStorage token
    const initializeAuth = async () => {
      try {
        const token = localStorage.getItem('token');
        if (token) {
          // Verify token and get user info from backend
          const currentUser = await authService.getCurrentUser();
          if (currentUser) {
            setUser(currentUser);
            setSession({ access_token: token });
          } else {
            // Invalid token, clear it
            localStorage.removeItem('token');
          }
        }
      } catch (error) {
        console.error('Error initializing auth:', error);
        localStorage.removeItem('token');
      } finally {
        setLoading(false);
      }
    };

    initializeAuth();
  }, []);

  const login = async (email, password) => {
    setLoading(true);
    try {
      const result = await authService.signIn({ email, password });
      
      const signedInUser = result?.user;
      const newSession = result?.session;
      
      if (signedInUser && newSession?.access_token) {
        setUser(signedInUser);
        setSession(newSession);
        localStorage.setItem('token', newSession.access_token);
      }
      
      return { user: signedInUser, session: newSession };
    } catch (error) {
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const signup = async ({ email, password, firstName, lastName, companyName }) => {
    setLoading(true);
    try {
      const data = await authService.signUp({
        email,
        password,
        firstName,
        lastName,
        companyName
      });
      
      // Automatically log in after signup
      if (data.user && data.session?.access_token) {
        setUser(data.user);
        setSession(data.session);
        localStorage.setItem('token', data.session.access_token);
      }
      
      return data;
    } catch (error) {
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const loginWithOAuth = async (provider) => {
    throw new Error('OAuth login is not available');
  };

  const logout = async () => {
    setLoading(true);
    try {
      await authService.signOut();
      setUser(null);
      setSession(null);
      localStorage.removeItem('token');
    } catch (error) {
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const resetPassword = async (email) => {
    try {
      await authService.resetPassword(email);
    } catch (error) {
      throw error;
    }
  };

  const updatePassword = async (newPassword) => {
    try {
      await authService.updatePassword(newPassword);
    } catch (error) {
      throw error;
    }
  };

  const updateProfile = async (updates) => {
    if (!user) return;
    try {
      const updatedProfile = await authService.updateUserProfile(user.id, updates);
      return updatedProfile;
    } catch (error) {
      throw error;
    }
  };

  const value = {
    user,
    session,
    profile: null, // Profile management removed
    loading,
    isAuthenticated: !!user,
    login,
    signup,
    loginWithOAuth,
    logout,
    resetPassword,
    updatePassword,
    updateProfile
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
