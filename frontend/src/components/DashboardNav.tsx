import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

export const DashboardNav = () => {
  const { user, logout, isOwner } = useAuth();

  return (
    <nav className="sticky top-0 z-50 backdrop-blur-md bg-slate-900/90 border-b border-slate-800/50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link to="/dashboard" className="flex items-center gap-2 sm:gap-3">
              <img src="/logo.png" alt="Logo" className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg shadow-lg shadow-blue-500/20" />
              <div>
                <div className="text-sm sm:text-base font-bold text-white">MY STORE MANAGER</div>
                <div className="text-[10px] sm:text-xs text-slate-400">Dashboard</div>
              </div>
            </Link>

            {/* Navigation links moved to Dashboard cards */}
          </div>

          <div className="flex items-center gap-4">
            <div className="text-right hidden sm:block">
              <div className="text-sm font-medium text-white">{user?.full_name}</div>
              <div className="text-xs text-slate-400 capitalize">{user?.role}</div>
            </div>
            <button
              onClick={logout}
              className="px-4 py-2 bg-slate-800/60 border border-slate-700/50 rounded-lg hover:bg-slate-800 hover:border-slate-600 transition-all font-medium text-sm text-slate-300"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

