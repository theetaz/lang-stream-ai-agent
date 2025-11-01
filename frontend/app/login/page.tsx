"use client";

import { signInWithGoogle, authClient } from "@/lib/auth-client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Bot } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export default function LoginPage() {
  const router = useRouter();
  const [checking, setChecking] = useState(true);

  // Check if user is already logged in
  useEffect(() => {
    const checkSession = async () => {
      console.log("Login page: Checking existing session...");

      // Check if we have backend tokens
      const backendToken = localStorage.getItem("backend_access_token");
      if (backendToken) {
        console.log("Login page: Found backend token, redirecting to home...");
        router.push("/");
        return;
      }

      // Check Better Auth session
      const session = await authClient.getSession();
      if (session.data) {
        console.log("Login page: Found Better Auth session, redirecting to home...");
        router.push("/");
        return;
      }

      console.log("Login page: No existing session");
      setChecking(false);
    };

    checkSession();
  }, [router]);

  const handleGoogleSignIn = async () => {
    console.log("Login page: Starting Google OAuth flow with Better Auth...");
    await signInWithGoogle();
  };

  // Show loading while checking for existing session
  if (checking) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center space-y-4">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-primary border-t-transparent mx-auto" />
          <p className="text-muted-foreground">Checking session...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-4 text-center">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-blue-600 to-purple-600">
            <Bot className="h-10 w-10 text-white" />
          </div>
          <div>
            <CardTitle className="text-2xl font-bold">Welcome to LangGraph AI</CardTitle>
            <CardDescription className="mt-2">
              Sign in with your Google account to start chatting
            </CardDescription>
          </div>
        </CardHeader>

        <CardContent>
          <Button
            onClick={handleGoogleSignIn}
            className="w-full h-12 text-base font-medium"
            size="lg"
          >
            <svg className="mr-2 h-5 w-5" viewBox="0 0 24 24">
              <path
                fill="currentColor"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="currentColor"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="currentColor"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
              />
              <path
                fill="currentColor"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
              />
            </svg>
            Continue with Google
          </Button>

          <p className="mt-6 text-center text-xs text-muted-foreground">
            By signing in, you agree to our Terms of Service and Privacy Policy
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
