// src/types/profile.types.ts

export interface Profile {
    id: number;
    user_id: number;
    email?: string;
    full_name?: string;
    phone?: string;
    location?: string;
    title?: string;
    bio?: string;
    linkedin_url?: string;
    portfolio_url?: string;
    github_username?: string;
    skills: string[];
    resume_path?: string;
    resume_uploaded_at?: string | Date;
    is_complete: boolean;
    completion_percentage: number;
    created_at: string | Date;
    updated_at?: string | Date;
  }
  
  export interface ProfileUpdatePayload {
    full_name?: string;
    phone?: string;
    location?: string;
    title?: string;
    bio?: string;
    linkedin_url?: string;
    portfolio_url?: string;
    github_username?: string;
  }
  
  export interface ProfileCreatePayload extends ProfileUpdatePayload {
    user_id?: number;
  }
  
  export interface ProfileStats {
    profile_completion: number;
    total_skills: number;
    has_resume: boolean;
    has_github: boolean;
    last_updated?: string | Date;
    profile_views?: number;
  }
  
  export interface PublicProfile {
    full_name?: string;
    title?: string;
    bio?: string;
    location?: string;
    skills: string[];
    linkedin_url?: string;
    portfolio_url?: string;
    github_username?: string;
  }
  
  export interface SkillsPayload {
    skills: string[];
  }
  
  export interface ProfileResponse {
    profile: Profile;
    message?: string;
  }
  
  export interface ProfileField {
    label: string;
    key: keyof ProfileUpdatePayload | 'email';
    type: 'text' | 'email' | 'tel' | 'url' | 'textarea';
    icon?: any;
    placeholder?: string;
    required?: boolean;
    disabled?: boolean;
    pattern?: string;
    title?: string;
    maxLength?: number;
    validate?: (value: string) => boolean;
    errorMessage?: string;
  }
  
  export interface ProfileCompletionItem {
    field: keyof Profile;
    label: string;
    weight: number;
    completed: boolean;
  }
  
  export interface ProfileValidationError {
    field: keyof ProfileUpdatePayload;
    message: string;
  }
  
  export interface ProfileFormData extends ProfileUpdatePayload {
    email: string;
  }
  
  // Enums for profile-related constants
  export enum ProfileCompletionWeight {
    FULL_NAME = 10,
    PHONE = 10,
    LOCATION = 10,
    TITLE = 15,
    BIO = 15,
    LINKEDIN = 10,
    PORTFOLIO = 10,
    RESUME = 10,
    GITHUB = 5,
    SKILLS = 5,
  }
  
  export enum ProfileStatus {
    INCOMPLETE = 'incomplete',
    PARTIAL = 'partial',
    COMPLETE = 'complete',
  }
  
  // Type guards
  export function isProfile(obj: any): obj is Profile {
    return (
      typeof obj === 'object' &&
      obj !== null &&
      'id' in obj &&
      'user_id' in obj &&
      'completion_percentage' in obj
    );
  }
  
  export function isPublicProfile(obj: any): obj is PublicProfile {
    return (
      typeof obj === 'object' &&
      obj !== null &&
      Array.isArray(obj.skills)
    );
  }
  
  // Utility types
  export type ProfileFields = keyof ProfileUpdatePayload;
  export type RequiredProfileFields = 'full_name' | 'title';
  export type OptionalProfileFields = Exclude<ProfileFields, RequiredProfileFields>;