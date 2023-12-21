import { defineConfig, loadEnv } from "vite";
import vue from "@vitejs/plugin-vue";
import { execSync } from "child_process";

export default ({ mode}) => {
  // Loads all environment variables to see if we are in VITE_DOCKER_DEVELOPMENT
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
    const dockerDev = process.env.VITE_DOCKER_DEVELOPMENT;
    // Change host to django when running vite inside docker
    const devHost = dockerDev ? 'django' : 'localhost';
    const devPort = dockerDev ? 8080 : 3000;
  return defineConfig({
      plugins: [vue()],
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
