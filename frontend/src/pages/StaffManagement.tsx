import { useState, useEffect } from "react";

import { useAuth } from "../contexts/AuthContext";
import { DashboardNav } from "../components/DashboardNav";
import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface StaffMember {
  id: number;
  username: string;
  full_name: string;
  business_name: string | null;
  role: string;
  is_active: boolean;
  created_at: string;
}

interface StaffCredentials {
  id: number;
  full_name: string;
  username: string;
  password: string;
  business_name: string;
  message: string;
}

export const StaffManagement = () => {
  const { isOwner } = useAuth();
  const [staff, setStaff] = useState<StaffMember[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [staffName, setStaffName] = useState("");
  const [staffEmail, setStaffEmail] = useState("");
  const [credentials, setCredentials] = useState<StaffCredentials | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (isOwner) {
      loadStaff();
    }
  }, [isOwner]);

  const loadStaff = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/staff/list`);
      setStaff(response.data);
    } catch (error) {
      console.error("Failed to load staff:", error);
    }
  };

  const handleCreateStaff = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      const response = await axios.post(`${API_URL}/api/staff/create`, {
        staff_name: staffName,
        email: staffEmail || null,
      });
      setCredentials(response.data);
      setStaffName("");
      setStaffEmail("");
      loadStaff(); // Refresh list
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to create staff account");
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    // You could add a toast notification here
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setStaffName("");
    setStaffEmail("");
    setCredentials(null);
    setError("");
  };

  const handleDeleteStaff = async (id: number) => {
    if (!window.confirm("Are you sure you want to delete this staff member?")) {
      return;
    }

    try {
      await axios.delete(`${API_URL}/api/staff/${id}`);
      loadStaff(); // Refresh list
    } catch (error) {
      console.error("Failed to delete staff:", error);
      alert("Failed to delete staff member");
    }
  };



  if (!isOwner) {
    return (
      <div className="min-h-screen bg-slate-950">
        <DashboardNav />
        <div className="flex items-center justify-center min-h-[80vh]">
          <div className="text-center">
            <div className="text-red-400 text-xl font-semibold mb-2">Access Denied</div>
            <div className="text-slate-400">Only owners can access staff management.</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950">
      <DashboardNav />

      <div className="py-8 px-6 max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Staff Management</h1>
          <p className="text-slate-400">Create and manage staff accounts with auto-generated credentials</p>
        </div>

        <div className="mb-6">
          <button
            onClick={() => setShowModal(true)}
            className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all font-semibold"
          >
            + Add Staff Member
          </button>
        </div>

        {/* Staff Table */}
        <div className="card">
          <h2 className="text-xl font-semibold text-white mb-4">Current Staff ({staff.length})</h2>
          {staff.length === 0 ? (
            <div className="text-slate-400 text-center py-8">No staff members yet</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-700">
                    <th className="text-left py-3 px-4 text-slate-300 font-semibold">Name</th>
                    <th className="text-left py-3 px-4 text-slate-300 font-semibold">Username</th>
                    <th className="text-left py-3 px-4 text-slate-300 font-semibold">Role</th>
                    <th className="text-left py-3 px-4 text-slate-300 font-semibold">Status</th>
                    <th className="text-left py-3 px-4 text-slate-300 font-semibold">Created</th>
                    <th className="text-right py-3 px-4 text-slate-300 font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {staff.map((member) => (
                    <tr key={member.id} className="border-b border-slate-800/50 hover:bg-slate-900/50">
                      <td className="py-3 px-4 text-slate-300">{member.full_name}</td>
                      <td className="py-3 px-4 text-slate-400 font-mono text-sm">{member.username}</td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-1 bg-blue-500/10 text-blue-400 rounded text-xs font-medium">
                          {member.role}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-1 rounded text-xs font-medium ${member.is_active
                            ? "bg-green-500/10 text-green-400"
                            : "bg-red-500/10 text-red-400"
                            }`}
                        >
                          {member.is_active ? "Active" : "Inactive"}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-400 text-sm">
                        {new Date(member.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => handleDeleteStaff(member.id)}
                          className="text-red-400 hover:text-red-300 transition-colors text-sm font-medium"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Danger Zone */}

      </div>

      {/* Add Staff Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-6">
          <div className="bg-slate-900 rounded-xl border border-slate-700 max-w-md w-full max-h-[90vh] overflow-y-auto">
            {!credentials ? (
              <>
                <div className="p-6 border-b border-slate-700">
                  <h2 className="text-2xl font-bold text-white mb-2">Add Staff Member</h2>
                  <p className="text-slate-400 text-sm">
                    Enter the staff member's name. Username and password will be auto-generated.
                  </p>
                </div>

                <form onSubmit={handleCreateStaff} className="p-6 space-y-4">
                  {error && (
                    <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
                      {error}
                    </div>
                  )}

                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Staff Name *
                    </label>
                    <input
                      type="text"
                      value={staffName}
                      onChange={(e) => setStaffName(e.target.value)}
                      required
                      className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Rohan Sharma"
                      disabled={isLoading}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Email Address *
                    </label>
                    <input
                      type="email"
                      value={staffEmail}
                      onChange={(e) => setStaffEmail(e.target.value)}
                      required
                      className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="rohan@example.com"
                      disabled={isLoading}
                    />
                    <p className="text-xs text-slate-500 mt-1">
                      Credentials will be emailed to this address.
                    </p>
                  </div>

                  <div className="flex gap-3 pt-4">
                    <button
                      type="button"
                      onClick={handleCloseModal}
                      className="flex-1 px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg hover:bg-slate-700 transition-all font-medium text-slate-300"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={isLoading}
                      className="flex-1 px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all font-semibold disabled:opacity-50"
                    >
                      {isLoading ? "Creating..." : "Create Account"}
                    </button>
                  </div>
                </form>
              </>
            ) : (
              <div className="p-6">
                <div className="mb-6">
                  <h2 className="text-2xl font-bold text-white mb-2">✅ Staff Account Created</h2>
                  <p className="text-slate-400 text-sm">{credentials.message}</p>
                </div>

                {/* Credentials Card */}
                <div className="bg-gradient-to-br from-blue-500/10 to-purple-500/10 border-2 border-blue-500/30 rounded-xl p-6 mb-6">
                  <div className="space-y-4">
                    <div>
                      <label className="text-xs text-slate-400 uppercase tracking-wider">Full Name</label>
                      <div className="text-lg font-semibold text-white mt-1">{credentials.full_name}</div>
                    </div>
                    <div>
                      <label className="text-xs text-slate-400 uppercase tracking-wider">Username</label>
                      <div className="flex items-center gap-2 mt-1">
                        <code className="text-lg font-mono font-semibold text-blue-400 flex-1 bg-slate-900/50 px-3 py-2 rounded">
                          {credentials.username}
                        </code>
                        <button
                          onClick={() => copyToClipboard(credentials.username)}
                          className="px-3 py-2 bg-blue-500/20 hover:bg-blue-500/30 rounded-lg text-blue-400 text-sm font-medium transition-all"
                        >
                          Copy
                        </button>
                      </div>
                    </div>
                    <div>
                      <label className="text-xs text-slate-400 uppercase tracking-wider">Password</label>
                      <div className="flex items-center gap-2 mt-1">
                        <code className="text-lg font-mono font-semibold text-purple-400 flex-1 bg-slate-900/50 px-3 py-2 rounded">
                          {credentials.password}
                        </code>
                        <button
                          onClick={() => copyToClipboard(credentials.password)}
                          className="px-3 py-2 bg-purple-500/20 hover:bg-purple-500/30 rounded-lg text-purple-400 text-sm font-medium transition-all"
                        >
                          Copy
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4 mb-6">
                  <p className="text-yellow-400 text-sm font-medium">
                    ⚠️ Copy these credentials now. They will not be shown again!
                  </p>
                </div>

                <button
                  onClick={handleCloseModal}
                  className="w-full px-4 py-3 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all font-semibold"
                >
                  Done
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

