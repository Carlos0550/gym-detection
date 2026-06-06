import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Para que el dev server en Docker sea accesible desde el host
  experimental: {
    allowedDevOrigins: ["http://localhost:3000", "http://localhost"],
  },
};

export default nextConfig;
