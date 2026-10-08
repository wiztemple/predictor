import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Every page is pre-rendered from the pipeline's JSON files, so the site is
  // exported as plain static files (out/) and served by Cloudflare.
  output: "export",
};

export default nextConfig;
