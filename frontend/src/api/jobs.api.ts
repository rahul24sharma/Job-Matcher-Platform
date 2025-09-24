import apiClient from './client';

export type JobMatch = {
  job_id: number;
  title: string;
  company: string;
  location: string | null;
  remote: boolean;
  salary_min: number | null;
  salary_max: number | null;
  match_score: number;       // backend returns 0..100
  match_reasons: string[];
  url?: string | null;
};

export type Job = {
  id: number;
  title: string;
  company: string;
  location: string | null;
  description: string;
  required_skills: string;
  url?: string | null;
  remote: boolean;
  salary_min: number | null;
  salary_max: number | null;
  source?: string;
  created_at?: string;
  expires_at?: string;
};

export type MatchStats = {
  total_matches: number;
  average_score: number;
  top_match_score: number;
  match_distribution: Record<string, number>;
};

export const jobsApi = {
  // GET /jobs/match — compute (or return cached) fresh matches for the user
  match: async (params?: { limit?: number; min_score?: number }): Promise<JobMatch[]> => {
    const { data } = await apiClient.get('/jobs/match', { params });
    return data;
  },

  // GET /jobs/statistics
  stats: async (): Promise<MatchStats> => {
    const { data } = await apiClient.get('/jobs/statistics');
    return data;
  },

  // Browsing helpers
  list: async (params?: { skip?: number; limit?: number }): Promise<Job[]> => {
    const { data } = await apiClient.get('/jobs', { params });
    return data;
  },

  byId: async (id: number): Promise<Job> => {
    const { data } = await apiClient.get(`/jobs/${id}`);
    return data;
  },

  searchBySkills: async (skillsCsv: string) => {
    const { data } = await apiClient.get('/jobs/search/skills', { params: { skills: skillsCsv } });
    return data as {
      search_skills: string[];
      jobs_found: number;
      jobs: Array<{ id: number; title: string; company: string; required_skills: string }>;
    };
  },
};
