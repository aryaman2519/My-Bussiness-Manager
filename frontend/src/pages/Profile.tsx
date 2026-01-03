import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { DashboardNav } from "../components/DashboardNav";
import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const Profile = () => {
    const { user, isOwner, logout } = useAuth();
    const navigate = useNavigate();
    const [isChangingPassword, setIsChangingPassword] = useState(false);
    const [step, setStep] = useState(1); // 1: Verify Code, 2: New Password
    const [securityCode, setSecurityCode] = useState("");
    const [newPassword, setNewPassword] = useState("");
    const [message, setMessage] = useState({ type: "", text: "" });
    const [isLoading, setIsLoading] = useState(false);

    const handleVerifyCode = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setMessage({ type: "", text: "" });
        try {
            await axios.post(`${API_URL}/api/auth/verify-security-code`, {
                security_code: securityCode
            }, {
                headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
            });
            setStep(2);
        } catch (err: any) {
            setMessage({ type: "error", text: err.response?.data?.detail || "Invalid Security Code" });
        } finally {
            setIsLoading(false);
        }
    };

    const handleResetPassword = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setMessage({ type: "", text: "" });
        try {
            await axios.post(`${API_URL}/api/auth/reset-password`, {
                security_code: securityCode,
                new_password: newPassword
            }, {
                headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
            });
            setMessage({ type: "success", text: "Password changed successfully! Check your email." });
            setStep(1);
            setIsChangingPassword(false);
            setSecurityCode("");
            setNewPassword("");
        } catch (err: any) {
            setMessage({ type: "error", text: err.response?.data?.detail || "Failed to reset password" });
        } finally {
            setIsLoading(false);
        }
    };

    const handleDeleteAccount = async () => {
        if (
            !window.confirm(
                "Are you sure you want to delete your account? This action cannot be undone and will delete all associated data."
            )
        ) {
            return;
        }

        try {
            await axios.delete(`${API_URL}/api/auth/me`, {
                headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
            });
            logout();
            navigate("/login");
        } catch (error) {
            console.error("Failed to delete account:", error);
            alert("Failed to delete account");
        }
    };

    return (
        <div className="min-h-screen bg-slate-950">
            <DashboardNav />

            <div className="py-12 px-6 max-w-4xl mx-auto">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-white mb-2">User Profile</h1>
                    <p className="text-slate-400">View your account credentials and role information</p>
                </div>

                <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg mb-8">
                    <div className="p-8">
                        <div className="flex items-center gap-6 mb-8">
                            <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-3xl font-bold text-white shadow-lg">
                                {(user?.full_name || "?").charAt(0).toUpperCase()}
                            </div>
                            <div>
                                <h2 className="text-2xl font-bold text-white">{user?.full_name}</h2>
                                <span className={`px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider ${isOwner ? 'bg-purple-500/20 text-purple-400' : 'bg-blue-500/20 text-blue-400'}`}>
                                    {user?.role}
                                </span>
                            </div>
                        </div>

                        <div className="grid gap-6 md:grid-cols-2">
                            <div className="space-y-1">
                                <label className="text-xs font-medium text-slate-500 uppercase tracking-wider">Username</label>
                                <div className="text-slate-200 font-mono bg-slate-800/50 px-4 py-2 rounded-lg border border-slate-700/50">
                                    {user?.username}
                                </div>
                            </div>

                            <div className="space-y-1">
                                <label className="text-xs font-medium text-slate-500 uppercase tracking-wider">Business Name</label>
                                <div className="text-slate-200 font-medium px-4 py-2">
                                    {user?.business_name || "N/A"}
                                </div>
                            </div>

                            <div className="space-y-1">
                                <label className="text-xs font-medium text-slate-500 uppercase tracking-wider">Email Address</label>
                                <div className="text-slate-200 font-medium px-4 py-2">
                                    {user?.email || "No email provided"}
                                </div>
                            </div>

                            <div className="space-y-1">
                                <label className="text-xs font-medium text-slate-500 uppercase tracking-wider">Account ID</label>
                                <div className="text-slate-400 font-mono text-sm px-4 py-2">
                                    #{user?.id}
                                </div>
                            </div>

                            {/* Reporting To (For Staff) */}
                            {!isOwner && (user as any)?.owner_name && (
                                <div className="space-y-1 col-span-full">
                                    <label className="text-xs font-medium text-slate-500 uppercase tracking-wider">Reporting To</label>
                                    <div className="text-blue-400 font-medium px-4 py-2 bg-blue-500/10 rounded-lg border border-blue-500/20">
                                        Owner: {(user as any)?.owner_name}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="bg-slate-950/50 px-8 py-4 border-t border-slate-800 flex justify-between items-center">
                        <span className="text-xs text-slate-500">
                            {isOwner
                                ? "As an Owner, you can manage staff and inventory."
                                : "As Staff, you have restricted access to inventory management."}
                        </span>
                    </div>
                </div>

                {/* Password Change Section */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 shadow-lg">
                    <div className="flex justify-between items-center mb-6">
                        <h2 className="text-xl font-bold text-white">Security Settings</h2>
                        {!isChangingPassword && (
                            <button
                                onClick={() => setIsChangingPassword(true)}
                                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors text-sm font-medium"
                            >
                                Change Password
                            </button>
                        )}
                    </div>

                    {message.text && (
                        <div className={`p-4 mb-6 rounded-lg ${message.type === 'error' ? 'bg-red-500/10 text-red-400 border border-red-500/20' : 'bg-green-500/10 text-green-400 border border-green-500/20'}`}>
                            {message.text}
                        </div>
                    )}

                    {isChangingPassword && (
                        <div className="bg-slate-950 p-6 rounded-xl border border-slate-800">
                            <div className="flex items-center gap-4 mb-6">
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${step === 1 ? 'bg-blue-500 text-white' : 'bg-green-500 text-white'}`}>1</div>
                                <div className="h-0.5 flex-1 bg-slate-800"></div>
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${step === 2 ? 'bg-blue-500 text-white' : 'bg-slate-800 text-slate-500'}`}>2</div>
                            </div>

                            {step === 1 ? (
                                <form onSubmit={handleVerifyCode} className="space-y-4">
                                    <h3 className="text-white font-medium">Verify Identity</h3>
                                    <p className="text-sm text-slate-400">Enter your 8-digit Security Code found in your welcome email.</p>
                                    <input
                                        type="text"
                                        value={securityCode}
                                        onChange={(e) => setSecurityCode(e.target.value)}
                                        placeholder="Enter Security Code"
                                        className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        required
                                    />
                                    <div className="flex gap-3">
                                        <button
                                            type="button"
                                            onClick={() => setIsChangingPassword(false)}
                                            className="px-4 py-2 text-slate-400 hover:text-white"
                                        >
                                            Cancel
                                        </button>
                                        <button
                                            type="submit"
                                            disabled={isLoading}
                                            className="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium disabled:opacity-50"
                                        >
                                            {isLoading ? "Verifying..." : "Verify Code"}
                                        </button>
                                    </div>
                                </form>
                            ) : (
                                <form onSubmit={handleResetPassword} className="space-y-4">
                                    <h3 className="text-white font-medium">Set New Password</h3>
                                    <p className="text-sm text-slate-400">Enter your new password.</p>
                                    <input
                                        type="password"
                                        value={newPassword}
                                        onChange={(e) => setNewPassword(e.target.value)}
                                        placeholder="New Password"
                                        minLength={6}
                                        className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        required
                                    />
                                    <div className="flex gap-3">
                                        <button
                                            type="button"
                                            onClick={() => setStep(1)}
                                            className="px-4 py-2 text-slate-400 hover:text-white"
                                        >
                                            Back
                                        </button>
                                        <button
                                            type="submit"
                                            disabled={isLoading}
                                            className="px-6 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg font-medium disabled:opacity-50"
                                        >
                                            {isLoading ? "Saving..." : "Reset Password"}
                                        </button>
                                    </div>
                                </form>
                            )}
                        </div>
                    )}
                </div>

                {/* Danger Zone */}
                {/* Danger Zone - Owners Only */}
                {isOwner && (
                    <div className="mt-12 border-t border-red-500/20 pt-8">
                        <h2 className="text-xl font-semibold text-red-400 mb-4">Danger Zone</h2>
                        <div className="bg-red-500/5 border border-red-500/10 rounded-lg p-6 flex items-center justify-between">
                            <div>
                                <h3 className="text-white font-medium mb-1">Delete Account</h3>
                                <p className="text-slate-400 text-sm">
                                    Permanently delete your account and all associated data. This action cannot be undone.
                                </p>
                            </div>
                            <button
                                onClick={handleDeleteAccount}
                                className="px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 rounded-lg transition-all font-medium"
                            >
                                Delete Account
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
