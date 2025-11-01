const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchAPI(endpoint: string, options?: RequestInit) {
  const url = `${API_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.statusText}`);
  }

  return response.json();
}

export interface ChatMessage {
  input: string;
}

export interface ChatResponse {
  response: string;
}

export const api = {
  // Health check
  health: () => fetchAPI('/'),

  // Chat endpoint
  chat: async (message: string): Promise<ChatResponse> => {
    return fetchAPI('/api/v1/chat', {
      method: 'POST',
      body: JSON.stringify({ input: message }),
    });
  },
};
