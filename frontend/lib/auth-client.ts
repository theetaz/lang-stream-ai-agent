/**
 * Better Auth Client with Custom Backend JWT Integration
 *
 * Flow:
 * 1. Better Auth handles Google OAuth
 * 2. After OAuth, send user data to our FastAPI backend
 * 3. Backend returns JWT tokens (access + refresh)
 * 4. Store JWT in localStorage and Better Auth session
 * 5. Use Better Auth for session management
 */
import { createAuthClient } from "better-auth/react";
import { inferAdditionalFields } from "better-auth/client/plugins";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const authClient = createAuthClient({
  baseURL: process.env.NEXT_PUBLIC_BETTER_AUTH_URL || "http://localhost:3000",
  plugins: [
    inferAdditionalFields<{
      // Custom fields we add to the session
      backendAccessToken?: string;
      backendRefreshToken?: string;
    }>(),
  ],
});

/**
 * Sign in with Google OAuth
 * After OAuth success, integrates with our backend
 */
export async function signInWithGoogle() {
  try {
    console.log("Starting Google OAuth flow...");

    // Better Auth handles the OAuth flow
    const result = await authClient.signIn.social({
      provider: "google",
      callbackURL: "/auth/success", // Custom callback to handle backend integration
    });

    return result;
  } catch (error) {
    console.error("Google sign in error:", error);
    throw error;
  }
}

/**
 * After OAuth success, send user data to backend and get JWT
 */
export async function exchangeForBackendJWT(betterAuthSession: any) {
  try {
    console.log("Exchanging Better Auth session for backend JWT...");

    const userData = {
      google_id: betterAuthSession.user.id,
      email: betterAuthSession.user.email,
      name: betterAuthSession.user.name,
      avatar_url: betterAuthSession.user.image,
    };

    console.log("Sending user data to backend:", API_URL + "/api/v1/auth/google");

    const response = await fetch(`${API_URL}/api/v1/auth/google`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Backend authentication failed:", errorText);
      throw new Error(`Backend authentication failed: ${response.status}`);
    }

    const data = await response.json();
    console.log("Received JWT tokens from backend");

    // Store tokens in localStorage for API calls
    localStorage.setItem("backend_access_token", data.access_token);
    localStorage.setItem("backend_refresh_token", data.refresh_token);
    localStorage.setItem("backend_user", JSON.stringify(data.user));

    return data;
  } catch (error) {
    console.error("Backend JWT exchange error:", error);
    throw error;
  }
}

/**
 * Get the backend JWT access token for API calls
 */
export function getBackendAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("backend_access_token");
}

/**
 * Get the backend refresh token
 */
export function getBackendRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("backend_refresh_token");
}

/**
 * Refresh the backend JWT token
 */
export async function refreshBackendToken(): Promise<boolean> {
  try {
    const refreshToken = getBackendRefreshToken();
    if (!refreshToken) {
      console.log("No refresh token available");
      return false;
    }

    console.log("Refreshing backend access token...");

    const response = await fetch(`${API_URL}/api/v1/auth/refresh`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      console.error("Token refresh failed");
      return false;
    }

    const data = await response.json();
    console.log("Access token refreshed successfully");

    // Update tokens
    localStorage.setItem("backend_access_token", data.access_token);
    localStorage.setItem("backend_refresh_token", data.refresh_token);

    return true;
  } catch (error) {
    console.error("Token refresh error:", error);
    return false;
  }
}

/**
 * Sign out - clears both Better Auth and backend sessions
 */
export async function signOut() {
  try {
    console.log("Signing out...");

    // Call backend logout
    const accessToken = getBackendAccessToken();
    if (accessToken) {
      await fetch(`${API_URL}/api/v1/auth/logout`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });
    }

    // Clear backend tokens
    localStorage.removeItem("backend_access_token");
    localStorage.removeItem("backend_refresh_token");
    localStorage.removeItem("backend_user");

    // Sign out from Better Auth
    await authClient.signOut();

    console.log("Signed out successfully");
  } catch (error) {
    console.error("Sign out error:", error);
    throw error;
  }
}

/**
 * Make authenticated API call to backend
 */
export async function apiCall(endpoint: string, options: RequestInit = {}) {
  let accessToken = getBackendAccessToken();

  // Try to refresh token if it doesn't exist
  if (!accessToken) {
    const refreshed = await refreshBackendToken();
    if (refreshed) {
      accessToken = getBackendAccessToken();
    } else {
      throw new Error("Not authenticated");
    }
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: `Bearer ${accessToken}`,
    },
  });

  // If unauthorized, try refreshing token once
  if (response.status === 401) {
    const refreshed = await refreshBackendToken();
    if (refreshed) {
      accessToken = getBackendAccessToken();
      return fetch(`${API_URL}${endpoint}`, {
        ...options,
        headers: {
          ...options.headers,
          Authorization: `Bearer ${accessToken}`,
        },
      });
    }
  }

  return response;
}
