// import apiClient from "./client";

// export type Profile = {
//     id: number;
//     email: string;
//     name?: string;
//     is_active: boolean;
//     phone?: string;
//     location?: string;
//     title?: string;
//     bio?: string;
//     linkedin?: string;
//     portfolio?: string;
//   };
  
//   export type UpdateProfilePayload = Partial<
//     Omit<Profile, 'id' | 'email' | 'is_active'>
//   >;
  
//   export const profileApi = {
//     getMe: async (): Promise<Profile> => {
//       const { data } = await apiClient.get('/auth/me');
//       return data;
//     },
//     // NOTE: change this path if your backend uses a different one
//     updateMe: async (payload: UpdateProfilePayload): Promise<Profile> => {
//       const { data } = await apiClient.patch('/users/me', payload);
//       return data;
//     },
//   };
  

// src/api/profile.api.ts

// src/api/profile.api.ts

import apiClient from "./client";
import type { 
  Profile, 
  ProfileUpdatePayload, 
  ProfileStats, 
  PublicProfile,
  SkillsPayload 
} from '../types/profile.types';

export const profileApi = {
  getMyProfile: async (): Promise<Profile> => {
    const { data } = await apiClient.get('/profile/me');
    return data;
  },

  updateProfile: async (payload: ProfileUpdatePayload): Promise<Profile> => {
    const { data } = await apiClient.put('/profile/me', payload);
    return data;
  },

  addSkills: async (skills: string[]): Promise<Profile> => {
    const payload: SkillsPayload = { skills };
    const { data } = await apiClient.post('/profile/skills', payload);
    return data;
  },

  removeSkill: async (skill: string): Promise<{ message: string }> => {
    const { data } = await apiClient.delete(`/profile/skills/${encodeURIComponent(skill)}`);
    return data;
  },

  getProfileStats: async (): Promise<ProfileStats> => {
    const { data } = await apiClient.get('/profile/stats');
    return data;
  },

  getUserProfile: async (userId: number): Promise<PublicProfile> => {
    const { data } = await apiClient.get(`/profile/user/${userId}`);
    return data;
  },

  deleteProfile: async (): Promise<{ message: string }> => {
    const { data } = await apiClient.delete('profile/me');
    return data;
  },
};