"use client";

import { Bot } from "lucide-react";
import { ToolCall, type ToolCallData } from "@/components/tool-call";

interface StreamingMessageProps {
  message: string;
  toolCalls: ToolCallData[];
  isStreaming: boolean;
}

export function StreamingMessage({ message, toolCalls, isStreaming }: StreamingMessageProps) {
  return (
    <div className="flex gap-3 px-4 py-6 bg-muted/50">
      <div className="flex-shrink-0">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-blue-600 to-purple-600 text-white">
          <Bot className="h-5 w-5" />
        </div>
      </div>
      <div className="flex-1 space-y-3">
        <p className="text-sm font-semibold">AI Assistant</p>

        {toolCalls.length > 0 && (
          <div className="space-y-2">
            {toolCalls.map((toolCall) => (
              <ToolCall key={toolCall.id} toolCall={toolCall} />
            ))}
          </div>
        )}

        {message ? (
          <div className="prose prose-sm dark:prose-invert max-w-none">
            <p className="whitespace-pre-wrap text-sm leading-relaxed">
              {message}
              <span className="inline-block w-1 h-4 ml-1 bg-current animate-pulse" />
            </p>
          </div>
        ) : !toolCalls.length ? (
          <div className="flex gap-1">
            <div className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.3s]"></div>
            <div className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.15s]"></div>
            <div className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground"></div>
          </div>
        ) : null}
      </div>
    </div>
  );
}

