import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  
  const token = localStorage.getItem("backend_access_token");
  
  if (!token) {
    const cookies = document.cookie.split("; ");
    const tokenCookie = cookies.find(row => row.startsWith("backend_access_token="));
    if (tokenCookie) {
      return tokenCookie.split("=")[1];
    }
  }
  
  return token;
}

export function getAuthHeaders(): Record<string, string> {
  const token = getAuthToken();
  
  if (token) {
    return {
      "Authorization": `Bearer ${token}`
    };
  }
  
  return {};
}
