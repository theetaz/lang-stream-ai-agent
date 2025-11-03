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
      setProcessing(true);

      try {
        const session = await authClient.getSession();

        if (!session.data) {
          setError("Authentication failed - no session");
          setTimeout(() => router.push("/login"), 2000);
          return;
        }

        const existingToken = localStorage.getItem("backend_access_token");
        if (existingToken) {
          window.location.href = "/";
          return;
        }

        await exchangeForBackendJWT(session.data);
        await new Promise((resolve) => setTimeout(resolve, 100));
        window.location.href = "/";
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Authentication failed";
        setError(errorMessage);
        localStorage.removeItem("backend_access_token");
        localStorage.removeItem("backend_refresh_token");
        localStorage.removeItem("backend_user");
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

