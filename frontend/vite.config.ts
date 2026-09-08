import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  base: "/static/",
  build: {
    manifest: "manifest.json",
    outDir: "frontend/dist",
    rollupOptions: { input: "frontend/app.tsx" },
  },
});
