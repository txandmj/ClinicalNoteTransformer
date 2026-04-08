import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/generate": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/cases": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/guidelines": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/health": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/privacy": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/export": { target: "http://127.0.0.1:8000", changeOrigin: true },
    },
  },
});
