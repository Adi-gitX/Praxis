import type { NextConfig } from "next";

// `standalone` produces a self-contained server bundle for Docker,
// pulling only the modules actually used by the runtime. Vercel ignores
// this; the dev server is unaffected. See app/Dockerfile.
const nextConfig: NextConfig = {
  output: "standalone",
  webpack: (config) => {
    // RainbowKit pulls in @metamask/sdk which references React-Native-only
    // optional peer deps. Tell webpack to no-op them in the browser bundle
    // so `next build` doesn't fail on a module that is never executed.
    config.resolve = config.resolve ?? {};
    config.resolve.fallback = {
      ...(config.resolve.fallback ?? {}),
      "@react-native-async-storage/async-storage": false,
      encoding: false,
      pino: false,
      "pino-pretty": false,
    };
    return config;
  },
};

export default nextConfig;
