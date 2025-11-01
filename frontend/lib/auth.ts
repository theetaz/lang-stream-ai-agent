/**
 * Better Auth server configuration
 * Handles Google OAuth authentication
 */
import { betterAuth } from "better-auth";
import { prismaAdapter } from "better-auth/adapters/prisma";
import Database from "better-auth/adapters/postgres";

export const auth = betterAuth({
  database: new Database({
    host: process.env.POSTGRES_HOST || "localhost",
    port: parseInt(process.env.POSTGRES_PORT || "5433"),
    user: process.env.POSTGRES_USER || "postgres",
    password: process.env.POSTGRES_PASSWORD || "",
    database: process.env.POSTGRES_DB || "lang_ai_agent",
  }),

  emailAndPassword: {
    enabled: false, // Only using OAuth
  },

  socialProviders: {
    google: {
      clientId: process.env.GOOGLE_CLIENT_ID || "",
      clientSecret: process.env.GOOGLE_CLIENT_SECRET || "",
      // Redirect URI will be: http://localhost:3000/api/auth/callback/google
    },
  },

  secret: process.env.BETTER_AUTH_SECRET || "",

  baseURL: process.env.BETTER_AUTH_URL || "http://localhost:3000",

  // Optional: customize session behavior
  session: {
    expiresIn: 60 * 60 * 24 * 7, // 7 days
    updateAge: 60 * 60 * 24, // 1 day
  },
});
