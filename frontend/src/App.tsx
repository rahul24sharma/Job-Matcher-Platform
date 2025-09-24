import { useEffect } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import { Toaster } from "react-hot-toast";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Profile from "./pages/profile/Profile";
import {JobExplore} from "./pages/jobs/JobsExplore";

import { useAuthStore } from "./store/authStore";
import { ProtectedRoute } from "./pages/auth/ProtectedRoute";
import { PublicRoute } from "./pages/auth/PublicRoute";
import { Login } from "./pages/auth/Login";
import { Register } from "./pages/auth/Register";
// import { Dashboard } from './pages/Dashboard';
import Dashboard from "./pages/dashboard/Dashboard";
import { Layout } from "./components/layout/Layout/Layout";
import Resume from "./pages/profile/Resume";
import GitHubPage from "./pages/github/GitHub";
import JobMatches from "./pages/jobs/JobMatches";
import "./App.css";
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  const checkAuth = useAuthStore((state) => state.checkAuth);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          <Route
            path="/login"
            element={
              <PublicRoute>
                <Login />
              </PublicRoute>
            }
          />
          <Route
            path="/register"
            element={
              <PublicRoute>
                <Register />
              </PublicRoute>
            }
          />

          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="profile" element={<Profile />} />
            <Route path="resume" element={<Resume />} />
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="github" element={<GitHubPage />} />
            <Route path="jobs/matches" element={<JobMatches />} />
            <Route path="jobs" element={<JobExplore />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>

      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: "#363636",
            color: "#fff",
          },
        }}
      />
    </QueryClientProvider>
  );
}

export default App;
