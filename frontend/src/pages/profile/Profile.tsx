// src/pages/Profile.tsx

import React, { useState, useEffect } from 'react';
import { User, Mail, Phone, MapPin, Briefcase, Link, Edit2, Save, Loader2, Check, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import { profileApi } from '../../api/profile.api';
import { authApi } from '../../api/auth.api';
import type { 
  Profile, 
  ProfileFormData, 
  ProfileField,
  ProfileUpdatePayload 
} from '../../types/profile.types';
import type { AxiosError } from 'axios';

interface ErrorResponse {
  detail?: string;
  message?: string;
}

const Profile: React.FC = () => {
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [saving, setSaving] = useState<boolean>(false);
  const [profile, setProfile] = useState<Profile | null>(null);
  
  // Initialize with empty strings to avoid undefined issues
  const [formData, setFormData] = useState<ProfileFormData>({
    full_name: '',
    email: '',
    phone: '',
    location: '',
    title: '',
    bio: '',
    linkedin_url: '',
    portfolio_url: ''
  });

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async (): Promise<void> => {
    setLoading(true);
    try {
      const profileData = await profileApi.getMyProfile();
      
      setFormData({
        full_name: profileData.full_name || '',
        email: profileData.email || '',
        phone: profileData.phone || '',
        location: profileData.location || '',
        title: profileData.title || '',
        bio: profileData.bio || '',
        linkedin_url: profileData.linkedin_url || '',
        portfolio_url: profileData.portfolio_url || ''
      });
      
      setProfile(profileData);
    } catch (error) {
      console.error('Error fetching profile:', error);
      
      try {
        const userData = await authApi.getMe();
        setFormData(prev => ({
          ...prev,
          email: userData.email || '',
          full_name: userData.full_name || ''
        }));
      } catch (userError) {
        toast.error('Failed to load profile information');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (): Promise<void> => {
    setSaving(true);
    try {
      const updatePayload: ProfileUpdatePayload = {
        full_name: formData.full_name || undefined,
        phone: formData.phone || undefined,
        location: formData.location || undefined,
        title: formData.title || undefined,
        bio: formData.bio || undefined,
        linkedin_url: formData.linkedin_url || undefined,
        portfolio_url: formData.portfolio_url || undefined
      };

      // Remove undefined values
      Object.keys(updatePayload).forEach(key => {
        if (updatePayload[key as keyof ProfileUpdatePayload] === undefined) {
          delete updatePayload[key as keyof ProfileUpdatePayload];
        }
      });

      const updatedProfile = await profileApi.updateProfile(updatePayload);
      setProfile(updatedProfile);
      setIsEditing(false);
      toast.success('Profile updated successfully!');
    } catch (error) {
      console.error('Error updating profile:', error);
      const axiosError = error as AxiosError<ErrorResponse>;
      const errorMessage = axiosError.response?.data?.detail || 
                          axiosError.response?.data?.message || 
                          'Failed to update profile';
      toast.error(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = (): void => {
    if (profile) {
      setFormData({
        full_name: profile.full_name || '',
        email: profile.email || '',
        phone: profile.phone || '',
        location: profile.location || '',
        title: profile.title || '',
        bio: profile.bio || '',
        linkedin_url: profile.linkedin_url || '',
        portfolio_url: profile.portfolio_url || ''
      });
    }
    setIsEditing(false);
  };

  const handleChange = (field: keyof ProfileFormData, value: string): void => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const validateUrl = (url: string): boolean => {
    if (!url) return true;
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  };

  // Helper function to safely get form field value
  const getFieldValue = (key: keyof ProfileFormData): string => {
    return formData[key] || '';
  };

  const fields: ProfileField[] = [
    { 
      label: 'Full Name', 
      key: 'full_name', 
      type: 'text', 
      icon: User, 
      placeholder: 'John Doe',
      required: false 
    },
    { 
      label: 'Email', 
      key: 'email', 
      type: 'email', 
      icon: Mail, 
      placeholder: 'john@example.com',
      disabled: true
    },
    { 
      label: 'Phone', 
      key: 'phone', 
      type: 'tel', 
      icon: Phone, 
      placeholder: '+1 234 567 8900',
      pattern: '[+]?[0-9\\s\\-()]+',
      title: 'Please enter a valid phone number'
    },
    { 
      label: 'Location', 
      key: 'location', 
      type: 'text', 
      icon: MapPin, 
      placeholder: 'San Francisco, CA' 
    },
    { 
      label: 'Job Title', 
      key: 'title', 
      type: 'text', 
      icon: Briefcase, 
      placeholder: 'Full Stack Developer' 
    },
    { 
      label: 'LinkedIn', 
      key: 'linkedin_url', 
      type: 'url', 
      icon: Link, 
      placeholder: 'https://linkedin.com/in/johndoe',
      validate: validateUrl,
      errorMessage: 'Please enter a valid URL'
    },
    { 
      label: 'Portfolio', 
      key: 'portfolio_url', 
      type: 'url', 
      icon: Link, 
      placeholder: 'https://johndoe.dev',
      validate: validateUrl,
      errorMessage: 'Please enter a valid URL'
    }
  ];

  if (loading) {
    return (
      <div className="min-h-screen p-6 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-12 w-12 text-blue-400 animate-spin" />
          <p className="text-white text-lg">Loading profile...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-6">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold text-white mb-8 flex items-center gap-3">
          <User className="text-blue-400" />
          Profile Information
        </h1>

        <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-2xl font-semibold text-white">Personal Details</h2>
              {profile && (
                <p className="text-gray-400 text-sm mt-1">
                  Profile completion: {profile.completion_percentage}%
                </p>
              )}
            </div>
            <div className="flex gap-2">
              {isEditing ? (
                <>
                  <button
                    onClick={handleCancel}
                    className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors disabled:opacity-50"
                  >
                    {saving ? (
                      <Loader2 size={18} className="animate-spin" />
                    ) : (
                      <Save size={18} />
                    )}
                    {saving ? 'Saving...' : 'Save Changes'}
                  </button>
                </>
              ) : (
                <button
                  onClick={() => setIsEditing(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
                >
                  <Edit2 size={18} />
                  Edit Profile
                </button>
              )}
            </div>
          </div>

          {profile && profile.completion_percentage < 100 && (
            <div className="mb-6">
              <div className="w-full bg-white/10 rounded-full h-2">
                <div 
                  className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${profile.completion_percentage}%` }}
                />
              </div>
            </div>
          )}

          <div className="space-y-4">
            {fields.map(field => {
              const Icon = field.icon;
              const fieldKey = field.key as keyof ProfileFormData;
              const fieldValue = getFieldValue(fieldKey); // FIX: Use helper function
              const hasError = field.validate ? !field.validate(fieldValue) : false; // FIX: Pass string value
              
              return (
                <div key={field.key}>
                  <label className="text-gray-300 text-sm mb-1 flex items-center gap-2">
                    <Icon size={16} />
                    {field.label}
                    {field.required && <span className="text-red-400">*</span>}
                  </label>
                  <input
                    type={field.type}
                    value={fieldValue} // FIX: Use the safe string value
                    onChange={(e) => handleChange(fieldKey, e.target.value)}
                    disabled={!isEditing || field.disabled}
                    pattern={field.pattern}
                    title={field.title}
                    className={`w-full px-4 py-2 bg-white/10 border ${
                      hasError && isEditing ? 'border-red-500' : 'border-white/20'
                    } rounded-lg text-white placeholder-gray-400 disabled:opacity-50 focus:outline-none focus:border-blue-400 transition-colors`}
                    placeholder={field.placeholder}
                  />
                  {hasError && isEditing && field.errorMessage && (
                    <p className="text-red-400 text-sm mt-1">{field.errorMessage}</p>
                  )}
                </div>
              );
            })}

            <div>
              <label className="text-gray-300 text-sm mb-1 block">Bio</label>
              <textarea
                value={getFieldValue('bio')} // FIX: Use helper function
                onChange={(e) => handleChange('bio', e.target.value)}
                disabled={!isEditing}
                rows={4}
                maxLength={500}
                className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 disabled:opacity-50 focus:outline-none focus:border-blue-400 transition-colors resize-none"
                placeholder="Tell us about yourself..."
              />
              {isEditing && (
                <p className="text-gray-400 text-xs mt-1 text-right">
                  {getFieldValue('bio').length}/500 characters {/* FIX: Use helper function */}
                </p>
              )}
            </div>
          </div>

          {profile && (
            <div className="mt-6 pt-6 border-t border-white/20">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <p className="text-gray-400 text-sm">Skills</p>
                  <p className="text-white text-xl font-bold">{profile.skills?.length || 0}</p>
                </div>
                <div className="text-center">
                  <p className="text-gray-400 text-sm">Resume</p>
                  <div className="text-white text-xl font-bold">
                    {profile.resume_uploaded_at ? (
                      <Check className="inline h-5 w-5 text-green-400" />
                    ) : (
                      <AlertCircle className="inline h-5 w-5 text-gray-400" />
                    )}
                  </div>
                </div>
                <div className="text-center">
                  <p className="text-gray-400 text-sm">GitHub</p>
                  <div className="text-white text-xl font-bold">
                    {profile.github_username ? (
                      <Check className="inline h-5 w-5 text-green-400" />
                    ) : (
                      <AlertCircle className="inline h-5 w-5 text-gray-400" />
                    )}
                  </div>
                </div>
                <div className="text-center">
                  <p className="text-gray-400 text-sm">Status</p>
                  <p className={`text-sm font-medium ${
                    profile.is_complete ? 'text-green-400' : 'text-yellow-400'
                  }`}>
                    {profile.is_complete ? 'Complete' : 'Incomplete'}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {profile && !profile.is_complete && (
          <div className="mt-6 bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4">
            <h3 className="text-yellow-400 font-medium mb-2">Complete Your Profile</h3>
            <ul className="text-gray-300 text-sm space-y-1">
              {!profile.resume_uploaded_at && (
                <li>• Upload your resume to extract skills</li>
              )}
              {!profile.github_username && (
                <li>• Connect your GitHub account</li>
              )}
              {(!profile.skills || profile.skills.length === 0) && (
                <li>• Add your technical skills</li>
              )}
              {!getFieldValue('bio') && ( // FIX: Use helper function
                <li>• Add a bio to introduce yourself</li>
              )}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

export default Profile;