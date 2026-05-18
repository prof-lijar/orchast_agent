import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";

export default defineConfig({
  plugins: [svelte()],
  server: {
    host: "localhost",
    port: 5173,
    cors: true,
    allowedHosts: "all",
    proxy: {
      "/apps": {
        target: "http://127.0.0.1:8081",
        changeOrigin: true,
      },
      "/list-apps": {
        target: "http://127.0.0.1:8081",
        changeOrigin: true,
      },
      "/run_sse": {
        target: "http://127.0.0.1:8081",
        changeOrigin: true,
      },
      "/run": {
        target: "http://127.0.0.1:8081",
        changeOrigin: true,
      },
      "/api": {
        target: "http://127.0.0.1:8081",
        changeOrigin: true,
      },
    },
  },
});
