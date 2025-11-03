import { fetchAPI, type APIResponse } from "../api";

export interface Session {
  id: string;
  device_info: string | null;
  ip_address: string | null;
  user_agent: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_activity: string;
}

export interface SessionsListResponse {
  sessions: Session[];
}

export async function getSessions(token: string): Promise<APIResponse<SessionsListResponse>> {
  return fetchAPI("/api/v1/auth/sessions", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}

export async function removeSession(token: string, sessionId: string): Promise<APIResponse<{ message: string }>> {
  return fetchAPI(`/api/v1/auth/sessions/${sessionId}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}

export async function removeAllSessions(token: string): Promise<APIResponse<{ message: string }>> {
  return fetchAPI("/api/v1/auth/sessions/all", {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}

