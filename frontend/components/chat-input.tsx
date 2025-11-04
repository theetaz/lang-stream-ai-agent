"use client"

import * as React from "react"
import { Send, X, FileText } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { FileUploadButton } from "@/components/file-upload-button"
import { cn } from "@/lib/utils"

interface ChatInputProps {
  onSend: (message: string, files?: File[]) => void
  disabled?: boolean
  isUploading?: boolean
  placeholder?: string
}

export function ChatInput({
  onSend,
  disabled = false,
  isUploading = false,
  placeholder = "Ask anything...",
}: ChatInputProps) {
  const [input, setInput] = React.useState("")
  const [selectedFiles, setSelectedFiles] = React.useState<File[]>([])
  const textareaRef = React.useRef<HTMLTextAreaElement>(null)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if ((input.trim() || selectedFiles.length > 0) && !disabled) {
      onSend(input.trim(), selectedFiles)
      setInput("")
      setSelectedFiles([])
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
    setSelectedFiles((prev) => [...prev, file])
  }

  const removeFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
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
      {selectedFiles.length > 0 && (
        <div className="flex flex-wrap gap-2 rounded-lg border border-input bg-background p-2">
          {selectedFiles.map((file, index) => (
            <div
              key={index}
              className="flex items-center gap-2 rounded-md border bg-muted px-3 py-2 text-sm"
            >
              <FileText className="h-4 w-4 text-muted-foreground" />
              <div className="flex flex-col min-w-0">
                <span className="truncate font-medium">{file.name}</span>
                <span className="text-xs text-muted-foreground">
                  {formatFileSize(file.size)}
                </span>
              </div>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="h-6 w-6 flex-shrink-0"
                onClick={() => removeFile(index)}
              >
                <X className="h-3 w-3" />
              </Button>
            </div>
          ))}
        </div>
      )}

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
          disabled={disabled}
          className={cn(
            "min-h-[24px] max-h-[200px] resize-none border-0 bg-transparent px-2 py-2 shadow-none focus-visible:ring-0 focus-visible:ring-offset-0",
            "scrollbar-thin scrollbar-thumb-muted-foreground/20 scrollbar-track-transparent"
          )}
          rows={1}
        />
        <Button
          type="submit"
          size="icon"
          disabled={(!input.trim() && selectedFiles.length === 0) || disabled}
          className="h-9 w-9 flex-shrink-0"
        >
          <Send className="h-4 w-4" />
          <span className="sr-only">Send message</span>
        </Button>
      </div>
    </form>
  )
}
