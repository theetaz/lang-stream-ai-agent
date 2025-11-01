/**
 * Better Auth Server Configuration
 * Handles Google OAuth flow only - stateless mode (no database required)
 * All user data is stored in backend database via API calls
 */
import { betterAuth } from "better-auth";
import { nextCookies } from "better-auth/next-js";

export const auth = betterAuth({
  // Stateless session management - no database needed
  // All session data stored in encrypted cookies
  session: {
    expiresIn: 60 * 60 * 24 * 7, // 7 days
    updateAge: 60 * 60 * 24, // 1 day
    cookieCache: {
      enabled: true,
      maxAge: 30 * 24 * 60 * 60, // 30 days cache duration
      strategy: "jwe", // Use encrypted tokens for better security
      refreshCache: true, // Enable stateless refresh
    },
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

  // Use next-cookies plugin for server actions support
  plugins: [nextCookies()],

  // Custom callbacks - Better Auth only handles OAuth callback
  // After OAuth success, frontend sends user data to backend API
  callbacks: {
    async signIn(data: any) {
      // Allow OAuth sign in - backend will handle user creation
      return true;
    },

    async session(data: any) {
      // Return session data - backend JWT is stored separately in localStorage
      return {
        ...data.session,
        user: {
          ...data.session.user,
        },
      };
    },
  },
});

export type Session = typeof auth.$Infer.Session;
