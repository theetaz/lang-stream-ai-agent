import { fetchAPI, APIResponse } from "../api";
import { getAuthHeaders } from "../utils";
import type { UploadedFile } from "../types/file";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function uploadFile(
  file: File,
  sessionId?: string
): Promise<APIResponse<UploadedFile>> {
  const formData = new FormData();
  formData.append("file", file);

  const url = sessionId
    ? `${API_URL}/api/v1/files/upload?session_id=${sessionId}`
    : `${API_URL}/api/v1/files/upload`;

  const response = await fetch(url, {
    method: "POST",
    headers: {
      ...getAuthHeaders(),
    },
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

