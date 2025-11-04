import { getAuthHeaders } from "./auth-interceptor";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface APIResponse<T> {
  success: boolean;
  message: string;
  data: T | null;
  metadata?: Record<string, unknown> | null;
}

export async function fetchAPI<T>(
  endpoint: string,
  options?: RequestInit
): Promise<APIResponse<T>> {
  const url = `${API_URL}${endpoint}`;
  const authHeaders = await getAuthHeaders();

  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders,
      ...options?.headers
    }
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.message || `API request failed: ${response.statusText}`
    );
  }

  return data;
}

export interface ChatMessage {
  input: string;
}

export interface ChatResponse {
  response: string;
}

export const api = {
  health: () => fetchAPI("/"),
  chat: async (message: string): Promise<APIResponse<ChatResponse>> => {
    return fetchAPI("/api/v1/chat", {
      method: "POST",
      body: JSON.stringify({ input: message })
    });
  }
};
