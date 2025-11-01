import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // Configure API URL for backend communication
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/:path*"
      }
    ];
  }
};

export default nextConfig;
