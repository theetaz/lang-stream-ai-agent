"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { handleOAuthCallback } from "@/lib/auth-client";
import { Loader2 } from "lucide-react";

export default function AuthCallbackPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    // Prevent multiple executions
    if (processing) return;

    const processCallback = async () => {
      setProcessing(true);

      try {
        // Get hash fragment from URL
        const hash = window.location.hash;

        console.log("OAuth callback received, hash:", hash ? "present" : "missing");

        if (!hash) {
          console.error("No hash fragment in URL");
          setError("No authentication data received from Google");
          setTimeout(() => router.push("/login"), 2000);
          return;
        }

        console.log("Processing OAuth callback...");

        // Handle OAuth callback and get JWT tokens from backend
        const user = await handleOAuthCallback(hash);

        console.log("Authentication successful, user:", user);
        console.log("Tokens stored, redirecting to home...");

        // Small delay to ensure tokens are written to localStorage
        await new Promise(resolve => setTimeout(resolve, 100));

        // Use replace instead of push to prevent back button issues
        window.location.href = "/";
      } catch (err) {
        console.error("OAuth callback error:", err);
        const errorMessage = err instanceof Error ? err.message : "Authentication failed";
        setError(errorMessage);

        // Clear any partial auth data
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');

        // Redirect to login after error
        setTimeout(() => {
          router.push("/login");
        }, 3000);
      }
    };

    processCallback();
  }, []); // Empty deps to run only once

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
        <div className="text-xl font-semibold">Completing sign in...</div>
        <p className="text-muted-foreground">Please wait while we set up your session</p>
      </div>
    </div>
  );
}
