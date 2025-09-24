import React, { useMemo, useState } from 'react';
import { useGithub } from '../../hooks/useGithub';
import { Github, Link, RefreshCw, LogOut, Loader2 } from 'lucide-react';

const pct = (part: number, total: number) => (total ? Math.round((part / total) * 100) : 0);

const Chip: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <span className="m-1 inline-flex px-3 py-1 bg-blue-500/10 border border-blue-400/30 rounded-full text-blue-200 text-sm">
    {children}
  </span>
);

const GitHubPage: React.FC = () => {
  const { connected, skillsQ, profileQ, connectM, analyzeM, disconnectM } = useGithub();
  const [username, setUsername] = useState('');

  const langs = profileQ.data?.languages || {};
  const totalLangBytes = useMemo(
    () => Object.values(langs).reduce((a, b) => a + (b || 0), 0),
    [langs]
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-slate-900 to-indigo-900 p-6">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-3xl font-bold text-white flex items-center gap-3 mb-6">
          <Github className="text-green-400" /> GitHub Integration
        </h1>

        {!connected && (
          <div className="bg-white/10 border border-white/20 rounded-xl p-6 mb-8">
            <h2 className="text-white text-xl mb-3">Connect your GitHub</h2>
            <p className="text-gray-300 mb-4">
              Enter your GitHub username to analyze your profile, languages, and repositories.
            </p>
            <div className="flex flex-col sm:flex-row gap-3">
              <input
                className="flex-1 px-4 py-2 rounded-lg bg-white/10 border border-white/20 text-white placeholder-gray-400 focus:outline-none focus:border-green-400"
                placeholder="e.g. torvalds"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
              <button
                onClick={() => connectM.mutate(username.trim())}
                disabled={!username || connectM.isPending}
                className="px-4 py-2 rounded-lg bg-green-600 hover:bg-green-700 text-white disabled:opacity-50"
              >
                {connectM.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Connect'}
              </button>
            </div>
          </div>
        )}

        {connected && (
          <div className="space-y-8">
            {/* Controls */}
            <div className="flex flex-wrap gap-3">
              <a
                href={`https://github.com/${skillsQ.data?.github_username ?? ''}`}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-white/10 border border-white/20 text-white hover:bg-white/20"
              >
                <Link size={16} /> View on GitHub
              </a>
              <button
                onClick={() => analyzeM.mutate()}
                disabled={analyzeM.isPending}
                className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50"
              >
                {analyzeM.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw size={16} />}
                Re-analyze
              </button>
              <button
                onClick={() => disconnectM.mutate()}
                disabled={disconnectM.isPending}
                className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white disabled:opacity-50"
              >
                {disconnectM.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <LogOut size={16} />}
                Disconnect
              </button>
            </div>

            {/* Profile + Stats */}
            <div className="grid md:grid-cols-2 gap-6">
              <div className="bg-white/10 border border-white/20 rounded-xl p-6">
                <h3 className="text-white text-lg mb-4">Profile</h3>
                {profileQ.isLoading ? (
                  <div className="text-gray-300">Loading…</div>
                ) : profileQ.data ? (
                  <div className="flex gap-4 items-center">
                    {profileQ.data.profile?.avatar_url && (
                      <img
                        src={profileQ.data.profile.avatar_url}
                        alt="avatar"
                        className="w-16 h-16 rounded-full border border-white/30"
                      />
                    )}
                    <div className="text-white">
                      <div className="text-xl font-semibold">
                        {profileQ.data.profile?.name || profileQ.data.username}
                      </div>
                      <div className="text-gray-300">@{profileQ.data.username}</div>
                      <div className="text-gray-300 mt-1">
                        ⭐ {profileQ.data.total_stars} • 🍴 {profileQ.data.total_forks} • Activity:{' '}
                        {Math.round(profileQ.data.activity_score)}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-gray-300">No profile yet.</div>
                )}
              </div>

              <div className="bg-white/10 border border-white/20 rounded-xl p-6">
                <h3 className="text-white text-lg mb-4">Top Languages</h3>
                {!profileQ.data || totalLangBytes === 0 ? (
                  <div className="text-gray-300">No language data.</div>
                ) : (
                  <div className="space-y-2">
                    {Object.entries(langs)
                      .sort((a, b) => b[1] - a[1])
                      .slice(0, 6)
                      .map(([lang, bytes]) => {
                        const p = pct(bytes, totalLangBytes);
                        return (
                          <div key={lang}>
                            <div className="flex justify-between text-sm text-gray-300 mb-1">
                              <span>{lang}</span><span>{p}%</span>
                            </div>
                            <div className="h-2 w-full bg-white/10 rounded">
                              <div className="h-2 rounded bg-blue-500" style={{ width: `${p}%` }} />
                            </div>
                          </div>
                        );
                      })}
                  </div>
                )}
              </div>
            </div>

            {/* Skills */}
            <div className="bg-white/10 border border-white/20 rounded-xl p-6">
              <h3 className="text-white text-lg mb-3">Skills from GitHub</h3>
              {skillsQ.isLoading ? (
                <div className="text-gray-300">Loading…</div>
              ) : skillsQ.data?.skills?.length ? (
                <div className="flex flex-wrap -m-1">
                  {skillsQ.data.skills.map((s) => (
                    <Chip key={s}>{s}</Chip>
                  ))}
                </div>
              ) : (
                <div className="text-gray-300">No skills detected yet.</div>
              )}
            </div>

            {/* Repos */}
            <div className="bg-white/10 border border-white/20 rounded-xl p-6">
              <h3 className="text-white text-lg mb-3">Top Repositories</h3>
              {!profileQ.data?.top_repositories?.length ? (
                <div className="text-gray-300">No repositories found.</div>
              ) : (
                <ul className="space-y-3">
                  {profileQ.data.top_repositories.map((r, i) => (
                    <li key={i} className="text-gray-200">
                      <a className="hover:underline" href={r.html_url} target="_blank" rel="noreferrer">
                        {r.full_name || r.name}
                      </a>
                      <div className="text-xs text-gray-400">
                        ⭐ {r.stargazers_count ?? 0} • 🍴 {r.forks_count ?? 0} • {r.language || '—'}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default GitHubPage;