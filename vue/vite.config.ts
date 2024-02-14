import { defineConfig, loadEnv } from "vite";
import vue from "@vitejs/plugin-vue";
import { execSync } from "child_process";
import wasm from "vite-plugin-wasm";
import topLevelAwait from "vite-plugin-top-level-await";
import { viteStaticCopy } from "vite-plugin-static-copy";

export default ({ mode}) => {
  // Loads all environment variables to see if we are in VITE_DEV_PROXY_TARGET
  process.env = {...process.env, ...loadEnv(mode, process.cwd())};
  // Load env file based on `mode` in the current working directory.
  // Set the third parameter to '' to load all env regardless of the `VITE_` prefix.
  const commitDate = execSync("git log -1 --format=%cI").toString().trimEnd();
  const branchName = execSync("git rev-parse --abbrev-ref HEAD")
    .toString()
    .trimEnd();
  const commitHash = execSync("git rev-parse HEAD").toString().trimEnd();
  const lastCommitMessage = execSync("git show -s --format=%s")
    .toString()
    .trimEnd();

  process.env.VITE_GIT_COMMIT_DATE = commitDate;
  process.env.VITE_GIT_BRANCH_NAME = branchName;
  process.env.VITE_GIT_COMMIT_HASH = commitHash;
  process.env.VITE_GIT_LAST_COMMIT_MESSAGE = lastCommitMessage;
  const devHost = process.env.VITE_DEV_PROXY_TARGET || 'localhost';
  // Change host to django when running vite inside docker
  const devPort = process.env.VITE_DEV_PROXY_TARGET ? 8080 : 3000;
  return defineConfig({
      plugins: [vue(),
        viteStaticCopy({
          targets: [
            {
              src: "node_modules/onnxruntime-web/dist/*.wasm",
              dest: ".",
            },
          ],
        }),
        {
          name: "configure-response-headers",
          configureServer: (server) => {
            server.middlewares.use((req, res, next) => {
              // res.setHeader("Cross-Origin-Opener-Policy", "same-origin");
              // res.setHeader("Cross-Origin-Embedder-Policy", "require-corp");
              if (req.url.endsWith(".wasm")) {
                res.setHeader("Content-Type", "application/wasm");
              }
              next();
            });
          },
        },
        // wasm(),
        topLevelAwait(),],
      server: {
        host: "0.0.0.0",
        port: devPort,
        proxy: {
          "/api": {
            target: `http://${devHost}:8000`,
            xfwd: true,
          },
        },
        strictPort: true,
      },
    });
}
