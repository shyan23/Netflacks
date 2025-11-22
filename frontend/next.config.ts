import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8080/api/:path*',
      },
      {
        source: '/stream/:path*',
        destination: 'http://localhost:8080/stream/:path*',
      },
      {
        source: '/upload',
        destination: 'http://localhost:8080/upload',
      },
    ];
  },
  // Enable standalone output for better performance
  output: 'standalone',
};

export default nextConfig;
