import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";

export default defineConfig({
  plugins: [svelte()],
  server: {
    host: "localhost",
    port: 5173,
    cors: {
      origin: "http://localhost:5173",
    },
    proxy: {
      "/apps": {
        target: "http://127.0.0.1:8001",
        changeOrigin: true,
      },
      "/list-apps": {
        target: "http://127.0.0.1:8001",
        changeOrigin: true,
      },
      "/run": {
        target: "http://127.0.0.1:8001",
        changeOrigin: true,
      },
    },
  },
});
