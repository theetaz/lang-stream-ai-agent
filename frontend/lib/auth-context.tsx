"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { signIn, signOut as authSignOut } from "./auth-client";

interface User {
  id: number;
  email: string;
  name?: string | null;
  avatar_url?: string | null;
  image?: string | null; // Alias for avatar_url
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: () => void;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  async function checkAuth() {
    console.log("AuthContext: checkAuth called");
    const accessToken = localStorage.getItem("access_token");

    if (!accessToken) {
      console.log("AuthContext: No access token found");
      setLoading(false);
      return;
    }

    console.log("AuthContext: Access token found, verifying with backend...");

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/me`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });

      console.log("AuthContext: /me response status:", res.status);

      if (res.ok) {
        const userData = await res.json();
        console.log("AuthContext: User authenticated:", userData.email);
        // Add image alias for avatar_url
        setUser({ ...userData, image: userData.avatar_url });
      } else {
        console.log("AuthContext: Access token invalid, attempting refresh...");
        await refreshToken();
      }
    } catch (error) {
      console.error("AuthContext: Auth check failed:", error);
    } finally {
      setLoading(false);
      console.log("AuthContext: Auth check complete");
    }
  }

  function login() {
    signIn();
  }

  async function logout() {
    await authSignOut();
    setUser(null);
    // Redirect to login
    window.location.href = "/login";
  }

  async function refreshToken() {
    const refreshTokenValue = localStorage.getItem("refresh_token");
    if (!refreshTokenValue) {
      await logout();
      return;
    }

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshTokenValue }),
      });

      if (res.ok) {
        const { access_token, refresh_token, user: userData } = await res.json();
        localStorage.setItem("access_token", access_token);
        localStorage.setItem("refresh_token", refresh_token);
        setUser({ ...userData, image: userData.avatar_url });
      } else {
        await logout();
      }
    } catch (error) {
      console.error("Token refresh failed:", error);
      await logout();
    }
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refreshToken }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}

// Export hook for compatibility with existing code
export function useSession() {
  const { user, loading } = useAuth();
  return {
    data: user ? { user, session: { user } } : null,
    isPending: loading,
  };
}
