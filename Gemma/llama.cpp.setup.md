# llama.cpp Setup Guide — Gemma 4 E4B Multimodal

**Model:** `unsloth/gemma-4-E4B-it-GGUF` | **Quant:** `IQ4_NL` (4.84 GB)
**Engine:** llama.cpp (llama-server)

---

## Step 1 — Install llama.cpp (Windows)

Open Command Prompt as Administrator and run:

```cmd
winget install -e --id ggml.llamacpp
```

Verify installation:

```cmd
llama-server --version
llama-cli --version
```

If commands not found, restart your terminal (Command Prompt or PowerShell) so `llama-server` and `llama-cli` are on `PATH`.

> **Tip:** You can test the model in your terminal before starting the server using `llama-cli`:
> ```cmd
> llama-cli -hf unsloth/gemma-4-E4B-it-GGUF:IQ4_NL -p "Hello!" -n 64
> ```

---

## Step 2 — Set Environment Variables (Windows)

Open Command Prompt as Administrator for all commands below.

### HF_TOKEN (required — gated model)

Get token at https://huggingface.co/settings/tokens (use **read** token).

```cmd
setx HF_TOKEN "hf_your_token_here"
```

### HF_HOME (optional but recommended)

Direct downloads to `Gemma\model_cache\` so models stay with project (not in `C:\Users\<username>\.cache\`):

```cmd
setx HF_HOME "E:\Compeition\deer-flow\Gemma\model_cache"
```

### LLAMA_API_KEY (optional but recommended for security)

Set the API key for llama-server:

```cmd
setx LLAMA_API_KEY "my_secret_key"
```

### Verify Environment Variables

**Close and reopen Command Prompt**, then verify:

```cmd
echo %HF_TOKEN%
echo %HF_HOME%
echo %LLAMA_API_KEY%
```

Each should print its value. If blank, `setx` didn't work — try running Command Prompt as Administrator.

> **Note:** `setx` makes variables permanent (survives restarts). For temporary (current session only), use `set` instead of `setx`, but you'll need to re-run after each terminal restart.

---

## Step 3 — Run the Model (Windows)

Open a **new Command Prompt** or **PowerShell** (so environment variables load).

### Method 1 — HuggingFace Auto-Stream (recommended first run)

llama.cpp downloads, caches, and runs the model in one command (Windows Command Prompt):

```cmd
llama-server -hf unsloth/gemma-4-E4B-it-GGUF:IQ4_NL --host 0.0.0.0 --port 8080 --api-key %LLAMA_API_KEY% -t 20 -ngl 999 -fa -c 0
```

**When to use:** Let llama.cpp manage downloads and caching. If `HF_HOME` is set (recommended), files land in `Gemma\model_cache\` (kept out of git). Otherwise, they go to your system cache at `C:\Users\<username>\.cache\huggingface\hub\`.

**For text-only** (skip vision, save VRAM):

```cmd
llama-server -hf unsloth/gemma-4-E4B-it-GGUF:IQ4_NL --no-mmproj --host 0.0.0.0 --port 8080 --api-key %LLAMA_API_KEY% -t 20 -ngl 999 -fa -c 0
```

> **PowerShell users:** Use `$env:LLAMA_API_KEY` instead of `%LLAMA_API_KEY%`:
> ```powershell
> llama-server -hf unsloth/gemma-4-E4B-it-GGUF:IQ4_NL --host 0.0.0.0 --port 8080 --api-key $env:LLAMA_API_KEY -t 20 -ngl 999 -fa -c 0
> ```

---

### Method 2 — Manual Local Cache (offline / full control)

Use when you are offline or need a specific cached version.

**First, locate your snapshot hash (Windows File Explorer):**

Navigate to your cache location:
- If `HF_HOME` set: `%HF_HOME%\hub\models--unsloth--gemma-4-E4B-it-GGUF\snapshots\`
- Otherwise: `C:\Users\<username>\.cache\huggingface\hub\models--unsloth--gemma-4-E4B-it-GGUF\snapshots\`

Inside `snapshots\`, you'll see folders like `a1b2c3d4...`. Pick one and note the full hash.

To verify the hash, open `refs\main` in Notepad — it shows the commit hash.

**Check your cache root (Command Prompt):**

```cmd
echo %HF_HOME%
```

If blank, cache is at `C:\Users\<username>\.cache\huggingface\hub\`.

**Run from local cache (with vision, Command Prompt):**

```cmd
llama-server -m "E:\Compeition\deer-flow\Gemma\model_cache\hub\models--unsloth--gemma-4-E4B-it-GGUF\snapshots\<HASH>\gemma-4-E4B-it-IQ4_NL.gguf" --mmproj "E:\Compeition\deer-flow\Gemma\model_cache\hub\models--unsloth--gemma-4-E4B-it-GGUF\snapshots\<HASH>\mmproj-BF16.gguf" --host 0.0.0.0 --port 8080 --api-key %LLAMA_API_KEY% -t 20 -ngl 999 -fa -c 0
```

**Or, if cache is on a custom path:**

```cmd
llama-server -m "E:\Compeition\lamma\cache\models--unsloth--gemma-4-E4B-it-GGUF\snapshots\<HASH>\gemma-4-E4B-it-IQ4_NL.gguf" --mmproj "E:\Compeition\lamma\cache\models--unsloth--gemma-4-E4B-it-GGUF\snapshots\<HASH>\mmproj-BF16.gguf" --host 0.0.0.0 --port 8080 --api-key %LLAMA_API_KEY% -t 20 -ngl 999 -fa -c 0
```

**Force offline (never touch the internet):**

Add `--offline` flag at the end:

```cmd
llama-server -m "E:\...\gemma-4-E4B-it-IQ4_NL.gguf" --mmproj "E:\...\mmproj-BF16.gguf" --host 0.0.0.0 --port 8080 --api-key %LLAMA_API_KEY% -t 20 -ngl 999 -fa -c 0 --offline
```

---

## Available Quantizations

From `unsloth/gemma-4-E4B-it-GGUF` on Intel Core i7 14th Gen (64 GB RAM):

| Bits | Quant | Size | Notes |
|------|-------|------|-------|
| 2-bit | UD-IQ2_M | 3.53 GB | Smallest, most lossy |
| 2-bit | UD-Q2_K_XL | 3.74 GB | |
| 3-bit | UD-IQ3_XXS | 3.7 GB | |
| 3-bit | Q3_K_S | 3.86 GB | |
| 3-bit | Q3_K_M | 4.06 GB | |
| 3-bit | UD-Q3_K_XL | 4.56 GB | |
| 4-bit | **IQ4_NL** | **4.84 GB** | **← this guide uses this** |
| 4-bit | IQ4_XS | 4.72 GB | Slightly smaller 4-bit |
| 4-bit | Q4_K_S | 4.84 GB | |
| 4-bit | Q4_0 | 4.84 GB | |
| 4-bit | Q4_1 | 5.07 GB | |
| 4-bit | Q4_K_M | 4.98 GB | |
| 4-bit | UD-Q4_K_XL | 5.1 GB | |
| 5-bit | Q5_K_S | 5.4 GB | |
| 5-bit | Q5_K_M | 5.48 GB | |
| 5-bit | UD-Q5_K_XL | 6.65 GB | |
| 6-bit | Q6_K | 7.07 GB | |
| 6-bit | UD-Q6_K_XL | 7.46 GB | |
| 8-bit | Q8_0 | 8.19 GB | Near-lossless |
| 8-bit | UD-Q8_K_XL | 8.66 GB | |
| 16-bit | BF16 | 15.1 GB | Full precision |

To use a different quant, replace `IQ4_NL` in the `-hf` command:

```cmd
llama-server -hf unsloth/gemma-4-E4B-it-GGUF:Q8_0 ...
```

---

## Parameter Glossary

| Parameter | Explanation | When to Use |
|-----------|-------------|-------------|
| `-m`, `--model` | Path to local `.gguf` file (Windows: use backslashes) | `"C:\path\to\model.gguf"` |
| `-hf` | Pull from HuggingFace as `repo:quant` | `unsloth/gemma-4-E4B-it-GGUF:IQ4_NL` |
| `--mmproj` | Path to multimodal projector (vision bridge) | Required for image input when using `-m` |
| `--no-mmproj` | Disable vision support | Text-only inference; saves VRAM |
| `-ngl`, `--n-gpu-layers` | Layers to offload to GPU | `999` = full GPU, `0` = CPU only |
| `-t`, `--threads` | CPU threads for inference | Match physical core count (e.g., `20` for i7-14th) |
| `-c`, `--ctx-size` | Context window size | `0` = use model max (128K for E4B) |
| `-fa`, `--flash-attn` | Flash Attention optimization | Always use with GPU; disable for CPU-only |
| `--host` | Server listen address | `127.0.0.1` local only; `0.0.0.0` network |
| `--port` | API port (default 8080) | Change if 8080 is occupied |
| `--api-key` | API password | Use when `--host 0.0.0.0` for security |
| `--mlock` | Pin model in RAM (no disk swap) | When RAM is plentiful, prevents lag spikes |
| `-np`, `--parallel` | Concurrent request slots | Set `>1` for multi-user/multi-app scenarios |
| `--offline` | Block all internet access | Force use of local cache only |

---

## Cache Location Reference (Windows)

| Variable | Effect | Example (Command Prompt) |
|----------|--------|---------|
| `HF_HOME` | Moves entire HF cache root | `setx HF_HOME "E:\Compeition\deer-flow\Gemma\model_cache"` |
| `HF_HUB_CACHE` | Moves only the model hub cache | `setx HF_HUB_CACHE "E:\Compeition\deer-flow\Gemma\model_cache\hub"` |
| `LLAMA_CACHE` | llama.cpp-specific cache override | `setx LLAMA_CACHE "E:\Compeition\deer-flow\Gemma\model_cache"` |
| *(default)* | System default (user profile) | `C:\Users\<username>\.cache\huggingface\hub` |

**Priority order (highest wins):** `LLAMA_CACHE` → `HF_HUB_CACHE` → `HF_HOME` → system default.

**Check current value (Command Prompt):**

```cmd
echo %HF_HOME%
echo %HF_HUB_CACHE%
echo %LLAMA_CACHE%
```

**For this project:** Set `HF_HOME` to `E:\Compeition\deer-flow\Gemma\model_cache` so models download locally and stay out of git.

---

## Verify Server is Running (Windows)

Once llama-server starts, verify it's ready in a **new Command Prompt or PowerShell**:

**Check API health:**

```cmd
curl http://localhost:8080/health
```

**List available models:**

```cmd
curl http://localhost:8080/v1/models
```

**Or use PowerShell:**

```powershell
Invoke-RestMethod -Uri "http://localhost:8080/health"
Invoke-RestMethod -Uri "http://localhost:8080/v1/models"
```

Output should show `"ok"` for health and your model name for `/v1/models`.

---

## Quick Start (Windows)

**Step 1:** Open Command Prompt as Administrator and run (one time):

```cmd
winget install -e --id ggml.llamacpp
setx HF_TOKEN "hf_your_token_here"
setx HF_HOME "E:\Compeition\deer-flow\Gemma\model_cache"
setx LLAMA_API_KEY "my_secret_key"
```

**Step 2:** Close Command Prompt, then open a **new Command Prompt** and run:

```cmd
llama-server -hf unsloth/gemma-4-E4B-it-GGUF:IQ4_NL --host 0.0.0.0 --port 8080 --api-key %LLAMA_API_KEY% -t 20 -ngl 999 -fa -c 0
```

**Step 3:** Access the server:

- REST API: `http://localhost:8080/v1/chat/completions`
- Web UI: `http://localhost:8080/` (built-in chat interface)

Models download to `Gemma\model_cache\` automatically (excluded from git).

> Replace `hf_your_token_here` and `my_secret_key` with your actual values.
