"use client";

import { Card, CardContent } from "@/components/ui/card";
import { LoginHeader } from "./login-header";
import { LoginForm } from "./login-form";
import { GoogleButton } from "./google-button";
import { loginWithEmailPassword, registerWithEmailPassword, signInWithGoogle } from "@/lib/auth-client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";

export function LoginContainer() {
  const router = useRouter();
  const [isLogin, setIsLogin] = useState(true);

  const emailLoginMutation = useMutation({
    mutationFn: async (data: { email: string; password: string; name?: string }) => {
      if (isLogin) {
        return await loginWithEmailPassword(data.email, data.password);
      } else {
        return await registerWithEmailPassword(data.email, data.password, data.name);
      }
    },
    onSuccess: () => {
      router.push("/");
    },
  });

  const googleLoginMutation = useMutation({
    mutationFn: async () => {
      return await signInWithGoogle();
    },
  });

  const loading = emailLoginMutation.isPending || googleLoginMutation.isPending;
  const error = emailLoginMutation.error?.message || googleLoginMutation.error?.message;

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 p-4">
      <Card className="w-full max-w-md">
        <LoginHeader isLogin={isLogin} />

        <CardContent className="space-y-4">
          {error && (
            <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </div>
          )}

          <LoginForm
            isLogin={isLogin}
            loading={loading}
            onSubmit={(data) => emailLoginMutation.mutate(data)}
          />

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-card px-2 text-muted-foreground">Or continue with</span>
            </div>
          </div>

          <GoogleButton
            loading={loading}
            onClick={() => googleLoginMutation.mutate()}
          />

          <div className="text-center text-sm">
            <button
              type="button"
              onClick={() => {
                setIsLogin(!isLogin);
                emailLoginMutation.reset();
                googleLoginMutation.reset();
              }}
              className="text-primary hover:underline"
              disabled={loading}
            >
              {isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
            </button>
          </div>

          <p className="text-center text-xs text-muted-foreground">
            By signing in, you agree to our Terms of Service and Privacy Policy
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

