// src/pages/jobs/JobMatches.tsx
import React from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { jobsApi, type JobMatch } from '../../api/jobs.api';
import { RefreshCw, ExternalLink } from 'lucide-react';
import toast from 'react-hot-toast';

const Pill: React.FC<{ tone?: 'ok' | 'muted'; children: React.ReactNode }> = ({ tone, children }) => (
  <span className={`m-1 inline-flex px-2 py-0.5 rounded-full text-xs
    ${tone === 'ok' ? 'bg-green-500/15 text-green-300 border border-green-500/30'
                    : 'bg-white/10 text-gray-300 border border-white/20'}`}>
    {children}
  </span>
);

const ScoreBar: React.FC<{ value: number }> = ({ value }) => (
  <div className="h-2 w-full bg-white/10 rounded">
    <div className="h-2 rounded bg-green-500" style={{ width: `${Math.max(0, Math.min(100, value))}%` }} />
  </div>
);

const JobMatches: React.FC = () => {
  const qc = useQueryClient();

  const { data, isLoading, isFetching, refetch } = useQuery({
    queryKey: ['jobs', 'match'],
    queryFn: () => jobsApi.match(),   // GET /jobs/match (fresh or cached on server)
  });

  const refresh = async () => {
    try {
      await qc.invalidateQueries({ queryKey: ['jobs', 'match'] });
      await refetch();
      toast.success('Matches refreshed');
    } catch {
      toast.error('Failed to refresh');
    }
  };

  return (
    <div className="p-6">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-white">Job Matches</h1>
        <button
          onClick={refresh}
          disabled={isFetching}
          className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50"
        >
          {isFetching ? <RefreshCw className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
          Refresh
        </button>
      </div>

      {isLoading ? (
        <div className="text-gray-300">Finding best matches…</div>
      ) : !data?.length ? (
        <div className="text-gray-300">
          No matches yet. Make sure you uploaded a resume and/or connected GitHub with relevant projects.
        </div>
      ) : (
        <div className="grid gap-4">
          {data.map((m: JobMatch) => {
            const pct = Math.round(Math.max(0, Math.min(100, m.match_score)));
            return (
              <div key={m.job_id} className="bg-white/10 border border-white/20 rounded-xl p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="text-white">
                    <div className="text-lg font-semibold">{m.title}</div>
                    <div className="text-gray-300">
                      {m.company} • {m.location || '—'} {m.remote ? '• Remote' : ''}
                    </div>
                    {!!(m.salary_min || m.salary_max) && (
                      <div className="text-gray-400 text-sm mt-1">
                        {m.salary_min ? `$${m.salary_min.toLocaleString()}` : ''}{m.salary_min && m.salary_max ? '–' : ''}{m.salary_max ? `$${m.salary_max.toLocaleString()}` : ''}
                      </div>
                    )}
                  </div>

                  <div className="text-right min-w-[110px]">
                    <div className="text-2xl font-bold text-green-400">{pct}%</div>
                    <div className="w-28 mt-1"><ScoreBar value={pct} /></div>
                  </div>
                </div>

                {!!m.match_reasons?.length && (
                  <div className="mt-3 flex flex-wrap -m-1">
                    {m.match_reasons.map((r, i) => <Pill key={i} tone="ok">{r}</Pill>)}
                  </div>
                )}

                <div className="mt-3">
                  {m.url ? (
                    <a href={m.url} target="_blank" rel="noreferrer"
                       className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-white/10 border border-white/20 text-white hover:bg-white/20">
                      <ExternalLink className="h-4 w-4" /> View job
                    </a>
                  ) : (
                    <span className="text-gray-400 text-sm">No external URL</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default JobMatches;
