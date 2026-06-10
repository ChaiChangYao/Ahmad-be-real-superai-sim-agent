import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  webpack: (config, { dev }) => {
    if (dev) {
      // Prevent stale/missing .pack.gz crashes when .next is cleared while dev is running (Windows).
      config.cache = false;
    }
    return config;
  },
};

export default nextConfig;
