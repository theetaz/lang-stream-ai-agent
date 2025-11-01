/**
 * Better Auth client configuration
 * Used in client components for authentication
 */
import { createAuthClient } from "better-auth/react";

export const authClient = createAuthClient({
  baseURL: process.env.NEXT_PUBLIC_BETTER_AUTH_URL || "http://localhost:3000",
});

// Export hooks for use in components
export const { signIn, signOut, useSession } = authClient;
