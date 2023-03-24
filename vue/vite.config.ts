import { defineConfig, loadEnv } from "vite";
import vue from "@vitejs/plugin-vue";
import { execSync } from "child_process";

export default defineConfig(({ mode }) => {
  // Load env file based on `mode` in the current working directory.
  // Set the third parameter to '' to load all env regardless of the `VITE_` prefix.
  const env = loadEnv(mode, process.cwd(), "");
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
  return {
    plugins: [vue()],
    server: {
      host: "0.0.0.0",
      port: 8080,
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
