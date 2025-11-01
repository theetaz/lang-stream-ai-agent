"use client";

import { useEffect, useRef, useState } from "react";
import { ChatMessage, type Message } from "@/components/chat-message";
import { ChatInput } from "@/components/chat-input";
import { ThemeToggle } from "@/components/theme-toggle";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Bot, Sparkles, LogOut, Loader2 } from "lucide-react";
import { useChatStream, type StreamEvent } from "@/lib/hooks/use-chat-stream";
import { ToolCall, type ToolCallData } from "@/components/tool-call";
import { useSession, signOut } from "@/lib/auth-client";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

export default function Home() {
  const router = useRouter();
  const { data: session, isPending } = useSession();
  const [messages, setMessages] = useState<Message[]>([]);
  const [streamingMessage, setStreamingMessage] = useState<string>("");
  const [streamingToolCalls, setStreamingToolCalls] = useState<ToolCallData[]>([]);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!isPending && !session) {
      router.push("/login");
    }
  }, [isPending, session, router]);

  // Show loading state while checking authentication
  if (isPending) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  // Don't render anything if not authenticated (will redirect)
  if (!session) {
    return null;
  }

  const handleSignOut = async () => {
    await signOut();
    router.push("/login");
  };

  const getUserInitials = () => {
    if (!session.user?.name) return "U";
    return session.user.name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  // Auto-scroll to bottom when new messages arrive or during streaming
  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollElement = scrollAreaRef.current;
      const isNearBottom =
        scrollElement.scrollHeight - scrollElement.scrollTop - scrollElement.clientHeight < 100;

      // Only auto-scroll if user is near the bottom (not scrolled up to read)
      if (isNearBottom || streamingMessage || streamingToolCalls.length > 0) {
        scrollElement.scrollTop = scrollElement.scrollHeight;
      }
    }
  }, [messages, streamingMessage, streamingToolCalls]);

  const handleToolEvent = (event: StreamEvent) => {
    if (event.type === "tool_start") {
      // Tool execution started - add a new tool call
      setStreamingToolCalls((prev) => [
        ...prev,
        {
          id: `tool-${Date.now()}`,
          tool: "search",
          status: "running",
        },
      ]);
    } else if (event.type === "tool_call" && event.tool && event.input) {
      // Update the last tool call with actual details
      setStreamingToolCalls((prev) => {
        const updated = [...prev];
        const lastIndex = updated.length - 1;
        if (lastIndex >= 0) {
          updated[lastIndex] = {
            ...updated[lastIndex],
            tool: event.tool || "",
            input: event.input,
            status: "running",
          };
        }
        return updated;
      });
    } else if (event.type === "tool_result" && event.result) {
      // Mark the last tool call as complete with result
      setStreamingToolCalls((prev) => {
        const updated = [...prev];
        const lastIndex = updated.length - 1;
        if (lastIndex >= 0) {
          updated[lastIndex] = {
            ...updated[lastIndex],
            result: event.result,
            status: "complete",
          };
        }
        return updated;
      });
    }
  };

  const { streamMessage, isStreaming, error } = useChatStream({
    onChunk: (chunk) => {
      setStreamingMessage((prev) => prev + chunk);
    },
    onToolEvent: handleToolEvent,
    onComplete: (fullMessage) => {
      // Add the complete assistant message with tool calls
      const assistantMessage: Message = {
        id: Date.now().toString(),
        role: "assistant",
        content: fullMessage,
        toolCalls: streamingToolCalls.length > 0 ? streamingToolCalls : undefined,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setStreamingMessage("");
      setStreamingToolCalls([]);
    },
    onError: (error) => {
      console.error("Stream error:", error);
      // Add error message
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: "assistant",
        content: `Sorry, I encountered an error: ${error.message}. Please make sure the backend is running with valid API keys.`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
      setStreamingMessage("");
      setStreamingToolCalls([]);
    },
  });

  const handleSendMessage = async (content: string) => {
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);

    // Start streaming
    await streamMessage(content);
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

        <div className="flex items-center gap-2">
          <ThemeToggle />

          {/* User Profile Dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="relative h-9 w-9 rounded-full">
                <Avatar className="h-9 w-9">
                  <AvatarImage src={session.user?.image || undefined} alt={session.user?.name || "User"} />
                  <AvatarFallback className="bg-gradient-to-br from-blue-600 to-purple-600 text-white">
                    {getUserInitials()}
                  </AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-56" align="end" forceMount>
              <DropdownMenuLabel className="font-normal">
                <div className="flex flex-col space-y-1">
                  <p className="text-sm font-medium leading-none">{session.user?.name || "User"}</p>
                  <p className="text-xs leading-none text-muted-foreground">
                    {session.user?.email || ""}
                  </p>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleSignOut} className="text-red-600 focus:text-red-600">
                <LogOut className="mr-2 h-4 w-4" />
                <span>Log out</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
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
              {/* Show streaming message */}
              {(isStreaming || streamingMessage || streamingToolCalls.length > 0) && (
                <div className="flex gap-3 px-4 py-6 bg-muted/50">
                  <div className="flex-shrink-0">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-blue-600 to-purple-600 text-white">
                      <Bot className="h-5 w-5" />
                    </div>
                  </div>
                  <div className="flex-1 space-y-3">
                    <p className="text-sm font-semibold">AI Assistant</p>

                    {/* Tool Calls (streaming) */}
                    {streamingToolCalls.length > 0 && (
                      <div className="space-y-2">
                        {streamingToolCalls.map((toolCall) => (
                          <ToolCall key={toolCall.id} toolCall={toolCall} />
                        ))}
                      </div>
                    )}

                    {/* Streaming text */}
                    {streamingMessage ? (
                      <div className="prose prose-sm dark:prose-invert max-w-none">
                        <p className="whitespace-pre-wrap text-sm leading-relaxed">
                          {streamingMessage}
                          <span className="inline-block w-1 h-4 ml-1 bg-current animate-pulse" />
                        </p>
                      </div>
                    ) : !streamingToolCalls.length ? (
                      <div className="flex gap-1">
                        <div className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.3s]"></div>
                        <div className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.15s]"></div>
                        <div className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground"></div>
                      </div>
                    ) : null}
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
              disabled={isStreaming}
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
