import { useState, useCallback, useRef } from "react"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface UseChatStreamOptions {
  onChunk?: (chunk: string) => void
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
        const response = await fetch(`${API_URL}/api/v1/chat/stream`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
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

        while (true) {
          const { done, value } = await reader.read()

          if (done) {
            break
          }

          const chunk = decoder.decode(value, { stream: true })
          const lines = chunk.split("\n")

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const data = line.slice(6)

              try {
                const parsed = JSON.parse(data)

                if (parsed.error) {
                  throw new Error(parsed.error)
                }

                if (parsed.done) {
                  options.onComplete?.(currentMessageRef.current)
                  break
                }

                if (parsed.content) {
                  currentMessageRef.current += parsed.content
                  options.onChunk?.(parsed.content)
                }
              } catch (e) {
                // Ignore JSON parse errors for incomplete chunks
                if (e instanceof Error && !e.message.includes("Unexpected")) {
                  throw e
                }
              }
            }
          }
        }
      } catch (err) {
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
