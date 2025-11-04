"use client"

import * as React from "react"
import { FileText, Loader2, CheckCircle2, XCircle, Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { ProcessingStatus, type UploadedFile } from "@/lib/types/file"

interface FileListProps {
  files: UploadedFile[]
  onDelete?: (fileId: string) => void
  className?: string
}

export function FileList({ files, onDelete, className }: FileListProps) {
  if (files.length === 0) {
    return null
  }

  const getStatusIcon = (status: ProcessingStatus) => {
    switch (status) {
      case ProcessingStatus.COMPLETED:
        return <CheckCircle2 className="h-4 w-4 text-green-500" />
      case ProcessingStatus.PROCESSING:
      case ProcessingStatus.PENDING:
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
      case ProcessingStatus.FAILED:
        return <XCircle className="h-4 w-4 text-red-500" />
      default:
        return <FileText className="h-4 w-4 text-muted-foreground" />
    }
  }

  const getStatusText = (status: ProcessingStatus) => {
    switch (status) {
      case ProcessingStatus.COMPLETED:
        return "Ready"
      case ProcessingStatus.PROCESSING:
        return "Processing..."
      case ProcessingStatus.PENDING:
        return "Pending..."
      case ProcessingStatus.FAILED:
        return "Failed"
      default:
        return status
    }
  }

  const formatFileSize = (bytes: number | null) => {
    if (!bytes) return "Unknown size"
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div className={cn("space-y-2", className)}>
      <div className="text-sm font-medium text-muted-foreground">
        Uploaded Files ({files.length})
      </div>
      <div className="space-y-1">
        {files.map((file) => (
          <div
            key={file.id}
            className="flex items-center justify-between gap-2 rounded-md border bg-card p-2 text-sm"
          >
            <div className="flex items-center gap-2 min-w-0 flex-1">
              <FileText className="h-4 w-4 flex-shrink-0 text-muted-foreground" />
              <div className="min-w-0 flex-1">
                <div className="truncate font-medium">{file.filename}</div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span>{formatFileSize(file.file_size)}</span>
                  <span>•</span>
                  <div className="flex items-center gap-1">
                    {getStatusIcon(file.processing_status)}
                    <span>{getStatusText(file.processing_status)}</span>
                  </div>
                </div>
              </div>
            </div>
            {onDelete && (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => onDelete(file.id)}
                className="h-8 w-8 flex-shrink-0"
                title="Delete file"
              >
                <Trash2 className="h-3.5 w-3.5" />
                <span className="sr-only">Delete</span>
              </Button>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

