"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { authClient, exchangeForBackendJWT } from "@/lib/auth-client";
import { Loader2 } from "lucide-react";

export function AuthSuccessHandler() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    if (processing) return;

    const handleAuthSuccess = async () => {
      console.log("🔐 Auth Success Handler: Starting...");
      setProcessing(true);

      try {
        console.log("🔐 Auth Success Handler: Fetching session from Better Auth...");
        const session = await authClient.getSession();
        console.log("🔐 Auth Success Handler: Session data:", session);

        if (!session.data) {
          console.error("🔐 Auth Success Handler: No session data found!");
          setError("Authentication failed - no session");
          setTimeout(() => router.push("/login"), 2000);
          return;
        }

        console.log("🔐 Auth Success Handler: Session user:", session.data.user);

        // Check if both localStorage token AND cookie exist
        const existingToken = localStorage.getItem("backend_access_token");
        const existingCookie = document.cookie.split('; ').find(row => row.startsWith('backend_access_token='));
        
        if (existingToken && existingCookie) {
          console.log("🔐 Auth Success Handler: Token and cookie already exist, redirecting to home");
          window.location.href = "/";
          return;
        }

        // If token exists but cookie doesn't, or vice versa, do the exchange to sync them
        if (existingToken || existingCookie) {
          console.log("🔐 Auth Success Handler: Token/cookie mismatch detected, re-exchanging...");
        }

        console.log("🔐 Auth Success Handler: Exchanging for backend JWT...");
        await exchangeForBackendJWT(session.data);
        
        console.log("🔐 Auth Success Handler: Exchange successful, redirecting to home");
        await new Promise((resolve) => setTimeout(resolve, 100));
        window.location.href = "/";
      } catch (err) {
        console.error("🔐 Auth Success Handler: Error occurred:", err);
        const errorMessage = err instanceof Error ? err.message : "Authentication failed";
        setError(errorMessage);
        
        // Clear localStorage
        localStorage.removeItem("backend_access_token");
        localStorage.removeItem("backend_refresh_token");
        localStorage.removeItem("backend_user");
        localStorage.removeItem("backend_session_id");
        
        // Clear cookies
        document.cookie = "backend_access_token=; path=/; max-age=0";
        document.cookie = "backend_refresh_token=; path=/; max-age=0";
        document.cookie = "backend_session_id=; path=/; max-age=0";
        
        setTimeout(() => router.push("/login"), 3000);
      }
    };

    handleAuthSuccess();
  }, [processing, router]);

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center space-y-4">
          <div className="text-red-500 text-xl">Authentication Error</div>
          <p className="text-muted-foreground">{error}</p>
          <p className="text-sm text-muted-foreground">Redirecting to login...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center space-y-4">
        <Loader2 className="h-12 w-12 animate-spin mx-auto text-primary" />
        <div className="text-xl font-semibold">Completing authentication...</div>
        <p className="text-muted-foreground">Setting up your session</p>
      </div>
    </div>
  );
}

