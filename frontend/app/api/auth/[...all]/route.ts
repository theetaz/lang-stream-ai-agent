/**
 * Better Auth API Route Handler
 * Mounts Better Auth handler to Next.js API routes
 */
import { auth } from "@/lib/auth";
import { toNextJsHandler } from "better-auth/next-js";

export const { GET, POST } = toNextJsHandler(auth.handler);

export const runtime = "nodejs";
