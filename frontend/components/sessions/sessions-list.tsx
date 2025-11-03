"use client";

import { Monitor, Smartphone, Tablet, Trash2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { formatDistanceToNow } from "date-fns";
import type { Session } from "@/lib/api/sessions";

interface SessionsListProps {
  sessions: Session[];
  currentSessionId: string | null;
  onDelete: (sessionId: string) => void;
  deleting: string | null;
}

function getDeviceIcon(deviceInfo: string | null) {
  if (!deviceInfo) return <Monitor className="h-5 w-5" />;
  const lower = deviceInfo.toLowerCase();
  if (lower.includes("mobile") || lower.includes("iphone") || lower.includes("android")) {
    return <Smartphone className="h-5 w-5" />;
  }
  if (lower.includes("tablet") || lower.includes("ipad")) {
    return <Tablet className="h-5 w-5" />;
  }
  return <Monitor className="h-5 w-5" />;
}

export function SessionsList({ sessions, currentSessionId, onDelete, deleting }: SessionsListProps) {
  if (sessions.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No sessions found
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {sessions.map((session) => (
        <div
          key={session.id}
          className={`flex items-center justify-between p-4 rounded-lg border ${
            session.id === currentSessionId
              ? "border-primary bg-primary/5"
              : "border-border"
          }`}
        >
          <div className="flex items-start gap-4 flex-1">
            <div className="mt-1">
              {getDeviceIcon(session.device_info)}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <h3 className="font-medium">
                  {session.device_info || "Unknown Device"}
                </h3>
                {session.id === currentSessionId && (
                  <span className="text-xs px-2 py-0.5 rounded bg-primary/10 text-primary">
                    Current Session
                  </span>
                )}
                {!session.is_active && (
                  <span className="text-xs px-2 py-0.5 rounded bg-muted text-muted-foreground">
                    Inactive
                  </span>
                )}
              </div>
              <div className="text-sm text-muted-foreground mt-1 space-y-1">
                {session.ip_address && <div>IP: {session.ip_address}</div>}
                <div>
                  Last active:{" "}
                  {formatDistanceToNow(new Date(session.last_activity), {
                    addSuffix: true,
                  })}
                </div>
                <div>
                  Created:{" "}
                  {formatDistanceToNow(new Date(session.created_at), {
                    addSuffix: true,
                  })}
                </div>
              </div>
            </div>
          </div>
          {session.is_active && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onDelete(session.id)}
              disabled={deleting === session.id}
            >
              {deleting === session.id ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Trash2 className="h-4 w-4" />
              )}
            </Button>
          )}
        </div>
      ))}
    </div>
  );
}

