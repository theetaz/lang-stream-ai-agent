"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { authClient, exchangeForBackendJWT } from "@/lib/auth-client";
import { Loader2 } from "lucide-react";

/**
 * OAuth Success Callback
 * After Better Auth completes Google OAuth:
 * 1. Get Better Auth session
 * 2. Send user data to our backend
 * 3. Store backend JWT tokens
 * 4. Redirect to home
 */
export default function AuthSuccessPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    if (processing) return;

    const handleAuthSuccess = async () => {
      setProcessing(true);

      try {
        console.log("Auth success callback - getting Better Auth session...");

        // Get the Better Auth session
        const session = await authClient.getSession();

        if (!session.data) {
          console.error("No Better Auth session found");
          setError("Authentication failed - no session");
          setTimeout(() => router.push("/login"), 2000);
          return;
        }

        console.log("Better Auth session found:", session.data.user.email);

        // Check if we already have backend tokens
        const existingToken = localStorage.getItem("backend_access_token");
        if (existingToken) {
          console.log("Backend tokens already exist, redirecting to home...");
          window.location.href = "/";
          return;
        }

        // Exchange for backend JWT
        console.log("Exchanging for backend JWT...");
        await exchangeForBackendJWT(session.data);

        console.log("Backend JWT obtained successfully, redirecting to home...");

        // Small delay to ensure tokens are written
        await new Promise((resolve) => setTimeout(resolve, 100));

        // Redirect to home
        window.location.href = "/";
      } catch (err) {
        console.error("Auth success handling error:", err);
        const errorMessage = err instanceof Error ? err.message : "Authentication failed";
        setError(errorMessage);

        // Clear any partial data
        localStorage.removeItem("backend_access_token");
        localStorage.removeItem("backend_refresh_token");
        localStorage.removeItem("backend_user");

        // Redirect to login after error
        setTimeout(() => {
          router.push("/login");
        }, 3000);
      }
    };

    handleAuthSuccess();
  }, []);

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
