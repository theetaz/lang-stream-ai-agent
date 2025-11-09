"use client";

import { useRef, useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ChatMessage, type Message } from "@/components/chat-message";
import { ChatInput } from "@/components/chat-input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useChatStream, type StreamEvent } from "@/lib/hooks/use-chat-stream";
import { type ToolCallData } from "@/components/tool-call";
import { ChatHeader } from "./chat-header";
import { ChatEmptyState } from "./chat-empty-state";
import { StreamingMessage } from "./streaming-message";
import { SessionSidebar } from "./session-sidebar";
import { uploadFile } from "@/lib/api/files";
import { createSession, getSessionMessages } from "@/lib/api/sessions";
import { useToast } from "@/hooks/use-toast";
import type { UploadedFile } from "@/lib/types/file";

interface ChatContainerProps {
  user: {
    name?: string;
    email?: string;
    image?: string;
  };
  initialSessionId?: string;
}

export function ChatContainer({ user, initialSessionId }: ChatContainerProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(initialSessionId || null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [streamingMessage, setStreamingMessage] = useState<string>("");
  const [streamingToolCalls, setStreamingToolCalls] = useState<ToolCallData[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [isNewSession, setIsNewSession] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  // Load message history when session changes (but not for new sessions)
  useEffect(() => {
    if (currentSessionId && !isNewSession) {
      loadSessionHistory(currentSessionId);
    } else if (!currentSessionId) {
      setMessages([]);
    }
    
    if (isNewSession) {
      setIsNewSession(false);
    }
  }, [currentSessionId]);

  const loadSessionHistory = async (sessionId: string) => {
    setIsLoadingHistory(true);
    try {
      const response = await getSessionMessages(sessionId);
      if (response.data) {
        const historyMessages: Message[] = response.data.map((msg) => ({
          id: msg.id,
          role: msg.role as "user" | "assistant",
          content: msg.content,
          timestamp: new Date(msg.created_at),
        }));
        setMessages(historyMessages);
      }
    } catch (error) {
      console.error("Failed to load session history:", error);
      toast({
        title: "Failed to load history",
        description: "Could not load conversation history",
        variant: "destructive",
      });
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const uploadMutation = useMutation({
    mutationFn: ({ file, sessionId }: { file: File; sessionId?: string }) =>
      uploadFile(file, sessionId),
  });

  const createSessionMutation = useMutation({
    mutationFn: () => createSession("New Chat"),
    onSuccess: (data) => {
      if (data.data) {
        setIsNewSession(true);
        setCurrentSessionId(data.data.id);
        queryClient.invalidateQueries({ queryKey: ["sessions"] });
        router.push(`/chat/${data.data.id}`);
      }
    },
  });

  const handleToolEvent = (event: StreamEvent) => {
    if (event.type === "tool_start") {
      setStreamingToolCalls((prev) => [
        ...prev,
        {
          id: `tool-${Date.now()}`,
          tool: "search",
          status: "running",
        },
      ]);
    } else if (event.type === "tool_call" && event.tool && event.input) {
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

  const { streamMessage, isStreaming } = useChatStream({
    onChunk: (chunk) => {
      setStreamingMessage((prev) => prev + chunk);
    },
    onToolEvent: handleToolEvent,
    onComplete: (fullMessage) => {
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
      
      queryClient.invalidateQueries({ queryKey: ["sessions"] });
    },
    onError: (error) => {
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

  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollElement = scrollAreaRef.current;
      const isNearBottom =
        scrollElement.scrollHeight - scrollElement.scrollTop - scrollElement.clientHeight < 100;

      if (isNearBottom || streamingMessage || streamingToolCalls.length > 0) {
        scrollElement.scrollTop = scrollElement.scrollHeight;
      }
    }
  }, [messages, streamingMessage, streamingToolCalls]);

  const handleSendMessage = async (content: string, files?: File[]) => {
    // Create session if this is the first message
    let sessionId = currentSessionId;
    if (!sessionId) {
      const response = await createSessionMutation.mutateAsync();
      if (!response.data) {
        toast({
          title: "Error",
          description: "Failed to create chat session",
          variant: "destructive",
        });
        return;
      }
      sessionId = response.data.id;
    }

    // Upload files first if any
    const uploadedFiles: UploadedFile[] = [];
    if (files && files.length > 0) {
      try {
        for (const file of files) {
          const result = await uploadMutation.mutateAsync({
            file,
            sessionId: sessionId || undefined,
          });
          if (result.data) {
            uploadedFiles.push(result.data);
          }
        }
      } catch (error) {
        toast({
          title: "Upload failed",
          description: "Failed to upload files",
          variant: "destructive",
        });
        return;
      }
    }

    // Create user message with attachments
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content,
      attachments: uploadedFiles.length > 0 ? uploadedFiles : undefined,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    
    // Send to AI
    setTimeout(async () => {
      await streamMessage(content, sessionId);
    }, 100);
  };

  // Handle initial message from URL query param
  useEffect(() => {
    const initialMessage = searchParams?.get("message");
    if (initialMessage && currentSessionId && messages.length === 0 && !isLoadingHistory) {
      // Send message after a short delay to ensure session is loaded
      setTimeout(() => {
        handleSendMessage(initialMessage);
        // Remove message from URL
        router.replace(`/chat/${currentSessionId}`, { scroll: false });
      }, 500);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentSessionId, searchParams, messages.length, isLoadingHistory]);

  const handleNewSession = () => {
    router.push("/");
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
        currentSessionId={currentSessionId}
        onSessionSelect={handleSessionSelect}
        onNewSession={handleNewSession}
      />

      <div className="flex flex-1 flex-col overflow-hidden">
        <ChatHeader user={user} />

        <div className="flex flex-1 flex-col overflow-hidden">
          {isLoadingHistory ? (
            <div className="flex flex-1 items-center justify-center">
              <div className="text-muted-foreground">Loading conversation...</div>
            </div>
          ) : messages.length === 0 ? (
            <ChatEmptyState />
          ) : (
            <ScrollArea ref={scrollAreaRef} className="flex-1">
              <div className="mx-auto max-w-3xl">
                {messages.map((message) => (
                  <ChatMessage key={message.id} message={message} />
                ))}
                {(isStreaming || streamingMessage || streamingToolCalls.length > 0) && (
                  <StreamingMessage
                    message={streamingMessage}
                    toolCalls={streamingToolCalls}
                    isStreaming={isStreaming}
                  />
                )}
              </div>
            </ScrollArea>
          )}

          <div className="border-t bg-background">
            <div className="mx-auto max-w-3xl p-4">
              <ChatInput
                onSend={handleSendMessage}
                disabled={isStreaming}
                isUploading={uploadMutation.isPending}
                placeholder="Ask anything..."
              />
              <p className="mt-2 text-center text-xs text-muted-foreground">
                LangGraph AI can make mistakes. Check important info.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
