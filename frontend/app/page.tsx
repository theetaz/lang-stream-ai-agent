"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { ChatMessage, type Message } from "@/components/chat-message";
import { ChatInput } from "@/components/chat-input";
import { ThemeToggle } from "@/components/theme-toggle";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Bot, Sparkles } from "lucide-react";

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = async (content: string) => {
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Call API
      const response = await api.chat(content);

      // Add assistant message
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.response,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Error sending message:", error);

      // Add error message
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Sorry, I encountered an error. Please make sure the backend is running and try again.",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen flex-col bg-background">
      {/* Header */}
      <header className="sticky top-0 z-10 flex h-14 items-center justify-between border-b bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-purple-600">
            <Bot className="h-5 w-5 text-white" />
          </div>
          <h1 className="text-lg font-semibold">LangGraph AI</h1>
        </div>
        <ThemeToggle />
      </header>

      {/* Main Content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {messages.length === 0 ? (
          // Empty State
          <div className="flex flex-1 items-center justify-center p-4">
            <div className="max-w-2xl text-center space-y-6">
              <div className="flex justify-center">
                <div className="rounded-full bg-gradient-to-br from-blue-600 to-purple-600 p-4">
                  <Sparkles className="h-12 w-12 text-white" />
                </div>
              </div>
              <div className="space-y-2">
                <h2 className="text-3xl font-bold tracking-tight">
                  What can I help with?
                </h2>
                <p className="text-muted-foreground">
                  Ask me anything and I'll do my best to help you.
                </p>
              </div>
            </div>
          </div>
        ) : (
          // Messages
          <ScrollArea ref={scrollAreaRef} className="flex-1">
            <div className="mx-auto max-w-3xl">
              {messages.map((message) => (
                <ChatMessage key={message.id} message={message} />
              ))}
              {isLoading && (
                <div className="flex gap-3 px-4 py-6 bg-muted/50">
                  <div className="flex-shrink-0">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-blue-600 to-purple-600 text-white">
                      <Bot className="h-5 w-5" />
                    </div>
                  </div>
                  <div className="flex-1 space-y-2">
                    <p className="text-sm font-semibold">AI Assistant</p>
                    <div className="flex gap-1">
                      <div className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.3s]"></div>
                      <div className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.15s]"></div>
                      <div className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground"></div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>
        )}

        {/* Input Area */}
        <div className="border-t bg-background">
          <div className="mx-auto max-w-3xl p-4">
            <ChatInput
              onSend={handleSendMessage}
              disabled={isLoading}
              placeholder="Ask anything..."
            />
            <p className="mt-2 text-center text-xs text-muted-foreground">
              LangGraph AI can make mistakes. Check important info.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
