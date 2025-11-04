"use client"

import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Plus, MessageSquare, Trash2, Archive, MoreVertical } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { getSessions, deleteSession, createSession } from "@/lib/api/sessions"
import { cn } from "@/lib/utils"
import type { ChatSession } from "@/lib/api/sessions"

interface SessionSidebarProps {
  currentSessionId: string | null
  onSessionSelect: (sessionId: string | null) => void
  onNewSession: () => void
}

export function SessionSidebar({
  currentSessionId,
  onSessionSelect,
  onNewSession,
}: SessionSidebarProps) {
  const queryClient = useQueryClient()

  const { data: sessionsData, isLoading } = useQuery({
    queryKey: ["sessions"],
    queryFn: () => getSessions(false),
    refetchInterval: 10000, // Refresh every 10 seconds
  })

  const sessions = sessionsData?.data || []

  const deleteMutation = useMutation({
    mutationFn: (sessionId: string) => deleteSession(sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sessions"] })
      if (currentSessionId) {
        onSessionSelect(null)
      }
    },
  })

  const createMutation = useMutation({
    mutationFn: () => createSession("New Chat"),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["sessions"] })
      if (data.data) {
        onSessionSelect(data.data.id)
      }
    },
  })

  const handleDelete = (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (confirm("Delete this conversation?")) {
      deleteMutation.mutate(sessionId)
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return "Just now"
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString()
  }

  return (
    <div className="flex h-full w-64 flex-col border-r bg-muted/10">
      <div className="flex items-center justify-between border-b p-4">
        <h2 className="font-semibold">Chats</h2>
        <Button
          variant="ghost"
          size="icon"
          onClick={onNewSession}
          title="New chat"
        >
          <Plus className="h-4 w-4" />
        </Button>
      </div>

      <ScrollArea className="flex-1">
        <div className="space-y-1 p-2">
          {isLoading ? (
            <div className="p-4 text-center text-sm text-muted-foreground">
              Loading...
            </div>
          ) : sessions.length === 0 ? (
            <div className="p-4 text-center text-sm text-muted-foreground">
              No conversations yet
            </div>
          ) : (
            sessions.map((session) => (
              <div
                key={session.id}
                className={cn(
                  "group flex items-center gap-2 rounded-lg p-3 hover:bg-muted cursor-pointer transition-colors",
                  currentSessionId === session.id && "bg-muted"
                )}
                onClick={() => onSessionSelect(session.id)}
              >
                <MessageSquare className="h-4 w-4 flex-shrink-0 text-muted-foreground" />
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-medium">
                    {session.title || "New Chat"}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {formatDate(session.last_message_at || session.created_at)}
                  </div>
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 opacity-0 group-hover:opacity-100"
                    >
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem
                      onClick={(e) => handleDelete(session.id, e)}
                      className="text-destructive"
                    >
                      <Trash2 className="mr-2 h-4 w-4" />
                      Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  )
}

