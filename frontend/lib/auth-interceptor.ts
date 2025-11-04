import { refreshBackendToken } from "./auth-client";

interface TokenData {
  exp: number;
  iat: number;
}

function parseJWT(token: string): TokenData | null {
  try {
    const base64Url = token.split(".")[1];
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join("")
    );
    return JSON.parse(jsonPayload);
  } catch (e) {
    console.error("Failed to parse JWT:", e);
    return null;
  }
}

function isTokenExpired(token: string): boolean {
  const decoded = parseJWT(token);
  if (!decoded || !decoded.exp) return true;
  
  const currentTime = Math.floor(Date.now() / 1000);
  const bufferTime = 60; // Refresh 60 seconds before expiration
  
  return decoded.exp - currentTime < bufferTime;
}

let isRefreshing = false;
let refreshSubscribers: Array<(token: string) => void> = [];

function subscribeTokenRefresh(callback: (token: string) => void) {
  refreshSubscribers.push(callback);
}

function onTokenRefreshed(token: string) {
  refreshSubscribers.forEach((callback) => callback(token));
  refreshSubscribers = [];
}

export async function getValidAccessToken(): Promise<string | null> {
  if (typeof window === "undefined") return null;

  let accessToken = localStorage.getItem("backend_access_token");
  
  if (!accessToken) {
    const cookies = document.cookie.split("; ");
    const tokenCookie = cookies.find((row) => row.startsWith("backend_access_token="));
    if (tokenCookie) {
      accessToken = tokenCookie.split("=")[1];
      localStorage.setItem("backend_access_token", accessToken);
    }
  }

  if (!accessToken) {
    console.warn("[Auth] No access token found");
    return null;
  }

  // Check if token is expired or about to expire
  if (!isTokenExpired(accessToken)) {
    return accessToken;
  }

  console.log("[Auth] Access token expired, attempting refresh...");

  // If already refreshing, wait for the refresh to complete
  if (isRefreshing) {
    return new Promise((resolve) => {
      subscribeTokenRefresh((token: string) => {
        resolve(token);
      });
    });
  }

  isRefreshing = true;

  try {
    const refreshToken = localStorage.getItem("backend_refresh_token");
    if (!refreshToken) {
      console.warn("[Auth] No refresh token found, redirecting to login");
      clearAuthAndRedirect();
      return null;
    }

    // Check if refresh token is also expired
    if (isTokenExpired(refreshToken)) {
      console.warn("[Auth] Refresh token expired, redirecting to login");
      clearAuthAndRedirect();
      return null;
    }

    // Attempt to refresh the token
    const newTokens = await refreshBackendToken(refreshToken);
    
    if (newTokens) {
      console.log("[Auth] Token refreshed successfully");
      isRefreshing = false;
      onTokenRefreshed(newTokens.access_token);
      return newTokens.access_token;
    } else {
      console.warn("[Auth] Token refresh failed, redirecting to login");
      clearAuthAndRedirect();
      return null;
    }
  } catch (error) {
    console.error("[Auth] Error during token refresh:", error);
    clearAuthAndRedirect();
    return null;
  } finally {
    isRefreshing = false;
  }
}

function clearAuthAndRedirect() {
  // Clear all auth data
  localStorage.removeItem("backend_access_token");
  localStorage.removeItem("backend_refresh_token");
  localStorage.removeItem("backend_user");
  localStorage.removeItem("backend_session_id");
  
  // Clear cookies
  document.cookie = "backend_access_token=; path=/; max-age=0";
  document.cookie = "backend_refresh_token=; path=/; max-age=0";
  document.cookie = "backend_session_id=; path=/; max-age=0";
  
  // Redirect to login
  if (typeof window !== "undefined" && window.location.pathname !== "/login") {
    window.location.href = "/login";
  }
}

export async function getAuthHeaders(): Promise<Record<string, string>> {
  const token = await getValidAccessToken();
  
  if (token) {
    return {
      Authorization: `Bearer ${token}`,
    };
  }
  
  return {};
}

