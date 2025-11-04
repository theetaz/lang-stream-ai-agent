"use client"

import * as React from "react"
import { Paperclip, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface FileUploadButtonProps {
  onFileSelect: (file: File) => void
  disabled?: boolean
  isUploading?: boolean
  accept?: string
  className?: string
}

export function FileUploadButton({
  onFileSelect,
  disabled = false,
  isUploading = false,
  accept = ".pdf,.doc,.docx,.txt,.md",
  className,
}: FileUploadButtonProps) {
  const inputRef = React.useRef<HTMLInputElement>(null)

  const handleClick = () => {
    inputRef.current?.click()
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      onFileSelect(file)
      // Reset input so same file can be selected again
      e.target.value = ""
    }
  }

  return (
    <>
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        onChange={handleFileChange}
        className="hidden"
        disabled={disabled || isUploading}
      />
      <Button
        type="button"
        variant="ghost"
        size="icon"
        onClick={handleClick}
        disabled={disabled || isUploading}
        className={cn("h-9 w-9 flex-shrink-0", className)}
        title="Upload file"
      >
        {isUploading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Paperclip className="h-4 w-4" />
        )}
        <span className="sr-only">Upload file</span>
      </Button>
    </>
  )
}

