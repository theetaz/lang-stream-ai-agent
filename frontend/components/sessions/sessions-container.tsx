"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2, LogOut } from "lucide-react";
import { SessionsList } from "./sessions-list";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getUserSessions, deleteSession, deleteAllSessions, getCurrentSessionId, getBackendAccessToken } from "@/lib/auth-client";
import { useState } from "react";
import { useRouter } from "next/navigation";

export function SessionsContainer() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [deleting, setDeleting] = useState<string | null>(null);
  const token = getBackendAccessToken();
  const currentSessionId = getCurrentSessionId();

  const { data, isLoading, error } = useQuery({
    queryKey: ["auth-sessions"],
    queryFn: async () => {
      if (!token) throw new Error("No token");
      return await getUserSessions();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (sessionId: string) => {
      if (!token) throw new Error("No token");
      return await deleteSession(sessionId);
    },
    onMutate: (sessionId) => {
      setDeleting(sessionId);
    },
    onSuccess: (_, sessionId) => {
      queryClient.invalidateQueries({ queryKey: ["auth-sessions"] });
      if (sessionId === currentSessionId) {
        window.location.href = "/login";
      }
    },
    onSettled: () => {
      setDeleting(null);
    },
  });

  const deleteAllMutation = useMutation({
    mutationFn: async () => {
      if (!token) throw new Error("No token");
      return await deleteAllSessions();
    },
    onSuccess: () => {
      window.location.href = "/login";
    },
  });

  const handleDeleteAll = () => {
    if (confirm("Are you sure you want to log out from all devices? This will end all your active sessions.")) {
      deleteAllMutation.mutate();
    }
  };

  if (isLoading) {
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
              disabled={deleteAllMutation.isPending || data?.filter((s) => s.is_active).length === 0}
            >
              {deleteAllMutation.isPending ? (
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
              {error instanceof Error ? error.message : "Failed to load sessions"}
            </div>
          )}
          <SessionsList
            sessions={data || []}
            currentSessionId={currentSessionId}
            onDelete={(id) => deleteMutation.mutate(id)}
            deleting={deleting}
          />
        </CardContent>
      </Card>
    </div>
  );
}

