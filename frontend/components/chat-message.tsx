import { cn } from "@/lib/utils"
import { Bot, User } from "lucide-react"
import { ToolCall, type ToolCallData } from "@/components/tool-call"
import { MessageAttachment } from "@/components/message-attachment"
import type { UploadedFile } from "@/lib/types/file"

export interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  toolCalls?: ToolCallData[]
  attachments?: UploadedFile[]
  timestamp?: Date
}

interface ChatMessageProps {
  message: Message
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user"

  return (
    <div
      className={cn(
        "flex w-full gap-3 px-4 py-6",
        isUser ? "bg-background" : "bg-muted/50"
      )}
    >
      <div className="flex-shrink-0">
        {isUser ? (
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground">
            <User className="h-5 w-5" />
          </div>
        ) : (
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-blue-600 to-purple-600 text-white">
            <Bot className="h-5 w-5" />
          </div>
        )}
      </div>
      <div className="flex-1 space-y-3">
        <p className="text-sm font-semibold">
          {isUser ? "You" : "AI Assistant"}
        </p>

        {/* File Attachments */}
        {message.attachments && message.attachments.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {message.attachments.map((file) => (
              <MessageAttachment
                key={file.id}
                filename={file.filename}
                fileSize={file.file_size}
                processingStatus={file.processing_status}
              />
            ))}
          </div>
        )}

        {/* Tool Calls */}
        {message.toolCalls && message.toolCalls.length > 0 && (
          <div className="space-y-2">
            {message.toolCalls.map((toolCall) => (
              <ToolCall key={toolCall.id} toolCall={toolCall} />
            ))}
          </div>
        )}

        {/* Message Content */}
        {message.content && (
          <div className="prose prose-sm dark:prose-invert max-w-none">
            <p className="whitespace-pre-wrap text-sm leading-relaxed">
              {message.content}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
