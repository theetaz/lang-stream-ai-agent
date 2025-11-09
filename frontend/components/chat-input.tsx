"use client"

import * as React from "react"
import { Send } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { FileUploadButton } from "@/components/file-upload-button"
import { cn } from "@/lib/utils"

interface ChatInputProps {
  onSend: (message: string, files?: File[]) => void
  onFileUpload?: (file: File) => void
  disabled?: boolean
  isUploading?: boolean
  placeholder?: string
}

export function ChatInput({
  onSend,
  onFileUpload,
  disabled = false,
  isUploading = false,
  placeholder = "Ask anything...",
}: ChatInputProps) {
  const [input, setInput] = React.useState("")
  const textareaRef = React.useRef<HTMLTextAreaElement>(null)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim() && !disabled) {
      onSend(input.trim())
      setInput("")
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto"
      }
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const handleFileSelect = (file: File) => {
    // If onFileUpload callback is provided, upload immediately
    if (onFileUpload) {
      onFileUpload(file)
    } else {
      // Fallback: pass files with message (old behavior)
      // This shouldn't happen with the new flow
      console.warn("onFileUpload not provided, files will be sent with message")
    }
  }

  React.useEffect(() => {
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = "auto"
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`
    }
  }, [input])

  return (
    <form
      onSubmit={handleSubmit}
      className="relative flex flex-col gap-2"
    >
      <div className="flex items-end gap-2 rounded-lg border border-input bg-background p-2">
        <FileUploadButton
          onFileSelect={handleFileSelect}
          disabled={disabled || isUploading}
          isUploading={isUploading}
        />
        <Textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled || isUploading}
          className={cn(
            "min-h-[24px] max-h-[200px] resize-none border-0 bg-transparent px-2 py-2 shadow-none focus-visible:ring-0 focus-visible:ring-offset-0",
            "scrollbar-thin scrollbar-thumb-muted-foreground/20 scrollbar-track-transparent"
          )}
          rows={1}
        />
        <Button
          type="submit"
          size="icon"
          disabled={!input.trim() || disabled || isUploading}
          className="h-9 w-9 flex-shrink-0"
        >
          <Send className="h-4 w-4" />
          <span className="sr-only">Send message</span>
        </Button>
      </div>
    </form>
  )
}
