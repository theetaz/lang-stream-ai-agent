import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // Configure API URL for backend communication
  // Exclude Better Auth routes from rewrite
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: "http://localhost:8000/api/v1/:path*"
      }
    ];
  }
};

export default nextConfig;
