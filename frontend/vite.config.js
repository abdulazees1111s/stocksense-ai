import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    chunkSizeWarningLimit: 6000,
    rollupOptions: {
      output: {
        manualChunks: {
          charts: ["plotly.js-dist-min", "react-plotly.js", "chart.js", "react-chartjs-2"],
          react: ["react", "react-dom"],
        },
      },
    },
  },
  server: {
    port: 5173,
  },
});
