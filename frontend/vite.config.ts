import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

export default defineConfig(({ mode }) => {
  // loadEnv reads .env files without needing node's process typings.
  const env = loadEnv(mode, process.cwd?.() ?? ".", "VITE_");

  const proxy = {
    "/api": {
      target: env.VITE_API_BASE_URL || "http://127.0.0.1:8000",
      changeOrigin: true,
    },
  };

  return {
    plugins: [react()],
    server: {
      port: 5173,
      // Proxying keeps the browser on a single origin in development, so CORS
      // behaves the same as it will behind a reverse proxy in production.
      proxy,
    },
    // `npm run preview` serves the real build with the same proxy, which is the
    // closest local mirror of Netlify: static files plus /api forwarded on.
    preview: {
      port: 4173,
      proxy,
    },
    build: {
      outDir: "dist",
      sourcemap: true,
    },
  };
});
