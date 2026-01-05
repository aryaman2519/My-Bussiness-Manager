import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  business_name: string;
  phone_number?: string; // Optional for legacy
  business_type?: string; // Optional because legacy users might not have it yet
  role: "owner" | "staff";
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  isOwner: boolean;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load auth state from localStorage on mount and VERIFY with backend
  useEffect(() => {
    const initializeAuth = async () => {
      const storedToken = localStorage.getItem("token");
      const storedUser = localStorage.getItem("user");

      if (storedToken && storedUser) {
        // Set temporary state to allow verification call to proceed with headers
        setToken(storedToken);
        axios.defaults.headers.common["Authorization"] = `Bearer ${storedToken}`;

        try {
          // Verify with backend
          const response = await axios.get(`${API_URL}/api/auth/verify-token`);
          // If successful, set user data from fresh response (single source of truth)
          setUser(response.data);
          // Update local storage in case something changed (like role or business name)
          localStorage.setItem("user", JSON.stringify(response.data));
        } catch (error) {
          console.error("Token verification failed:", error);
          // If verification fails (401 or other), clear everything
          logout();
          // Optional: You could show a toast here if you have a toast context
          // alert("Session expired. Please log in again.");
        }
      } else {
        // Ensure clean state if no token
        logout();
      }
      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  const login = async (username: string, password: string) => {
    const formData = new FormData();
    formData.append("username", username);
    formData.append("password", password);

    const response = await axios.post(`${API_URL}/api/auth/token`, formData, {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    });

    const { access_token, user: userData } = response.data;

    setToken(access_token);
    setUser(userData);

    localStorage.setItem("token", access_token);
    localStorage.setItem("user", JSON.stringify(userData));

    axios.defaults.headers.common["Authorization"] = `Bearer ${access_token}`;
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    // Clear any other app specific keys if necessary
    delete axios.defaults.headers.common["Authorization"];

    // Optional: Redirect to login if not already handled by protected routes
    // window.location.href = "/login"; // Force full reload/redirect if needed
  };

  const isOwner = user?.role === "owner";

  return (
    <AuthContext.Provider
      value={{ user, token, login, logout, isOwner, isLoading }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

