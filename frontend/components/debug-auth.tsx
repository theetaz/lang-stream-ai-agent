"use client"

import { useEffect, useState } from "react"
import { getAuthToken } from "@/lib/utils"

export function DebugAuth() {
  const [tokenInfo, setTokenInfo] = useState<{
    hasLocalStorage: boolean
    hasCookie: boolean
    token: string | null
  } | null>(null)

  useEffect(() => {
    const token = getAuthToken()
    const hasLocalStorage = !!localStorage.getItem("backend_access_token")
    const cookies = document.cookie.split("; ")
    const hasCookie = !!cookies.find((row) => row.startsWith("backend_access_token="))

    setTokenInfo({
      hasLocalStorage,
      hasCookie,
      token: token ? token.substring(0, 20) + "..." : null,
    })
  }, [])

  if (process.env.NODE_ENV !== "development") {
    return null
  }

  return (
    <div className="fixed bottom-4 right-4 bg-black/90 text-white text-xs p-3 rounded-lg font-mono max-w-xs z-50">
      <div className="font-bold mb-1">Auth Debug Info:</div>
      <div>localStorage: {tokenInfo?.hasLocalStorage ? "✅" : "❌"}</div>
      <div>Cookie: {tokenInfo?.hasCookie ? "✅" : "❌"}</div>
      <div>Token: {tokenInfo?.token || "NONE"}</div>
    </div>
  )
}

