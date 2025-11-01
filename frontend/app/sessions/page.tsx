"use client";

import { useEffect, useState } from "react";
import { getUserSessions, deleteSession, deleteAllSessions, getCurrentSessionId } from "@/lib/auth-client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2, Trash2, LogOut, Monitor, Smartphone, Tablet } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

interface Session {
  id: string;
  device_info: string | null;
  ip_address: string | null;
  user_agent: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_activity: string;
}

export default function SessionsPage() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [deletingAll, setDeletingAll] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const currentSessionId = getCurrentSessionId();

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getUserSessions();
      setSessions(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load sessions");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteSession = async (sessionId: string) => {
    try {
      setDeleting(sessionId);
      setError(null);
      await deleteSession(sessionId);
      await loadSessions();
      
      // If we deleted the current session, redirect to login
      if (sessionId === currentSessionId) {
        window.location.href = "/login";
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete session");
    } finally {
      setDeleting(null);
    }
  };

  const handleDeleteAll = async () => {
    if (!confirm("Are you sure you want to log out from all devices? This will end all your active sessions.")) {
      return;
    }

    try {
      setDeletingAll(true);
      setError(null);
      await deleteAllSessions();
      // Redirect to login since all sessions are deleted
      window.location.href = "/login";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete all sessions");
      setDeletingAll(false);
    }
  };

  const getDeviceIcon = (deviceInfo: string | null) => {
    if (!deviceInfo) return <Monitor className="h-5 w-5" />;
    const lower = deviceInfo.toLowerCase();
    if (lower.includes("mobile") || lower.includes("iphone") || lower.includes("android")) {
      return <Smartphone className="h-5 w-5" />;
    }
    if (lower.includes("tablet") || lower.includes("ipad")) {
      return <Tablet className="h-5 w-5" />;
    }
    return <Monitor className="h-5 w-5" />;
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
          <p className="text-muted-foreground">Loading sessions...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-4xl py-8 px-4">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Active Sessions</CardTitle>
              <CardDescription className="mt-2">
                Manage your active sessions across different devices and browsers
              </CardDescription>
            </div>
            <Button
              variant="destructive"
              onClick={handleDeleteAll}
              disabled={deletingAll || sessions.filter(s => s.is_active).length === 0}
            >
              {deletingAll ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Logging out...
                </>
              ) : (
                <>
                  <LogOut className="mr-2 h-4 w-4" />
                  Logout All
                </>
              )}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {error && (
            <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive mb-4">
              {error}
            </div>
          )}

          {sessions.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No sessions found
            </div>
          ) : (
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
                        {session.ip_address && (
                          <div>IP: {session.ip_address}</div>
                        )}
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
                      onClick={() => handleDeleteSession(session.id)}
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
          )}
        </CardContent>
      </Card>
    </div>
  );
}

