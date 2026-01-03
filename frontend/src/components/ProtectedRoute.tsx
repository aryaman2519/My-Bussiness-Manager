import { Navigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireOwner?: boolean;
}

export const ProtectedRoute = ({ children, requireOwner = false }: ProtectedRouteProps) => {
  const { user, isLoading, isOwner } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-slate-400">Loading...</div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (requireOwner && !isOwner) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-400 text-xl font-semibold mb-2">Access Denied</div>
          <div className="text-slate-400">Only owners can access this page.</div>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};

