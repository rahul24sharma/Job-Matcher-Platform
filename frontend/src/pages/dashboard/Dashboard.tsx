import { Link } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { Upload, Github, Briefcase, TrendingUp, User, FileText, Code, Target } from 'lucide-react';

export const Dashboard = () => {
  const user = useAuthStore((s) => s.user);

  return (
    <div className="min-h-screen p-6">
      <div className="max-w-7xl mx-auto">
        {/* Welcome Section */}
        <div className="bg-white/10 backdrop-blur-md rounded-xl p-8 border border-white/20 mb-6">
          <h1 className="text-3xl md:text-4xl font-extrabold text-white mb-2">
            Welcome back, {user?.full_name || user?.email?.split('@')[0]}!
          </h1>
          <p className="text-gray-300 text-lg">
            Start by uploading your resume or connecting your GitHub account to find your perfect job matches.
          </p>

          <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Link 
              to="/profile/resume" 
              className="group relative overflow-hidden rounded-lg p-6 bg-blue-500/20 border border-blue-500/50 hover:bg-blue-500/30 transition-all duration-300 hover:scale-105"
            >
              <div className="flex flex-col items-center text-center">
                <Upload className="h-10 w-10 text-blue-400 mb-3" />
                <span className="text-white font-medium">Upload Resume</span>
                <span className="text-gray-400 text-sm mt-1">Add your CV</span>
              </div>
            </Link>

            <Link 
              to="/profile/github" 
              className="group relative overflow-hidden rounded-lg p-6 bg-purple-500/20 border border-purple-500/50 hover:bg-purple-500/30 transition-all duration-300 hover:scale-105"
            >
              <div className="flex flex-col items-center text-center">
                <Github className="h-10 w-10 text-purple-400 mb-3" />
                <span className="text-white font-medium">Connect GitHub</span>
                <span className="text-gray-400 text-sm mt-1">Sync repos</span>
              </div>
            </Link>

            <Link 
              to="/jobs/matches" 
              className="group relative overflow-hidden rounded-lg p-6 bg-green-500/20 border border-green-500/50 hover:bg-green-500/30 transition-all duration-300 hover:scale-105"
            >
              <div className="flex flex-col items-center text-center">
                <Target className="h-10 w-10 text-green-400 mb-3" />
                <span className="text-white font-medium">View Matches</span>
                <span className="text-gray-400 text-sm mt-1">See your fits</span>
              </div>
            </Link>

            <Link 
              to="/jobs" 
              className="group relative overflow-hidden rounded-lg p-6 bg-indigo-500/20 border border-indigo-500/50 hover:bg-indigo-500/30 transition-all duration-300 hover:scale-105"
            >
              <div className="flex flex-col items-center text-center">
                <Briefcase className="h-10 w-10 text-indigo-400 mb-3" />
                <span className="text-white font-medium">Explore Jobs</span>
                <span className="text-gray-400 text-sm mt-1">Browse all</span>
              </div>
            </Link>
          </div>
        </div>

        {/* Stats Section */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Profile Completion</p>
                <p className="text-2xl font-bold text-white mt-1">75%</p>
              </div>
              <User className="h-8 w-8 text-blue-400" />
            </div>
            <div className="mt-4 w-full bg-white/10 rounded-full h-2">
              <div className="bg-blue-500 h-2 rounded-full" style={{ width: '75%' }}></div>
            </div>
          </div>

          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Skills Identified</p>
                <p className="text-2xl font-bold text-white mt-1">0</p>
              </div>
              <Code className="h-8 w-8 text-purple-400" />
            </div>
            <p className="text-gray-400 text-xs mt-3">Upload resume to extract skills</p>
          </div>

          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Job Matches</p>
                <p className="text-2xl font-bold text-white mt-1">0</p>
              </div>
              <TrendingUp className="h-8 w-8 text-green-400" />
            </div>
            <p className="text-gray-400 text-xs mt-3">Complete profile for matches</p>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
          <h2 className="text-xl font-semibold text-white mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Link 
              to="/profile" 
              className="flex items-center gap-3 p-4 bg-white/5 rounded-lg hover:bg-white/10 transition-colors"
            >
              <User className="h-5 w-5 text-gray-400" />
              <div>
                <p className="text-white font-medium">Complete Your Profile</p>
                <p className="text-gray-400 text-sm">Add your details and preferences</p>
              </div>
            </Link>

            <Link 
              to="/profile/resume" 
              className="flex items-center gap-3 p-4 bg-white/5 rounded-lg hover:bg-white/10 transition-colors"
            >
              <FileText className="h-5 w-5 text-gray-400" />
              <div>
                <p className="text-white font-medium">Manage Resume</p>
                <p className="text-gray-400 text-sm">Upload or update your CV</p>
              </div>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;