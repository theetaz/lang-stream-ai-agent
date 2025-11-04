import { useState, useCallback, useRef } from "react"
import type { ToolCallData } from "@/components/tool-call"
import { getAuthHeaders } from "@/lib/auth-interceptor"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export interface StreamEvent {
  type: "content" | "tool_start" | "tool_call" | "tool_result" | "tool_thinking" | "done" | "error"
  content?: string
  tool?: string
  input?: Record<string, any>
  result?: string
  message?: string
  tool_name?: string
  error?: string
}

interface UseChatStreamOptions {
  onChunk?: (chunk: string) => void
  onToolEvent?: (event: StreamEvent) => void
  onComplete?: (fullMessage: string) => void
  onError?: (error: Error) => void
}

export function useChatStream(options: UseChatStreamOptions = {}) {
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)
  const currentMessageRef = useRef<string>("")

  const streamMessage = useCallback(
    async (input: string) => {
      setIsStreaming(true)
      setError(null)
      currentMessageRef.current = ""

      // Create new AbortController for this request
      abortControllerRef.current = new AbortController()

      try {
        const authHeaders = await getAuthHeaders();
        
        const response = await fetch(`${API_URL}/api/v1/chat/stream`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...authHeaders,
          },
          body: JSON.stringify({ input }),
          signal: abortControllerRef.current.signal,
        })

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const reader = response.body?.getReader()
        const decoder = new TextDecoder()

        if (!reader) {
          throw new Error("No response body")
        }

        let buffer = ""

        while (true) {
          const { done, value } = await reader.read()

          if (done) {
            break
          }

          // Decode the chunk
          buffer += decoder.decode(value, { stream: true })

          // Split by newlines to process complete SSE messages
          const lines = buffer.split("\n")

          // Keep the last incomplete line in the buffer
          buffer = lines.pop() || ""

          for (const line of lines) {
            // Skip empty lines and comments
            if (!line.trim() || line.startsWith(":")) {
              continue
            }

            if (line.startsWith("data: ")) {
              const data = line.slice(6).trim()

              try {
                const parsed: StreamEvent = JSON.parse(data)

                if (parsed.type === "error" && parsed.error) {
                  throw new Error(parsed.error)
                }

                if (parsed.type === "done") {
                  options.onComplete?.(currentMessageRef.current)
                  break
                }

                if (parsed.type === "content" && parsed.content) {
                  currentMessageRef.current += parsed.content
                  // Call onChunk immediately for real-time display
                  options.onChunk?.(parsed.content)
                }

                // Handle tool events
                if (
                  parsed.type === "tool_start" ||
                  parsed.type === "tool_call" ||
                  parsed.type === "tool_result" ||
                  parsed.type === "tool_thinking"
                ) {
                  options.onToolEvent?.(parsed)
                }
              } catch (e) {
                // Only throw if it's not a JSON parse error
                if (e instanceof Error && e.message.includes("HTTP error")) {
                  throw e
                }
                // Silently ignore incomplete JSON chunks
              }
            }
          }
        }
      } catch (err) {
        if (err instanceof Error && err.name === "AbortError") {
          // User cancelled, not an error
          return
        }
        const error = err instanceof Error ? err : new Error("Stream failed")
        setError(error)
        options.onError?.(error)
      } finally {
        setIsStreaming(false)
        abortControllerRef.current = null
      }
    },
    [options]
  )

  const cancel = useCallback(() => {
    abortControllerRef.current?.abort()
    setIsStreaming(false)
  }, [])

  return {
    streamMessage,
    isStreaming,
    error,
    cancel,
  }
}
