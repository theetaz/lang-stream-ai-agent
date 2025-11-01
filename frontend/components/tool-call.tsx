import { CheckCircle2, Search, Loader2, AlertCircle } from "lucide-react"
import { cn } from "@/lib/utils"

export interface ToolCallData {
  id: string
  tool: string
  input?: Record<string, any>
  result?: string
  status: "pending" | "running" | "complete" | "error"
  error?: string
}

interface ToolCallProps {
  toolCall: ToolCallData
}

export function ToolCall({ toolCall }: ToolCallProps) {
  const getIcon = () => {
    switch (toolCall.status) {
      case "complete":
        return <CheckCircle2 className="h-4 w-4 text-green-500" />
      case "error":
        return <AlertCircle className="h-4 w-4 text-red-500" />
      case "running":
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
      default:
        return <Search className="h-4 w-4 text-muted-foreground" />
    }
  }

  const getToolName = () => {
    // Format tool name nicely
    if (toolCall.tool === "tavily_search_results_json") {
      return "Web Search"
    }
    return toolCall.tool
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ")
  }

  const getQuery = () => {
    if (toolCall.input && typeof toolCall.input === "object") {
      return toolCall.input.query || toolCall.input.input || JSON.stringify(toolCall.input)
    }
    return ""
  }

  return (
    <div
      className={cn(
        "flex flex-col gap-2 rounded-lg border p-3 text-sm transition-all",
        toolCall.status === "complete" && "border-green-500/20 bg-green-500/5",
        toolCall.status === "error" && "border-red-500/20 bg-red-500/5",
        toolCall.status === "running" && "border-blue-500/20 bg-blue-500/5",
        toolCall.status === "pending" && "border-border bg-muted/30"
      )}
    >
      {/* Header */}
      <div className="flex items-center gap-2">
        {getIcon()}
        <span className="font-medium">{getToolName()}</span>
        <span
          className={cn(
            "ml-auto text-xs",
            toolCall.status === "complete" && "text-green-600 dark:text-green-400",
            toolCall.status === "error" && "text-red-600 dark:text-red-400",
            toolCall.status === "running" && "text-blue-600 dark:text-blue-400",
            toolCall.status === "pending" && "text-muted-foreground"
          )}
        >
          {toolCall.status === "complete" && "Complete"}
          {toolCall.status === "error" && "Error"}
          {toolCall.status === "running" && "Searching..."}
          {toolCall.status === "pending" && "Pending"}
        </span>
      </div>

      {/* Query/Input */}
      {getQuery() && (
        <div className="text-muted-foreground">
          <span className="font-medium">Query: </span>
          <span className="italic">&quot;{getQuery()}&quot;</span>
        </div>
      )}

      {/* Result - only show if complete */}
      {toolCall.status === "complete" && toolCall.result && (
        <div className="text-xs text-muted-foreground border-t pt-2 mt-1">
          {typeof toolCall.result === "string" ? (
            <span className="line-clamp-3">{toolCall.result}</span>
          ) : (
            <pre className="overflow-auto max-h-32">
              {JSON.stringify(toolCall.result, null, 2)}
            </pre>
          )}
        </div>
      )}

      {/* Error */}
      {toolCall.status === "error" && toolCall.error && (
        <div className="text-xs text-red-600 dark:text-red-400">
          Error: {toolCall.error}
        </div>
      )}
    </div>
  )
}
