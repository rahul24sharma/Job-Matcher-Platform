import React, { useState, useRef, useEffect } from "react";
import { Outlet, NavLink, Link, useNavigate } from "react-router-dom";
import { useAuthStore } from "../../../store/authStore";

export const Layout: React.FC = () => {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const profileRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        profileRef.current &&
        !profileRef.current.contains(event.target as Node)
      ) {
        setProfileOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const baseLink =
    "inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors";
  const inactive =
    "border-transparent text-gray-400 hover:border-blue-400 hover:text-white";
  const active = "border-blue-400 text-white";
  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `${baseLink} ${isActive ? active : inactive}`;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900">
      <nav className="bg-black/20 backdrop-blur-md border-b border-white/10 sticky top-0 z-40 w-full">
        <div className="mx-auto w-full px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Link to="/" className="text-xl font-bold text-blue-400">
                  SkillSync Pro
                </Link>
              </div>

              <div className="hidden md:ml-6 md:block">
                <div className="flex space-x-4">
                  <NavLink to="/dashboard" className={linkClass}>
                    Dashboard
                  </NavLink>
                  <NavLink to="/jobs" className={linkClass}>
                    Jobs
                  </NavLink>
                  <NavLink to="/jobs/matches" className={linkClass}>
                    Matches
                  </NavLink>

                  <div className="relative ml-3" ref={profileRef}>
                    <button
                      type="button"
                      className={linkClass({ isActive: false })}
                      onClick={() => setProfileOpen(!profileOpen)}
                      onMouseEnter={() => setProfileOpen(true)}
                    >
                      Profile
                    </button>
                    {profileOpen && (
                      <div
                        className="absolute left-0 mt-2 w-48 rounded-md shadow-lg bg-gray-800/95 backdrop-blur-sm ring-1 ring-white/10 z-50"
                        onMouseLeave={() => setProfileOpen(false)}
                      >
                        <div className="py-1">
                          <NavLink
                            to="/profile"
                            className={({ isActive }) =>
                              `block px-4 py-2 text-sm ${
                                isActive
                                  ? "text-blue-400 bg-white/10"
                                  : "text-gray-300 hover:bg-white/5"
                              }`
                            }
                            onClick={() => setProfileOpen(false)}
                          >
                            Overview
                          </NavLink>
                          <NavLink
                            to="/resume"
                            className={({ isActive }) =>
                              `block px-4 py-2 text-sm ${
                                isActive
                                  ? "text-blue-400 bg-white/10"
                                  : "text-gray-300 hover:bg-white/5"
                              }`
                            }
                            onClick={() => setProfileOpen(false)}
                          >
                            Resume
                          </NavLink>
                          <NavLink
                            to="/github"
                            className={({ isActive }) =>
                              `block px-4 py-2 text-sm ${
                                isActive
                                  ? "text-blue-400 bg-white/10"
                                  : "text-gray-300 hover:bg-white/5"
                              }`
                            }
                            onClick={() => setProfileOpen(false)}
                          >
                            GitHub
                          </NavLink>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>

            <div className="hidden md:ml-4 md:flex md:items-center">
              <span className="text-gray-300 text-sm mr-4 truncate max-w-[160px]">
                {user?.email}
              </span>
              <button
                onClick={handleLogout}
                className="text-gray-400 hover:text-white text-sm font-medium transition-colors"
              >
                Logout
              </button>
            </div>

            <div className="flex md:hidden">
              <button
                type="button"
                onClick={() => setMobileOpen(!mobileOpen)}
                className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:bg-white/10 focus:outline-none"
                aria-expanded={mobileOpen}
              >
                <span className="sr-only">Open main menu</span>
                {!mobileOpen ? (
                  <svg
                    className="block h-6 w-6"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 6h16M4 12h16M4 18h16"
                    />
                  </svg>
                ) : (
                  <svg
                    className="block h-6 w-6"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                )}
              </button>
            </div>
          </div>
        </div>

        {mobileOpen && (
          <div className="md:hidden border-t border-white/10 bg-black/20 backdrop-blur-md">
            <div className="space-y-1 px-2 pb-3 pt-2">
              {[
                ["/dashboard", "Dashboard"],
                ["/jobs", "Jobs"],
                ["/jobs/matches", "Matches"],
                ["/profile", "Profile"],
                ["/profile/resume", "Resume"],
                ["/profile/github", "GitHub"],
              ].map(([to, label]) => (
                <NavLink
                  key={to}
                  to={to}
                  className={({ isActive }) =>
                    `block rounded-md px-3 py-2 text-base font-medium ${
                      isActive
                        ? "bg-white/10 text-white"
                        : "text-gray-300 hover:bg-white/5 hover:text-white"
                    }`
                  }
                  onClick={() => setMobileOpen(false)}
                >
                  {label}
                </NavLink>
              ))}
            </div>
            <div className="border-t border-white/10 pb-3 pt-4">
              <div className="flex items-center px-5">
                <div className="flex-shrink-0">
                  <div className="h-10 w-10 rounded-full bg-gray-800 flex items-center justify-center text-white">
                    {user?.email?.charAt(0).toUpperCase()}
                  </div>
                </div>
                <div className="ml-3">
                  <div className="text-base font-medium text-white">
                    {user?.email}
                  </div>
                </div>
              </div>
              <div className="mt-3 space-y-1 px-2">
                <button
                  onClick={handleLogout}
                  className="block w-full rounded-md px-3 py-2 text-base font-medium text-gray-400 hover:bg-white/5 hover:text-white"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        )}
      </nav>

      <main className="w-full mx-auto">
        <Outlet />
      </main>
    </div>
  );
};
