import { Link, useNavigate } from "react-router-dom";
import { useEffect } from "react";
import axios from "axios";
import { useAuth } from "../contexts/AuthContext";
import { DashboardNav } from "../components/DashboardNav";

export const Dashboard = () => {
  const { user, isOwner } = useAuth();
  const navigate = useNavigate();

  /* 
  Legacy Check Removed: We no longer force users to upload a bill template.
  useEffect(() => {
    const checkTemplate = async () => {
      if (isOwner) {
        try {
          // Verify if template exists
          const response = await axios.get(`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/api/settings/template`);
          if (!response.data.html) {
            navigate("/billing/setup");
          }
        } catch (error) {
          // If error (e.g. 404 or nothing saved), assume setup needed
          navigate("/billing/setup");
        }
      }
    };
    checkTemplate();
  }, [isOwner, navigate]);
  */

  return (
    <div className="min-h-screen bg-slate-950">
      <DashboardNav />

      <main className="px-6 py-10 space-y-8 max-w-6xl mx-auto">
        <header>
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <p className="text-sm text-slate-400 uppercase tracking-widest mb-1">
                Welcome back
              </p>
              <h1 className="text-3xl font-bold text-white max-w-2xl">
                {user?.full_name}
              </h1>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-lg px-4 py-2">
              <span className="text-slate-400 text-sm">Role: </span>
              <span className="text-white font-medium capitalize">{user?.role}</span>
            </div>
          </div>
        </header>

        <section className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {/* Stock Management Card */}
          <Link to="/stock" className="group relative bg-slate-900 border border-slate-800 rounded-2xl p-6 hover:border-blue-500/50 hover:bg-slate-800/50 transition-all duration-300">
            <div className="absolute top-6 right-6 p-2 bg-blue-500/10 rounded-lg group-hover:bg-blue-500/20 transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Stock Management</h3>
            <p className="text-slate-400 text-sm mb-4">
              View inventory levels, add new items, and update stock quantities.
            </p>
            <span className="text-blue-400 text-sm font-medium flex items-center gap-1 group-hover:gap-2 transition-all">
              Manage Stock &rarr;
            </span>
          </Link>





          {/* Profile Management Card */}
          <Link to="/profile" className="group relative bg-slate-900 border border-slate-800 rounded-2xl p-6 hover:border-purple-500/50 hover:bg-slate-800/50 transition-all duration-300">
            <div className="absolute top-6 right-6 p-2 bg-purple-500/10 rounded-lg group-hover:bg-purple-500/20 transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-white mb-2">My Profile</h3>
            <p className="text-slate-400 text-sm mb-4">
              View your account details, credentials, and role permissions.
            </p>
            <span className="text-purple-400 text-sm font-medium flex items-center gap-1 group-hover:gap-2 transition-all">
              View Profile &rarr;
            </span>
          </Link>

          {/* Billing Generation Card */}
          <Link to="/billing" className="group relative bg-slate-900 border border-slate-800 rounded-2xl p-6 hover:border-green-500/50 hover:bg-slate-800/50 transition-all duration-300">
            <div className="absolute top-6 right-6 p-2 bg-green-500/10 rounded-lg group-hover:bg-green-500/20 transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Generate Bill</h3>
            <p className="text-slate-400 text-sm mb-4">
              Create invoices, deduct stock automatically, and print receipts.
            </p>
            <span className="text-green-400 text-sm font-medium flex items-center gap-1 group-hover:gap-2 transition-all">
              Create Invoice &rarr;
            </span>
          </Link>

          {/* Owner Only: Staff Management */}
          {isOwner && (
            <Link to="/staff" className="group relative bg-slate-900 border border-slate-800 rounded-2xl p-6 hover:border-emerald-500/50 hover:bg-slate-800/50 transition-all duration-300">
              <div className="absolute top-6 right-6 p-2 bg-emerald-500/10 rounded-lg group-hover:bg-emerald-500/20 transition-colors">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-white mb-2">Staff Management</h3>
              <p className="text-slate-400 text-sm mb-4">
                Manage staff accounts, assign roles, and view team details.
              </p>
              <span className="text-emerald-400 text-sm font-medium flex items-center gap-1 group-hover:gap-2 transition-all">
                Manage Team &rarr;
              </span>
            </Link>
          )}

          {/* Accounts & Finance */}
          {/* Accounts & Finance - Owner Only */}
          {isOwner && (
            <Link to="/accounts" className="group relative bg-slate-900 border border-slate-800 rounded-2xl p-6 hover:border-yellow-500/50 hover:bg-slate-800/50 transition-all duration-300">
              <div className="absolute top-6 right-6 p-2 bg-yellow-500/10 rounded-lg group-hover:bg-yellow-500/20 transition-colors">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-white mb-2">Accounts & Finance</h3>
              <p className="text-slate-400 text-sm mb-4">
                Track bank accounts, cash flow, and record expenses.
              </p>
              <span className="text-yellow-400 text-sm font-medium flex items-center gap-1 group-hover:gap-2 transition-all">
                Manage Finance &rarr;
              </span>
            </Link>
          )}

          {/* General Settings - Visible to All (Restricted inside) */}
          <Link to="/business-setup" className="group relative bg-slate-900 border border-slate-800 rounded-2xl p-6 hover:border-orange-500/50 hover:bg-slate-800/50 transition-all duration-300">
            <div className="absolute top-6 right-6 p-2 bg-orange-500/10 rounded-lg group-hover:bg-orange-500/20 transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-orange-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-white mb-2">General Settings</h3>
            <p className="text-slate-400 text-sm mb-4">
              Configure invoice template, logo, signature, and business details.
            </p>
            <span className="text-orange-400 text-sm font-medium flex items-center gap-1 group-hover:gap-2 transition-all">
              Configure &rarr;
            </span>
          </Link>

        </section>
      </main>
    </div>
  );
};







