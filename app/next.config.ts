import type { NextConfig } from "next";

// `standalone` produces a self-contained server bundle for Docker,
// pulling only the modules actually used by the runtime. Vercel ignores
// this; the dev server is unaffected. See app/Dockerfile.
const nextConfig: NextConfig = {
  output: "standalone",
};

export default nextConfig;
