"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function Home() {
  const [backendStatus, setBackendStatus] = useState<string>("Checking...");
  const [backendMessage, setBackendMessage] = useState<string>("");

  useEffect(() => {
    // Test connection to backend
    api
      .health()
      .then((data) => {
        setBackendStatus("Connected ✓");
        setBackendMessage(data.message || "Backend is running");
      })
      .catch((error) => {
        setBackendStatus("Failed to connect ✗");
        setBackendMessage(error.message);
      });
  }, []);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-zinc-50 to-zinc-100 dark:from-zinc-900 dark:to-black">
      <main className="flex flex-col items-center gap-8 p-8 max-w-2xl">
        <div className="text-center space-y-4">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            LangGraph AI Agent
          </h1>
          <p className="text-xl text-zinc-600 dark:text-zinc-400">
            Full-stack AI Agent with FastAPI & Next.js
          </p>
        </div>

        <div className="w-full bg-white dark:bg-zinc-800 rounded-lg shadow-lg p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
              Backend Status
            </h2>
            <span
              className={`px-3 py-1 rounded-full text-sm font-medium ${
                backendStatus.includes("Connected")
                  ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100"
                  : backendStatus.includes("Failed")
                  ? "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100"
                  : "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100"
              }`}
            >
              {backendStatus}
            </span>
          </div>
          {backendMessage && (
            <p className="text-sm text-zinc-600 dark:text-zinc-400">
              {backendMessage}
            </p>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full">
          <div className="bg-white dark:bg-zinc-800 rounded-lg shadow p-4 space-y-2">
            <h3 className="font-semibold text-zinc-900 dark:text-zinc-100">
              Frontend
            </h3>
            <p className="text-sm text-zinc-600 dark:text-zinc-400">
              Next.js 15 with TypeScript
            </p>
          </div>
          <div className="bg-white dark:bg-zinc-800 rounded-lg shadow p-4 space-y-2">
            <h3 className="font-semibold text-zinc-900 dark:text-zinc-100">
              Backend
            </h3>
            <p className="text-sm text-zinc-600 dark:text-zinc-400">
              FastAPI with LangGraph
            </p>
          </div>
          <div className="bg-white dark:bg-zinc-800 rounded-lg shadow p-4 space-y-2">
            <h3 className="font-semibold text-zinc-900 dark:text-zinc-100">
              UI Library
            </h3>
            <p className="text-sm text-zinc-600 dark:text-zinc-400">
              shadcn/ui + Tailwind
            </p>
          </div>
        </div>

        <div className="text-center text-sm text-zinc-500 dark:text-zinc-400">
          <p>Edit app/page.tsx to get started building your AI agent!</p>
        </div>
      </main>
    </div>
  );
}
