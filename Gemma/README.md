# Gemma 4 E4B Deployment & Integration Guide

This guide provides step-by-step instructions for deploying Gemma 4 E4B using vLLM on Docker, testing the deployment, and integrating it into DeerFlow via `config.yaml`.

---

## 1. Deployment Guide (Docker)

We provide two optimized configurations for vLLM based on whether you prioritise quality or speed.

| Configuration | Model | Precision | Best For |
| :--- | :--- | :--- | :--- |
| **Standard (BF16)** | `google/gemma-4-E4B-it` | BF16 | Max quality, short sessions |
| **Fast (GPTQ)** | `ciocan/gemma-4-E4B-it-W4A16` | INT4 | Daily chat, RAG, agentic use |

### Prerequisites

1.  **Hugging Face Token:** Create a `.env` file in this directory:
    ```bash
    echo "HF_TOKEN=hf_your_token_here" > .env
    ```
2.  **Accept License:** Visit [Hugging Face](https://huggingface.co/google/gemma-4-E4B-it) and accept the model license.
3.  **GPU Drivers:** Ensure you have the NVIDIA Container Toolkit installed.

### Launching the Model

Choose one of the following commands to start the server:

**Option A: GPTQ (Recommended for daily use)**
```bash
docker compose -f docker-compose.gptq.yml up -d
```

**Option B: BF16 (Full Quality)**
```bash
docker compose up -d
```

**Monitor Progress:**
```bash
# For GPTQ
docker compose -f docker-compose.gptq.yml logs -f vllm
# For BF16
docker compose logs -f vllm
```
Wait for the log message: `Application startup complete`.

---

## 2. Usage & Testing

Once the container is running, the model exposes an OpenAI-compatible API on `http://localhost:8000/v1`.

### Quick Test via cURL
```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma-4-E4B-it-GPTQ",
    "messages": [{"role": "user", "content": "Hello! What can you do?"}],
    "max_tokens": 256
  }'
```
*Note: Use `"model": "gemma-4-E4B-it"` if running the BF16 config.*

### Testing with Python (LiteLLM)
We provide a `test_gemma.py` script. This project uses `uv` for dependency management.

```bash
# Install dependencies
uv sync

# Run the test script
uv run test_gemma.py
```

---

## 3. Integration with DeerFlow (`config.yaml`)

To use your local Gemma model within DeerFlow, add (or update) the following configuration in your root `config.yaml`:

```yaml
models:
  - name: Gemma-4-Local
    display_name: Gemma 4 (vLLM)
    use: deerflow.models.vllm_provider:VllmChatModel
    model: gemma-4-E4B-it-GPTQ  # Must match the --served-model-name in docker-compose
    api_key: none
    base_url: http://localhost:8000/v1
    timeout: 600.0
    max_retries: 2
    max_tokens: 10000
    supports_vision: true
    supports_thinking: true
    when_thinking_enabled:
      extra_body:
        chat_template_kwargs:
          enable_thinking: true
```

### Key Configuration Fields:
*   `use`: Uses the `VllmChatModel` provider which preserves reasoning/thinking content across turns.
*   `base_url`: Points to your local vLLM instance.
*   `supports_thinking`: Enables the model's reasoning capabilities in the UI.
*   `enable_thinking`: Toggles the vLLM reasoning parser.

---

## Technical Details & Flag Explanations

### VRAM Budgets (RTX 4070 Ti SUPER 16 GB)

```
BF16 on 16 GB (--gpu-memory-utilization 0.92):
  Weights          ~9.0 GB  ████████████████████████░░░
  KV cache (8K×4)  ~3.5 GB  ████████░░░░░░░░░░░░░░░░░░░
  Runtime + driver ~2.2 GB  █████░░░░░░░░░░░░░░░░░░░░░░
  Free             ~0.0 GB  — just fits

GPTQ INT4 on 16 GB (--gpu-memory-utilization 0.92):
  Weights          ~2.5 GB  ██████░░░░░░░░░░░░░░░░░░░░░
  KV cache (24K×8) ~6.0 GB  ██████████████░░░░░░░░░░░░░
  Runtime + driver ~2.2 GB  █████░░░░░░░░░░░░░░░░░░░░░░
  Free             ~4.0 GB  — comfortable headroom
```

### Flag Breakdown

| Flag | Why it's used |
| :--- | :--- |
| `--dtype float16` | Required for GPTQ kernels (BF16 is incompatible). |
| `--max-model-len` | Set to 24K for GPTQ or 8K for BF16 to prevent OOM. |
| `--enforce-eager` | Skips CUDA graph capture to save ~1-2 GB of VRAM. |
| `--enable-prefix-caching` | Reuses KV blocks for repeated system prompts/RAG. |
| `--tool-call-parser gemma4` | Enables native tool calling for agentic workflows. |

### Known Limitation: Triton Attention
Gemma 4 uses heterogeneous head dimensions (256 and 512). Since FlashAttention only supports up to 256, vLLM currently falls back to the Triton backend. This is expected and will be optimized in future vLLM releases (watch PR #38891).

---

## Troubleshooting

**OOM on startup:**
* Lower `--max-model-len` (e.g., to 16384 for GPTQ).
* Lower `--max-num-seqs` (e.g., to 4).
* Ensure no other apps are using GPU memory (`nvidia-smi`).

**401 Unauthorized:**
* Ensure `HF_TOKEN` is set in `.env` and you have accepted the license on Hugging Face.

**"gemma4 is not a recognized model type":**
* Ensure you are using the `vllm/vllm-openai:gemma4` image tag.

