import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type {  LoginCredentials, RegisterCredentials, User } from '../types';
import { authApi } from '../api/auth.api';
import { TOKEN_KEY } from '../config/constants';
import toast from 'react-hot-toast';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (credentials: RegisterCredentials) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
  setUser: (user: User) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()(
  devtools(
    persist(
      (set, get) => ({
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,

        login: async (credentials: LoginCredentials) => {
          set({ isLoading: true });
          try {
            const response = await authApi.login(credentials);
            const { access_token } = response;
            
            localStorage.setItem(TOKEN_KEY, access_token);
            
            const userData = await authApi.getMe();
            
            set({
              token: access_token,
              user: userData,
              isAuthenticated: true,
              isLoading: false,
            });
            
            toast.success('Login successful!');
          } catch (error: any) {
            set({ isLoading: false });
            const errorMessage = error.response?.data?.detail || 'Login failed';
            toast.error(errorMessage);
            throw error;
          }
        },

        register: async (credentials: RegisterCredentials) => {
          set({ isLoading: true });
          try {
            await authApi.register(credentials);
            toast.success('Registration successful! Please login.');
            set({ isLoading: false });
          } catch (error: any) {
            set({ isLoading: false });
            const errorMessage = error.response?.data?.detail || 'Registration failed';
            toast.error(errorMessage);
            throw error;
          }
        },

        logout: () => {
          localStorage.removeItem(TOKEN_KEY);
          set({
            user: null,
            token: null,
            isAuthenticated: false,
          });
          toast.success('Logged out successfully');
        },

        checkAuth: async () => {
          const token = localStorage.getItem(TOKEN_KEY);
          if (!token) {
            set({ isAuthenticated: false, user: null, token: null });
            return;
          }
          
          try {
            const user = await authApi.getMe();
            set({
              user,
              token,
              isAuthenticated: true,
            });
          } catch (error) {
            get().clearAuth();
          }
        },

        setUser: (user: User) => {
          set({ user });
        },

        clearAuth: () => {
          localStorage.removeItem(TOKEN_KEY);
          set({
            user: null,
            token: null,
            isAuthenticated: false,
          });
        },
      }),
      {
        name: 'auth-storage',
        partialize: (state) => ({ 
          user: state.user,
          token: state.token,
          isAuthenticated: state.isAuthenticated 
        }),
      }
    )
  )
);