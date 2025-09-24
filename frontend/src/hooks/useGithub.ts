import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { githubApi } from '../api/github.api';
import toast from 'react-hot-toast';

export function useGithub() {
  const qc = useQueryClient();

  const skillsQ = useQuery({
    queryKey: ['github', 'skills'],
    queryFn: githubApi.skills,
  });

  const profileQ = useQuery({
    queryKey: ['github', 'profile'],
    queryFn: githubApi.profile,
    // avoid refetch loop when not connected
    enabled: !!(skillsQ.data && skillsQ.data.github_username),
  });

  const connectM = useMutation({
    mutationFn: (username: string) => githubApi.connect(username),
    onSuccess: (res) => {
      toast.success(res.message || 'GitHub connected');
      qc.invalidateQueries({ queryKey: ['github'] });
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.detail || 'Failed to connect GitHub';
      toast.error(msg);
    },
  });

  const analyzeM = useMutation({
    mutationFn: githubApi.analyze,
    onSuccess: () => {
      toast.success('GitHub analysis complete');
      qc.invalidateQueries({ queryKey: ['github'] });
    },
    onError: () => toast.error('Failed to analyze GitHub'),
  });

  const disconnectM = useMutation({
    mutationFn: githubApi.disconnect,
    onSuccess: (res) => {
      toast.success(res.message || 'Disconnected');
      qc.invalidateQueries({ queryKey: ['github'] });
    },
    onError: () => toast.error('Failed to disconnect'),
  });

  const connected = !!skillsQ.data?.github_username;

  return {
    connected,
    skillsQ,
    profileQ,
    connectM,
    analyzeM,
    disconnectM,
  };
}
