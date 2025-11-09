"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Sparkles, Plus, Mic, ArrowUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ChatHeader } from "./chat-header";
import { SessionSidebar } from "./session-sidebar";
import { createSession } from "@/lib/api/sessions";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useToast } from "@/hooks/use-toast";

interface ChatLandingPageProps {
  user: {
    name?: string;
    email?: string;
    image?: string;
  };
}

const SUGGESTIONS = [
  "Ask for trip planning tips",
  "Help me write a professional email",
  "Explain quantum computing",
  "Create a workout plan",
];

export function ChatLandingPage({ user }: ChatLandingPageProps) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [input, setInput] = useState("");

  const createSessionMutation = useMutation({
    mutationFn: () => createSession("New Chat"),
    onSuccess: (data) => {
      if (data.data) {
        queryClient.invalidateQueries({ queryKey: ["sessions"] });
        router.push(`/chat/${data.data.id}`);
      }
    },
    onError: () => {
      toast({
        title: "Error",
        description: "Failed to create chat session",
        variant: "destructive",
      });
    },
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const messageToSend = input.trim();
    
    try {
      const response = await createSessionMutation.mutateAsync();
      if (response.data) {
        // Store message in sessionStorage for the chat page to pick up
        sessionStorage.setItem(`pending_message_${response.data.id}`, messageToSend);
        router.push(`/chat/${response.data.id}`);
      }
    } catch (error) {
      console.error("Failed to create session:", error);
    }
  };

  const handleSuggestionClick = async (suggestion: string) => {
    setInput(suggestion);
    
    try {
      const response = await createSessionMutation.mutateAsync();
      if (response.data) {
        // Store message in sessionStorage for the chat page to pick up
        sessionStorage.setItem(`pending_message_${response.data.id}`, suggestion);
        router.push(`/chat/${response.data.id}`);
      }
    } catch (error) {
      console.error("Failed to create session:", error);
    }
  };

  const handleNewSession = () => {
    // Already on landing page, just clear input
    setInput("");
  };

  const handleSessionSelect = (sessionId: string | null) => {
    if (sessionId) {
      router.push(`/chat/${sessionId}`);
    } else {
      router.push("/");
    }
  };

  return (
    <div className="flex h-screen bg-background">
      {/* Sessions Sidebar on Left */}
      <SessionSidebar
        currentSessionId={null}
        onSessionSelect={handleSessionSelect}
        onNewSession={handleNewSession}
      />

      <div className="flex flex-1 flex-col overflow-hidden">
        <ChatHeader user={user} />

        <div className="flex flex-1 flex-col items-center justify-center p-4">
          <div className="w-full max-w-3xl space-y-8">
            {/* Logo/Icon */}
            <div className="flex justify-center">
              <div className="rounded-full bg-gradient-to-br from-blue-600 to-purple-600 p-4">
                <Sparkles className="h-12 w-12 text-white" />
              </div>
            </div>

            {/* Title */}
            <div className="text-center">
              <h1 className="text-4xl font-semibold mb-2">What can I help with?</h1>
            </div>

            {/* Input Box */}
            <form onSubmit={handleSubmit} className="relative">
              <div className="flex items-end gap-2 rounded-2xl border border-input bg-background p-4 shadow-lg">
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 flex-shrink-0"
                >
                  <Plus className="h-4 w-4" />
                </Button>
                <Textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask for trip planning tips"
                  className="min-h-[24px] max-h-[200px] resize-none border-0 bg-transparent px-2 py-2 text-base shadow-none focus-visible:ring-0 focus-visible:ring-offset-0"
                  rows={1}
                  autoFocus
                />
                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 flex-shrink-0"
                  >
                    <Mic className="h-4 w-4" />
                  </Button>
                  <Button
                    type="submit"
                    size="icon"
                    disabled={!input.trim() || createSessionMutation.isPending}
                    className="h-8 w-8 flex-shrink-0 bg-primary text-primary-foreground hover:bg-primary/90"
                  >
                    <ArrowUp className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </form>

            {/* Suggestions */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {SUGGESTIONS.map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="text-left p-4 rounded-lg border border-input bg-background hover:bg-muted/50 transition-colors text-sm"
                  disabled={createSessionMutation.isPending}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

