import type { NextConfig } from "next";

const isGitHubPages = process.env.GITHUB_PAGES === "true";

const nextConfig: NextConfig = {
  ...(isGitHubPages
    ? {
        output: "export",
        basePath: "/Septem",
        trailingSlash: true,
        env: {
          NEXT_PUBLIC_API_BASE_URL:
            process.env.NEXT_PUBLIC_API_BASE_URL?.trim() ?? "",
        },
      }
    : {}),
  turbopack: {
    root: process.cwd(),
  },
};

export default nextConfig;
