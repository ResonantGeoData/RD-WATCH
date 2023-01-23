import { defineConfig, loadEnv } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig(({ mode }) => {
  // Load env file based on `mode` in the current working directory.
  // Set the third parameter to '' to load all env regardless of the `VITE_` prefix.
  const env = loadEnv(mode, process.cwd(), "");
  return {
    plugins: [vue()],
    server: {
      host: "0.0.0.0",
      port: 9000,
      proxy: {
        "/api": {
          target: "http://localhost:8000",
          xfwd: true,
        },
      },
      strictPort: true,
      usePolling: env.RDWATCH_FILE_POLLING === "1",
    },
  };
});
