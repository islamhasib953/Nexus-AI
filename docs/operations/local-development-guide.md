# Nexus-AI — Local Development Guide

**Target Environment:** Windows 11 / PowerShell 7+ (also compatible with macOS / Linux)  
**Last Updated:** 2026-10-19  

---

## 1. Prerequisites

Before starting, ensure the following runtimes and tools are installed:

| Tool | Required Version | Verification Command | Download / Install |
|---|---|---|---|
| **Python** | 3.12+ | `uv run python --version` | Managed automatically by `uv` |
| **uv** | Latest | `uv --version` | https://docs.astral.sh/uv/getting-started/installation/ |
| **Node.js** | 22+ | `node --version` | https://nodejs.org/ |
| **npm** | 11+ | `npm --version` | Bundled with Node.js |
| **Git** | 2.40+ | `git --version` | https://git-scm.com/ |

---

## 2. Quickstart (Minimal Mock Setup)

### Step 1: Set up Environment Files

From the repository root in PowerShell:

```powershell
# Copy the safe example configuration
Copy-Item .env.example .env
Copy-Item .env.example apps/api/.env
```

### Step 2: Install Dependencies

```powershell
# Backend (Python virtualenv and locked dependencies)
uv sync --directory apps/api

# Frontend (Node modules)
npm ci --prefix apps/web
```

### Step 3: Start the Backend

In your first terminal window:

```powershell
uv run --directory apps/api uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Verify backend health:
```powershell
Invoke-RestMethod http://localhost:8000/api/v1/health/live
# Expected: {"status":"ok","service":"nexus-ai-api","version":"0.1.0"}
```

### Step 4: Start the Frontend

In a second terminal window:

```powershell
npm run dev --prefix apps/web
```

Open your browser to: **`http://localhost:5173`**

---

## 3. Configuring Groq (Real LLM Provider)

Nexus-AI supports Groq for ultra-fast, hosted inference using models like `llama-3.3-70b-versatile` and `llama-3.1-8b-instant`.

### Step 1: Obtain a Free Groq API Key

1. Go to the official Groq Console: **[https://console.groq.com/keys](https://console.groq.com/keys)**
2. Sign in (or create a free account — no credit card required).
3. Click **"Create API Key"**.
4. Give it a name (e.g., `nexus-ai-local`) and copy the generated key (`gsk_...`).

> ⚠️ **SECURITY WARNING:**  
> Never commit your API key to Git, paste it in public forums, or share it in screenshots. Keep it exclusively in your local `.env.local` file.

### Step 2: Configure `.env.local`

Create a file named `.env.local` in the project root (`e:\learn\Nexus-AI\.env.local`).  
*(Because `.env.local` is listed in `.gitignore`, Git will never track it).*

Add the following lines to your `.env.local`:

```ini
# Enable Groq as the active LLM provider
MODEL_PROVIDER=groq
LLM_PRIMARY_MODEL_ID=groq-llama-3.3-70b
GROQ_API_KEY=gsk_your_actual_key_here
```

### Step 3: Restart the Backend

Restart your backend server:
```powershell
uv run --directory apps/api uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The application will automatically detect `.env.local`, validate your Groq API key at startup, and route chat completions to Groq!

---

## 4. Optional External Services

### 4.1 Ollama (Local Open-Weight Inference)

If you prefer 100% local, offline inference without external API keys:

1. **Install Ollama for Windows:**  
   Download from: **[https://ollama.com/download/OllamaSetup.exe](https://ollama.com/download/OllamaSetup.exe)**
2. **Pull the Qwen 3 model:**  
   ```powershell
   ollama pull qwen3:8b
   ```
3. **Configure `.env.local`:**  
   ```ini
   MODEL_PROVIDER=ollama
   LLM_PRIMARY_MODEL_ID=ollama-qwen3
   OLLAMA_BASE_URL=http://localhost:11434
   ```

### 4.2 Qdrant (Vector Database for Semantic RAG)

Qdrant enables high-performance vector search for document retrieval:

```powershell
# Run local Qdrant container (requires Docker Desktop)
docker run -p 6333:6333 -v qdrant_storage:/qdrant/storage:z qdrant/qdrant
```

In `.env.local`:
```ini
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=nexus_chunks
```

---

## 5. Running Verification Checks

Before pushing any changes or verifying your environment, run the complete test suite:

```powershell
# 1. Backend Linting & Formatting
uv run --directory apps/api ruff check .
uv run --directory apps/api ruff format --check .

# 2. Backend Automated Tests (69 tests, >=90% coverage required)
uv run --directory apps/api pytest

# 3. Frontend Typecheck, Lint, Tests, and Build
npm run typecheck --prefix apps/web
npm run lint --prefix apps/web
npm run test --prefix apps/web -- --run
npm run build --prefix apps/web

# 4. Repository Governance Scripts
powershell -ExecutionPolicy Bypass -File scripts/validate-phase2.ps1
powershell -ExecutionPolicy Bypass -File scripts/validate-phase14.ps1
```

---

## 6. How to Shut Down

To cleanly shut down local development processes:
- In the backend terminal: Press `Ctrl + C`.
- In the frontend terminal: Press `Ctrl + C` and type `Y` if prompted.
- SQLite database data persists under `data/nexus.db` (or in-memory for tests).
