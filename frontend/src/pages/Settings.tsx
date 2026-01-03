import { useAuth } from "../contexts/AuthContext";
import { Link } from "react-router-dom";
import { DashboardNav } from "../components/DashboardNav";

export const Settings = () => {
  const { isOwner } = useAuth();

  if (!isOwner) {
    return (
      <div className="min-h-screen bg-slate-950">
        <DashboardNav />
        <div className="flex items-center justify-center min-h-[80vh]">
          <div className="text-center">
            <div className="text-red-400 text-xl font-semibold mb-2">Access Denied</div>
            <div className="text-slate-400">Only owners can access settings.</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950">
      <DashboardNav />
      <div className="py-8 px-6 max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Settings</h1>
          <p className="text-slate-400">Manage staff accounts and system settings</p>
        </div>

        <div className="card mb-8">
          <h2 className="text-xl font-semibold text-white mb-4">Staff Management</h2>
          <p className="text-slate-400 mb-4">
            Create and manage staff accounts with auto-generated credentials. Staff members get automatically generated usernames and passwords.
          </p>
          <Link
            to="/staff"
            className="inline-block px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all font-semibold"
          >
            Go to Staff Management →
          </Link>
        </div>

        <div className="card">
          <h2 className="text-xl font-semibold text-white mb-4">System Settings</h2>
          <p className="text-slate-400">More settings coming soon...</p>
        </div>
      </div>
    </div>
  );
};
