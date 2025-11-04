import { fetchAPI, APIResponse } from "../api";

export interface ChatSession {
  id: string;
  user_id: number;
  title: string | null;
  created_at: string;
  updated_at: string;
  last_message_at: string | null;
  is_archived: boolean;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: "user" | "assistant" | "system" | "tool";
  content: string;
  created_at: string;
}

export async function createSession(
  title: string
): Promise<APIResponse<ChatSession>> {
  return fetchAPI("/api/v1/chat/sessions", {
    method: "POST",
    body: JSON.stringify({ title }),
  });
}

export async function getSessions(
  archived: boolean = false,
  limit: number = 50,
  offset: number = 0
): Promise<APIResponse<ChatSession[]>> {
  const params = new URLSearchParams({
    archived: archived.toString(),
    limit: limit.toString(),
    offset: offset.toString(),
  });
  return fetchAPI(`/api/v1/chat/sessions?${params.toString()}`);
}

export async function getSession(
  sessionId: string
): Promise<APIResponse<ChatSession>> {
  return fetchAPI(`/api/v1/chat/sessions/${sessionId}`);
}

export async function updateSession(
  sessionId: string,
  data: { title?: string; is_archived?: boolean }
): Promise<APIResponse<ChatSession>> {
  return fetchAPI(`/api/v1/chat/sessions/${sessionId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteSession(
  sessionId: string
): Promise<APIResponse<{ session_id: string }>> {
  return fetchAPI(`/api/v1/chat/sessions/${sessionId}`, {
    method: "DELETE",
  });
}

export async function getSessionMessages(
  sessionId: string,
  limit: number = 50,
  offset: number = 0
): Promise<APIResponse<ChatMessage[]>> {
  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
  });
  return fetchAPI(
    `/api/v1/chat/sessions/${sessionId}/messages?${params.toString()}`
  );
}
