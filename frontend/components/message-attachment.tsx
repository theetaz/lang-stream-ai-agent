"use client"

import { FileText, Loader2, CheckCircle2, XCircle } from "lucide-react"
import { cn } from "@/lib/utils"
import { ProcessingStatus } from "@/lib/types/file"

interface MessageAttachmentProps {
  filename: string
  fileSize: number | null
  processingStatus: ProcessingStatus
  className?: string
}

export function MessageAttachment({
  filename,
  fileSize,
  processingStatus,
  className,
}: MessageAttachmentProps) {
  const getStatusIcon = () => {
    switch (processingStatus) {
      case ProcessingStatus.COMPLETED:
        return <CheckCircle2 className="h-3 w-3 text-green-500" />
      case ProcessingStatus.PROCESSING:
      case ProcessingStatus.PENDING:
        return <Loader2 className="h-3 w-3 animate-spin text-blue-500" />
      case ProcessingStatus.FAILED:
        return <XCircle className="h-3 w-3 text-red-500" />
      default:
        return <FileText className="h-3 w-3 text-muted-foreground" />
    }
  }

  const formatFileSize = (bytes: number | null) => {
    if (!bytes) return ""
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div
      className={cn(
        "inline-flex items-center gap-2 rounded-md border bg-muted/50 px-3 py-2 text-sm",
        className
      )}
    >
      <FileText className="h-4 w-4 text-muted-foreground flex-shrink-0" />
      <div className="flex items-center gap-2 min-w-0">
        <span className="truncate font-medium">{filename}</span>
        {fileSize && (
          <span className="text-xs text-muted-foreground">
            {formatFileSize(fileSize)}
          </span>
        )}
        {getStatusIcon()}
      </div>
    </div>
  )
}

