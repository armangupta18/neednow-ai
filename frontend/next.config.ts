import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  // Pin Turbopack root to frontend directory (prevents picking up C:\Users\acer\Desktop\package-lock.json)
  turbopack: {
    root: path.resolve(__dirname),
  },

  // Allow dev access from local network
  allowedDevOrigins: ["10.26.29.116"],

  // Environment variables exposed to the browser
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
    NEXT_PUBLIC_APP_NAME: "NeedNow AI",
  },

  // Image optimization (for product images)
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "**" },
    ],
  },

  // Strict React mode for development
  reactStrictMode: true,

  // Experimental features
  experimental: {
    optimizePackageImports: ["lucide-react"],
  },
};

export default nextConfig;
