import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: "standalone",
  // Para que el dev server en Docker sea accesible desde el host
  allowedDevOrigins: ["http://localhost:3000", "http://localhost"],
};

export default nextConfig;
