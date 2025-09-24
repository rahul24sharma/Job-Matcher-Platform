import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { jobsApi } from '../../api/jobs.api';

export const JobExplore: React.FC = () => {
  const { data: jobs, isLoading, isError } = useQuery({
    queryKey: ['jobs'],
    queryFn: async () => {
      try {
        const response = await jobsApi.list();
        return response;
      } catch (error) {
        throw new Error('Failed to fetch jobs');
      }
    },
  });
  
  if (isLoading) return <div className="text-white">Loading jobs...</div>;
  if (isError) return <div className="text-red-400">Error loading jobs</div>;
  if (!jobs || jobs.length === 0) return <div className="text-white">No jobs found</div>;
  
  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold text-white mb-6">Job Explorer</h1>
      
      <div className="grid gap-4">
        {jobs.map((job) => (
          <div key={job.id} className="bg-white/10 border border-white/20 rounded-xl p-6 hover:bg-white/5 transition-colors">
            {/* Job Header */}
            <div className="mb-4">
              <h2 className="text-xl font-semibold text-white mb-2">{job.title || 'No title'}</h2>
              
              <div className="flex flex-wrap items-center gap-2 text-sm">
                {job.company && (
                  <span className="text-blue-300 font-medium">{job.company}</span>
                )}
                {job.company && job.location && <span className="text-gray-500">•</span>}
                {job.location && (
                  <span className="text-gray-300">{job.location}</span>
                )}
                {job.remote && (
                  <>
                    <span className="text-gray-500">•</span>
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-900/50 text-green-300 border border-green-800">
                      Remote
                    </span>
                  </>
                )}
              </div>
              
              {/* Salary Range */}
              {(job.salary_min || job.salary_max) && (
                <div className="mt-2 text-emerald-400 font-medium">
                  💰 {job.salary_min ? `$${job.salary_min.toLocaleString()}` : ''}
                  {job.salary_min && job.salary_max ? ' - ' : ''}
                  {job.salary_max ? `$${job.salary_max.toLocaleString()}` : ''}
                  {/* {job.salary_currency && <span className="text-gray-400 text-sm ml-1">{job.salary_currency}</span>} */}
                </div>
              )}
            </div>
            
            {/* Job Description - Rendered HTML with Tailwind prose classes */}
            {job.description && (
              <div 
                className="prose prose-sm prose-invert max-w-none mb-4
                  prose-p:text-gray-300 prose-p:mb-3
                  prose-strong:text-white prose-strong:font-semibold
                  prose-ul:text-gray-300 prose-ul:my-3 prose-ul:list-disc prose-ul:pl-5
                  prose-ol:text-gray-300 prose-ol:my-3 prose-ol:list-decimal prose-ol:pl-5
                  prose-li:text-gray-300 prose-li:mb-1
                  prose-h1:text-white prose-h1:text-lg prose-h1:font-bold prose-h1:mt-4 prose-h1:mb-2
                  prose-h2:text-white prose-h2:text-lg prose-h2:font-bold prose-h2:mt-4 prose-h2:mb-2
                  prose-h3:text-white prose-h3:text-base prose-h3:font-semibold prose-h3:mt-3 prose-h3:mb-2
                  prose-a:text-blue-400 prose-a:underline hover:prose-a:text-blue-300
                  prose-blockquote:border-l-4 prose-blockquote:border-gray-600 prose-blockquote:pl-4 prose-blockquote:italic prose-blockquote:text-gray-400
                  prose-code:bg-gray-800 prose-code:text-gray-300 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-sm
                  prose-pre:bg-gray-900 prose-pre:text-gray-300 prose-pre:p-4 prose-pre:rounded-lg prose-pre:overflow-x-auto
                  prose-img:hidden"
                dangerouslySetInnerHTML={{ 
                  __html: job.description
                    // Remove script tags and event handlers for security
                    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
                    .replace(/on\w+="[^"]*"/gi, '')
                    .replace(/on\w+='[^']*'/gi, '')
                    // Hide tracking pixels
                    .replace(/<img[^>]*src="[^"]*blank\.gif[^"]*"[^>]*>/gi, '')
                }}
              />
            )}
            
            {/* Action Button */}
            <div className="mt-4 pt-4 border-t border-white/10">
              {job.url ? (
                <a
                  href={job.url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-medium transition-colors"
                >
                  <span className='text-white'>View Job</span>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </a>
              ) : (
                <span className="text-gray-400 text-sm">No external URL available</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};