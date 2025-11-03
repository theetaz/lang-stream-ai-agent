"use client";

import { useRef, useState, useEffect } from "react";
import { ChatMessage, type Message } from "@/components/chat-message";
import { ChatInput } from "@/components/chat-input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useChatStream, type StreamEvent } from "@/lib/hooks/use-chat-stream";
import { type ToolCallData } from "@/components/tool-call";
import { ChatHeader } from "./chat-header";
import { ChatEmptyState } from "./chat-empty-state";
import { StreamingMessage } from "./streaming-message";

interface ChatContainerProps {
  user: {
    name?: string;
    email?: string;
    image?: string;
  };
}

export function ChatContainer({ user }: ChatContainerProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [streamingMessage, setStreamingMessage] = useState<string>("");
  const [streamingToolCalls, setStreamingToolCalls] = useState<ToolCallData[]>([]);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

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
          <div className="mx-auto max-w-3xl p-4">
            <ChatInput onSend={handleSendMessage} disabled={isStreaming} placeholder="Ask anything..." />
            <p className="mt-2 text-center text-xs text-muted-foreground">
              LangGraph AI can make mistakes. Check important info.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

