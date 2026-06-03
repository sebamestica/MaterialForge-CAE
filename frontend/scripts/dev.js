const { spawn, execSync } = require("child_process");
const http = require("http");
const path = require("path");
const os = require("os");

const FRONTEND_DIR = path.resolve(__dirname, "../");
const BACKEND_DIR = path.resolve(__dirname, "../../");

// 1. Helper to check if Ollama is running
function checkOllamaRunning() {
  return new Promise((resolve) => {
    const req = http.get("http://127.0.0.1:11434/api/tags", (res) => {
      resolve(res.statusCode === 200);
    });
    req.on("error", () => {
      resolve(false);
    });
    req.end();
  });
}

// 2. Start Ollama if not running
async function startOllama() {
  const running = await checkOllamaRunning();
  if (running) {
    console.log("[Ollama] Ollama server is already running and connected.");
    return true;
  }

  console.log("[Ollama] Ollama server not detected. Starting Ollama...");
  
  const fs = require("fs");
  let cmd = "ollama";
  if (os.platform() === "win32") {
    const defaultWinPath = path.join(os.homedir(), "AppData", "Local", "Programs", "Ollama", "ollama.exe");
    if (fs.existsSync(defaultWinPath)) {
      cmd = defaultWinPath;
    }
  }

  try {
    if (os.platform() === "win32") {
      const child = spawn(cmd, ["serve"], {
        detached: true,
        stdio: "ignore"
      });
      child.on("error", (err) => {
        console.warn("[Ollama] Failed to spawn Ollama process (executable might be missing):", err.message);
      });
      child.unref();
    } else {
      const child = spawn("ollama", ["serve"], {
        detached: true,
        stdio: "ignore"
      });
      child.on("error", (err) => {
        console.warn("[Ollama] Failed to spawn Ollama process (executable might be missing):", err.message);
      });
      child.unref();
    }
  } catch (err) {
    console.error("[Ollama] Failed to start Ollama executable automatically:", err.message);
  }

  // Poll for connection
  console.log("[Ollama] Waiting for Ollama to become responsive...");
  for (let i = 0; i < 15; i++) {
    await new Promise((r) => setTimeout(r, 1000));
    const isUp = await checkOllamaRunning();
    if (isUp) {
      console.log("[Ollama] Ollama is active!");
      return true;
    }
  }
  console.warn("[Ollama] Ollama server did not respond within 15 seconds. Proceeding anyway...");
  return false;
}

// 3. Helper to verify and build database if missing
function checkAndBuildDatabase(pythonBin, backendDir) {
  const fs = require("fs");
  const dbPath = path.join(backendDir, "data", "processed", "training_table.parquet");
  if (fs.existsSync(dbPath)) {
    console.log("[Database] Master training table detected.");
    return;
  }

  console.log("[Database] Master training table NOT found. Running ingestion scanner first...");
  try {
    execSync(`"${pythonBin}" -m backend.src.data.dataset_scanner`, {
      cwd: backendDir,
      stdio: "inherit"
    });
    console.log("[Database] Ingestion successfully completed and database consolidated.");
  } catch (err) {
    console.error("[Database] Failed to build database on startup:", err.message);
  }
}

// Helper to kill processes on specific ports to avoid conflicts
function killProcessesOnPorts(ports) {
  console.log(`[System] Checking and freeing ports: ${ports.join(", ")}...`);
  for (const port of ports) {
    try {
      if (os.platform() === "win32") {
        const output = execSync(`netstat -ano | findstr :${port}`, { encoding: "utf8" });
        const lines = output.split("\n");
        for (const line of lines) {
          const parts = line.trim().split(/\s+/);
          if (parts.length >= 5 && parts[1].endsWith(`:${port}`) && parts[3] === "LISTENING") {
            const pid = parts[4];
            if (pid && pid !== "0" && pid !== process.pid.toString()) {
              console.log(`[System] Port conflict detected: killing process ${pid} on port ${port}...`);
              execSync(`taskkill /F /PID ${pid}`, { stdio: "ignore" });
            }
          }
        }
      } else {
        const pids = execSync(`lsof -t -i:${port}`, { encoding: "utf8" }).trim().split("\n");
        for (const pid of pids) {
          if (pid && pid !== process.pid.toString()) {
            console.log(`[System] Port conflict detected: killing process ${pid} on port ${port}...`);
            execSync(`kill -9 ${pid}`, { stdio: "ignore" });
          }
        }
      }
    } catch (err) {
      // Ignore errors if no process is listening on the port
    }
  }
}

// 4. Main process execution
async function main() {
  // Free up ports to avoid conflict
  killProcessesOnPorts([3000, 8000]);

  // Start Ollama
  await startOllama();

  const pythonBin = os.platform() === "win32"
    ? path.join(BACKEND_DIR, ".venv", "Scripts", "python.exe")
    : path.join(BACKEND_DIR, ".venv", "bin", "python");

  // Verify and build database if missing
  checkAndBuildDatabase(pythonBin, BACKEND_DIR);

  // Start Backend FastAPI
  console.log("[Backend] Starting FastAPI Server...");

  const backendProc = spawn(
    pythonBin,
    ["-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
    {
      cwd: BACKEND_DIR,
      stdio: "inherit",
      shell: true
    }
  );

  // Start Next.js dev server
  console.log("[Frontend] Starting Next.js Dev Server...");
  const npmCmd = os.platform() === "win32" ? "npm.cmd" : "npm";
  const frontendProc = spawn(
    npmCmd,
    ["run", "next-dev"],
    {
      cwd: FRONTEND_DIR,
      stdio: "inherit",
      shell: true
    }
  );

  // Print helpful URLs
  setTimeout(() => {
    console.log("\n========================================================");
    console.log("  [MaterialForge Workspaces Ready]");
    console.log("  -> Frontend Workspace: http://localhost:3000");
    console.log("  -> Backend API Service: http://127.0.0.1:8000");
    console.log("========================================================\n");
  }, 4000);

  // Handle process termination
  const cleanUp = () => {
    console.log("\n[MaterialForge] Stopping development servers...");
    try {
      if (os.platform() === "win32") {
        // Kill subprocess tree on Windows
        if (backendProc.pid) {
          execSync(`taskkill /pid ${backendProc.pid} /T /F`, { stdio: "ignore" });
        }
        if (frontendProc.pid) {
          execSync(`taskkill /pid ${frontendProc.pid} /T /F`, { stdio: "ignore" });
        }
      } else {
        backendProc.kill("SIGINT");
        frontendProc.kill("SIGINT");
      }
    } catch (e) {}
    process.exit();
  };

  process.on("SIGINT", cleanUp);
  process.on("SIGTERM", cleanUp);
}

main().catch((err) => {
  console.error("Failed to run development stack orchestrator:", err);
});
