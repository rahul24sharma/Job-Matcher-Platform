// src/hooks/useProfile.ts

import { useState, useEffect, useCallback } from 'react';
import toast from 'react-hot-toast';
import { profileApi } from '../api/profile.api';
import type { 
  Profile, 
  ProfileUpdatePayload, 
  ProfileStats,
} from '../types/profile.types';

export const useProfile = () => {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [stats, setStats] = useState<ProfileStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchProfile = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await profileApi.getMyProfile();
      setProfile(data);
      return data;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to load profile';
      setError(errorMessage);
      toast.error(errorMessage);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchStats = useCallback(async () => {
    try {
      const data = await profileApi.getProfileStats();
      setStats(data);
      return data;
    } catch (err) {
      console.error('Failed to fetch profile stats:', err);
      return null;
    }
  }, []);

  const updateProfile = useCallback(async (payload: ProfileUpdatePayload) => {
    setUpdating(true);
    setError(null);
    try {
      const data = await profileApi.updateProfile(payload);
      setProfile(data);
      toast.success('Profile updated successfully!');
      return data;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to update profile';
      setError(errorMessage);
      toast.error(errorMessage);
      throw err;
    } finally {
      setUpdating(false);
    }
  }, []);

  const addSkills = useCallback(async (skills: string[]) => {
    try {
      const data = await profileApi.addSkills(skills);
      setProfile(data);
      toast.success(`Added ${skills.length} skill(s)`);
      return data;
    } catch (err: any) {
      toast.error('Failed to add skills');
      throw err;
    }
  }, []);

  const removeSkill = useCallback(async (skill: string) => {
    try {
      await profileApi.removeSkill(skill);
      if (profile) {
        setProfile({
          ...profile,
          skills: profile.skills.filter(s => s !== skill)
        });
      }
      toast.success(`Removed skill: ${skill}`);
    } catch (err) {
      toast.error('Failed to remove skill');
      throw err;
    }
  }, [profile]);

  const deleteProfile = useCallback(async () => {
    try {
      await profileApi.deleteProfile();
      setProfile(null);
      toast.success('Profile deleted successfully');
    } catch (err) {
      toast.error('Failed to delete profile');
      throw err;
    }
  }, []);

  const getCompletionItems = useCallback(() => {
    if (!profile) return [];

    return [
      { field: 'full_name', label: 'Full Name', completed: !!profile.full_name },
      { field: 'phone', label: 'Phone', completed: !!profile.phone },
      { field: 'location', label: 'Location', completed: !!profile.location },
      { field: 'title', label: 'Job Title', completed: !!profile.title },
      { field: 'bio', label: 'Bio', completed: !!profile.bio },
      { field: 'skills', label: 'Skills', completed: profile.skills.length > 0 },
      { field: 'resume', label: 'Resume', completed: !!profile.resume_uploaded_at },
      { field: 'github', label: 'GitHub', completed: !!profile.github_username },
    ];
  }, [profile]);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  return {
    profile,
    stats,
    loading,
    updating,
    error,
    fetchProfile,
    fetchStats,
    updateProfile,
    addSkills,
    removeSkill,
    deleteProfile,
    getCompletionItems,
  };
};