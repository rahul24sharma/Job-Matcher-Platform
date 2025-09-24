import apiClient from './client';
import type { AuthResponse, LoginCredentials, RegisterCredentials, User } from '../types/auth.types';

export const authApi = {
  // LOGIN: send x-www-form-urlencoded with username+password
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const body = new URLSearchParams();
    body.set('username', credentials.email);   // OAuth2PasswordRequestForm expects 'username'
    body.set('password', credentials.password);

    const response = await apiClient.post('api/v1/auth/login', body, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return response.data;
  },

  register: async (credentials: RegisterCredentials): Promise<User> => {
    const response = await apiClient.post('api/v1/auth/register', credentials);
    return response.data;
  },

  getMe: async (): Promise<User> => {
    const response = await apiClient.get('api/v1/auth/me');
    return response.data;
  },
};
