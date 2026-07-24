import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  reactStrictMode: true,
  serverExternalPackages: ["postgres"],
  transpilePackages: ["@clientatlas/database"]
};

export default nextConfig;
