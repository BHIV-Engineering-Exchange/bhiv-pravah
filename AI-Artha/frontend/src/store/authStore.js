import { create } from 'zustand';
import api, { AUTH_TOKEN_KEY } from '../services/api';

export const useAuthStore = create((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,

  setLoading: (loading) => set({ isLoading: loading }),

  checkAuth: async () => {
    try {
      if (typeof window !== 'undefined' && !localStorage.getItem(AUTH_TOKEN_KEY)) {
        set({
          user: null,
          isAuthenticated: false,
          isLoading: false,
        });
        return;
      }
      const response = await api.get('/auth/me');
      set({
        user: response.data?.data || null,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch {
      set({
        user: null,
        isAuthenticated: false,
        isLoading: false,
      });
    }
  },

  logout: () => {
    try {
      localStorage.removeItem(AUTH_TOKEN_KEY);
    } catch {
      /* ignore */
    }
    set({ user: null, isAuthenticated: false, isLoading: false });
    window.location.href = '/login';
  },

  updateUser: (userData) => {
    set((state) => ({
      user: { ...state.user, ...userData },
    }));
  },
}));
