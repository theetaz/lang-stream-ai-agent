/**
 * Suppress Better Auth database warning in development
 * This warning is expected when using stateless mode with cookieCache
 * 
 * NOTE: This runs on the server-side only (when window is undefined)
 */
if (typeof window === "undefined") {
  const originalWarn = console.warn;
  console.warn = (...args: any[]) => {
    // Suppress Better Auth database warning
    const message = args[0];
    if (
      message &&
      typeof message === "string" &&
      (message.includes("No database configuration provided") ||
       message.includes("Using memory adapter in development"))
    ) {
      return;
    }
    originalWarn.apply(console, args);
  };
}


