import apiClient from './client';

export type GitHubConnectRequest = { username: string };

export type GitHubProfileResponse = {
  username: string;
  profile: Record<string, any>;         
  languages: Record<string, number>;     
  skills: string[];
  top_repositories: Array<Record<string, any>>;
  activity_score: number;
  total_stars: number;
  total_forks: number;
};

export const githubApi = {
  connect: async (username: string) => {
    const { data } = await apiClient.post('/github/connect', { username } as GitHubConnectRequest);
    return data as { message: string; data?: any };
  },
  profile: async () => {
    const { data } = await apiClient.get('/github/profile');
    return data as GitHubProfileResponse | null; // null if not connected
  },
  analyze: async () => {
    const { data } = await apiClient.post('/github/analyze');
    return data as GitHubProfileResponse;
  },
  skills: async () => {
    const { data } = await apiClient.get('/github/skills');
    return data as { skills: string[]; total: number; github_username: string | null };
  },
  allSkills: async () => {
    const { data } = await apiClient.get('/github/all-skills');
    return data as {
      resume_skills: string[];
      github_skills: string[];
      common_skills: string[];
      all_skills: string[];
      total_unique: number;
      stats: { resume_only: number; github_only: number; both: number };
    };
  },
  disconnect: async () => {
    const { data } = await apiClient.delete('/github/disconnect');
    return data as { message: string };
  },
};
