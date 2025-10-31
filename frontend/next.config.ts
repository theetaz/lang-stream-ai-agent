import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // Configure API URL for backend communication
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://fastapi:8000/:path*",
      },
    ];
  },
};

export default nextConfig;
