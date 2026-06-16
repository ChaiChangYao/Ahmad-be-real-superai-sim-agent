import type { NextConfig } from "next";

const apiUpstream = process.env.API_UPSTREAM_URL?.replace(/\/$/, "");

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async rewrites() {
    if (!apiUpstream) return [];
    return [{ source: "/backend/:path*", destination: `${apiUpstream}/:path*` }];
  },
  webpack: (config, { dev }) => {
    if (dev) {
      // Prevent stale/missing .pack.gz crashes when .next is cleared while dev is running (Windows).
      config.cache = false;
    }
    return config;
  },
};

export default nextConfig;
