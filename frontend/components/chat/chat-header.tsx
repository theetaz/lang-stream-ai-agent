"use client";

import { Bot } from "lucide-react";
import { ThemeToggle } from "@/components/theme-toggle";
import { UserMenu } from "./user-menu";

interface ChatHeaderProps {
  user: {
    name?: string;
    email?: string;
    image?: string;
  };
}

export function ChatHeader({ user }: ChatHeaderProps) {
  return (
    <header className="sticky top-0 z-10 flex h-14 items-center justify-between border-b bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex items-center gap-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-purple-600">
          <Bot className="h-5 w-5 text-white" />
        </div>
        <h1 className="text-lg font-semibold">LangGraph AI</h1>
      </div>

      <div className="flex items-center gap-2">
        <ThemeToggle />
        <UserMenu user={user} />
      </div>
    </header>
  );
}

