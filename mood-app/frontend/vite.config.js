// Vite settings: turn on React and run the site on port 5173.
// (If something else is already using that port, set PORT before starting.)

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: { port: Number(process.env.PORT) || 5173 },
});
