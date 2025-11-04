"use client";

import { useRef, useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ChatMessage, type Message } from "@/components/chat-message";
import { ChatInput } from "@/components/chat-input";
import { FileList } from "@/components/file-list";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useChatStream, type StreamEvent } from "@/lib/hooks/use-chat-stream";
import { type ToolCallData } from "@/components/tool-call";
import { ChatHeader } from "./chat-header";
import { ChatEmptyState } from "./chat-empty-state";
import { StreamingMessage } from "./streaming-message";
import { uploadFile, getFiles, deleteFile } from "@/lib/api/files";
import { useToast } from "@/hooks/use-toast";
import type { UploadedFile } from "@/lib/types/file";

interface ChatContainerProps {
  user: {
    name?: string;
    email?: string;
    image?: string;
  };
  sessionId?: string;
}

export function ChatContainer({ user, sessionId }: ChatContainerProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [streamingMessage, setStreamingMessage] = useState<string>("");
  const [streamingToolCalls, setStreamingToolCalls] = useState<ToolCallData[]>([]);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const { data: filesData, refetch: refetchFiles } = useQuery({
    queryKey: ["files", sessionId],
    queryFn: () => getFiles(sessionId),
    refetchInterval: 5000, // Refetch every 5 seconds to update processing status
  });

  const files = filesData?.data || [];

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadFile(file, sessionId),
    onSuccess: (data) => {
      refetchFiles();
      toast({
        title: "File uploaded",
        description: `${data.data?.filename} is being processed`,
      });
    },
    onError: (error: Error) => {
      toast({
        title: "Upload failed",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (fileId: string) => deleteFile(fileId),
    onSuccess: () => {
      refetchFiles();
      toast({
        title: "File deleted",
        description: "File removed successfully",
      });
    },
    onError: (error: Error) => {
      toast({
        title: "Delete failed",
        description: error.message,
        variant: "destructive",
      });
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

  const handleSendMessage = async (content: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    await streamMessage(content);
  };

  const handleFileSelect = (file: File) => {
    uploadMutation.mutate(file);
  };

  const handleFileDelete = (fileId: string) => {
    deleteMutation.mutate(fileId);
  };

  return (
    <div className="flex h-screen flex-col bg-background">
      <ChatHeader user={user} />

      <div className="flex flex-1 flex-col overflow-hidden">
        {messages.length === 0 ? (
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
          <div className="mx-auto max-w-3xl p-4 space-y-3">
            {files.length > 0 && (
              <FileList files={files} onDelete={handleFileDelete} />
            )}
            <ChatInput
              onSend={handleSendMessage}
              onFileSelect={handleFileSelect}
              disabled={isStreaming}
              isUploading={uploadMutation.isPending}
              placeholder="Ask anything..."
            />
            <p className="text-center text-xs text-muted-foreground">
              LangGraph AI can make mistakes. Check important info.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
