import * as React from "react"

type ToastProps = {
  title: string
  description?: string
  variant?: "default" | "destructive"
}

export function useToast() {
  const toast = React.useCallback(({ title, description, variant = "default" }: ToastProps) => {
    console.log(`[Toast ${variant}] ${title}${description ? `: ${description}` : ""}`)
  }, [])

  return { toast }
}

