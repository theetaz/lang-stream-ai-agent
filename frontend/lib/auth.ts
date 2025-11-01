/**
 * Better Auth Server Configuration
 * Handles Google OAuth and stores custom JWT from our backend
 */
import { betterAuth } from "better-auth";
import { nextCookies } from "better-auth/next-js";

export const auth = betterAuth({
  database: {
    provider: "postgres",
    url: process.env.DATABASE_URL || `postgresql://${process.env.POSTGRES_USER}:${process.env.POSTGRES_PASSWORD}@${process.env.POSTGRES_HOST}:${process.env.POSTGRES_PORT}/${process.env.POSTGRES_DB}`,
  },

  socialProviders: {
    google: {
      clientId: process.env.GOOGLE_CLIENT_ID as string,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET as string,
      // Get refresh token
      accessType: "offline",
      prompt: "select_account consent",
    },
  },

  // Custom session configuration to store our backend JWT
  session: {
    expiresIn: 60 * 60 * 24 * 7, // 7 days
    updateAge: 60 * 60 * 24, // 1 day
    cookieCache: {
      enabled: true,
      maxAge: 60 * 5, // 5 minutes
    },
  },

  // Use next-cookies plugin for server actions support
  plugins: [nextCookies()],

  // Custom callbacks to integrate with our backend
  callbacks: {
    async signIn(data) {
      // This is called after OAuth success
      // We'll send user data to our backend here
      console.log("Better Auth: Sign in callback", data);
      return true; // Allow sign in
    },

    async session(data) {
      // Add our custom JWT to the session
      return {
        ...data.session,
        user: {
          ...data.session.user,
          // Custom fields will be added here
        },
      };
    },
  },
});

export type Session = typeof auth.$Infer.Session;
