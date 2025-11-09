import { fetchAPI, APIResponse } from "../api";
import { getAuthHeaders } from "../auth-interceptor";
import type { UploadedFile } from "../types/file";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function uploadFile(
  file: File,
  sessionId?: string
): Promise<APIResponse<UploadedFile>> {
  const authHeaders = await getAuthHeaders();
  
  if (!authHeaders.Authorization) {
    throw new Error("Not authenticated. Please log in again.");
  }

  if (!sessionId) {
    throw new Error("Session ID is required for file upload");
  }

  const formData = new FormData();
  formData.append("file", file);
  formData.append("session_id", sessionId);

  const url = `${API_URL}/api/v1/files/upload`;

  const response = await fetch(url, {
    method: "POST",
    headers: authHeaders,
    body: formData,
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.message || "File upload failed");
  }

  return data;
}

export async function getFiles(
  sessionId?: string,
  limit = 50,
  offset = 0
): Promise<APIResponse<UploadedFile[]>> {
  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
  });

  if (sessionId) {
    params.append("session_id", sessionId);
  }

  return fetchAPI(`/api/v1/files?${params.toString()}`);
}

export async function deleteFile(
  fileId: string
): Promise<APIResponse<{ file_id: string }>> {
  return fetchAPI(`/api/v1/files/${fileId}`, {
    method: "DELETE",
  });
}

