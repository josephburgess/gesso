import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  base: "/static/",
  build: {
    manifest: "manifest.json",
    outDir: "frontend/dist",
    rollupOptions: { input: "frontend/app.tsx" },
  },
});
