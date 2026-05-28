import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  // Относительные пути к ассетам, чтобы один и тот же билд работал и на
  // GitHub Pages (в подкаталоге /<repo>/), и на Timeweb/Beget (в корне домена).
  // Вместе с hash-роутером это даёт полностью портативную статику.
  base: "./",
  plugins: [vue()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
      "@data": fileURLToPath(new URL("../data", import.meta.url)),
    },
  },
  server: {
    port: 5173,
    open: true,
  },
});
