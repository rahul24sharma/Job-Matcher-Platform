// src/api/resume.api.ts
import apiClient from './client';

export type UploadResumeResponse = {
  message: string;
  skills?: string[];
  user: string;
};

export const resumeApi = {
  upload: async (file: File): Promise<UploadResumeResponse> => {
    const form = new FormData();
    form.append('file', file);

    const { data } = await apiClient.post('api/v1/resume/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },
};
