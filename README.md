# 🦌 DeerFlow — Agentic Integration Guide

[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)](./backend/pyproject.toml)
[![Node.js](https://img.shields.io/badge/Node.js-22%2B-339933?logo=node.js&logoColor=white)](./Makefile)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

DeerFlow is an open-source **super agent harness** built on LangGraph and LangChain. It orchestrates sub-agents, long-term memory, and sandboxed execution environments — all wired together through extensible skills and MCP tool servers.

> [!IMPORTANT]
> **This repository is adapted for the [Gemma 4 Kaggle Competition](https://www.kaggle.com/competitions/gemma-3-hackathon).** DeerFlow in its upstream form is a general-purpose research framework that is not tailored to specific business needs out of the box. The work done here — skills, MCP integrations, and model configuration — is scoped to demonstrate what Gemma 4 can do as an agentic orchestrator within the competition context. It is not production-ready for arbitrary business deployments without further hardening.

This guide covers configuration and extension. You will rarely need to touch the source code.

---

## Table of Contents

- [Architecture at a Glance](#architecture-at-a-glance)
- [Running Locally](#running-locally)
- [Sandbox Strategy](#sandbox-strategy)
- [The Three Integration Points](#the-three-integration-points)
  - [1. Skills — Encoding Business Concepts](#1-skills--encoding-business-concepts)
  - [2. MCP Integration — Connecting Tools](#2-mcp-integration--connecting-tools)
  - [3. Model Configuration — Deploying Gemma 4](#3-model-configuration--deploying-gemma-4)
- [LangSmith Tracing](#langsmith-tracing)
- [LangGraph Middlewares](#langgraph-middlewares)
- [IM Channels — Telegram & WhatsApp](#im-channels--telegram--whatsapp)
- [Security Notice](#security-notice)
- [Acknowledgments](#acknowledgments)

---

## Architecture at a Glance

```
Browser / IM Channel → http://localhost:2026
                               │
                         [Nginx :2026]
                        /             \
          /api/langgraph/*           /api/*            / (everything else)
                │                      │                       │
       LangGraph :2024          Gateway API :8001         Next.js :3000
       (AI agent engine)        (models, skills,          (web UI)
                                 memory, uploads)
```

The lead agent in LangGraph spawns sub-agents, invokes MCP tools, reads/writes files through the sandbox, and applies middlewares at each step of the graph. The Gateway API is the REST surface for configuration and management.

---

## Running Locally

For Windows developers, a detailed step-by-step guide covering prerequisites (Git, uv, Node.js, pnpm, nginx), service startup, and troubleshooting is in [LOCAL_DEV_GUIDE.md](./LOCAL_DEV_GUIDE.md).

> **Tip:** If you use GitHub Copilot, paste this into the chat and let it walk you through the full setup interactively:
>
> ```text
> Read @LOCAL_DEV_GUIDE.md and walk me through running DeerFlow locally on Windows step by step.
> ```

The four services and their ports:

| Service | Port | Purpose |
|---|---|---|
| Nginx | `2026` | Unified entry point |
| LangGraph Server | `2024` | AI agent engine |
| Gateway API | `8001` | REST management API |
| Next.js Frontend | `3000` | Web UI |

Open `http://localhost:2026` in your browser after all services start.

---

## Sandbox Strategy

DeerFlow supports three sandbox modes. The right choice depends on your deployment target.

### Local Sandbox (Default — Recommended for Development)

The local sandbox runs file operations directly on the host filesystem. It is the **fastest option** with the lowest latency because there is no container startup overhead, no Docker socket round-trip, and no network hop.

File tools (`read_file`, `write_file`, `ls`, `glob`, `grep`, `str_replace`) are always available. Host bash execution is disabled by default and should only be enabled for fully trusted local workflows.

```yaml
# config.yaml
sandbox:
  use: deerflow.sandbox.local:LocalSandboxProvider
  allow_host_bash: false   # set true only if you fully trust the agent's commands
```

Skills that produce Markdown output (reports, plans, structured data) rely on the file write tools. Make sure `file:read` and `file:write` tool groups are enabled in `config.yaml`:

```yaml
tool_groups:
  - name: file:read
  - name: file:write
```

### Docker Sandbox (VBS / VM Deployments)

When deploying on a virtual machine or bare-metal server where Docker is available, you can switch to the container-based sandbox. This gives the agent an isolated execution environment while still keeping iteration fast — containers are reused across turns within a session.

```yaml
sandbox:
  use: deerflow.community.aio_sandbox:AioSandboxProvider
  # image: enterprise-public-cn-beijing.cr.volces.com/vefaas-public/all-in-one-sandbox:latest
  # replicas: 3
```

Run `make docker-init` once to pull the sandbox image before starting.

### Kubernetes Provisioner (K8s Clusters)

For Kubernetes deployments, the provisioner service manages sandbox pods. Each session gets a dedicated pod with full isolation.

```yaml
sandbox:
  use: deerflow.community.aio_sandbox:AioSandboxProvider
  provisioner_url: http://provisioner:8002
```

> **Note:** The provisioner sandbox involves significant pod scheduling latency and is not practical for interactive or low-latency workflows. Use it when isolation and scalability are requirements that outweigh response time. For most development and staging environments, the Docker sandbox is the better trade-off.

---

## The Three Integration Points

Extending DeerFlow for a specific business domain requires changes in exactly three places — no source code modifications needed.

### 1. Skills — Encoding Business Concepts

Skills are Markdown files that define workflows, best practices, and instructions for the agent. They encode your business concepts: what the agent should do, how it should reason about a domain, and which tools it should prefer.

Skills live under `skills/public/` (built-in) or a custom directory you mount. Two kinds of skills exist:

| Kind | What it does | File tools needed? |
|---|---|---|
| **Plugin** | Describes a capability — wraps an MCP tool or API with instructions | No |
| **Workflow** | Multi-step process that produces files (reports, plans, Markdown output) | **Yes** — needs `file:read` and `file:write` enabled |

For workflow skills, the agent writes intermediate and final Markdown files to the sandbox filesystem. The LLM reads these files back in subsequent turns to maintain context across long tasks. This is why `file:read` and `file:write` tool groups must be active when running workflows.

**Example workflow skill structure:**

```
skills/public/
├── my-domain/
│   └── SKILL.md        ← defines the workflow and instructions
└── my-plugin/
    └── SKILL.md        ← describes how to use a specific MCP server
```

A skill file is plain Markdown. The agent loads it into its context when the task matches the skill's domain. Keep skills focused — one concept per file.

### 2. MCP Integration — Connecting Tools

MCP (Model Context Protocol) servers expose tools that the agent can call. Configure them in `extensions_config.json`. No code changes are required — DeerFlow discovers and registers MCP tools at startup.

This is where **Gemma 4** shines: it is a strong orchestrator that can spawn general-purpose sub-agents, inject them with specific instructions and skills, and coordinate across multiple MCP servers to complete complex multi-step tasks.

#### Method 1: STDIO (Subprocess)

Run an MCP server as a local subprocess. The agent communicates over stdin/stdout. This is the most common approach for local tools.

```json
{
  "mcpServers": {
    "filesystem": {
      "enabled": true,
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/workspace"],
      "env": {}
    },
    "github": {
      "enabled": true,
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "$GITHUB_TOKEN"
      }
    }
  }
}
```

Environment variable values prefixed with `$` are automatically resolved from your `.env` file at startup.

#### Method 2: STDIO Proxy via `npx` (Remote MCP over HTTP)

Some MCP servers are hosted remotely over HTTP but expose a stdio-compatible proxy via `npx`. This lets you use remote MCPs without running a local server process:

```json
{
  "mcpServers": {
    "remote-tool": {
      "enabled": true,
      "type": "stdio",
      "command": "npx",
      "args": [
        "-y",
        "remote-mcp-package",
        "--allow-http",
        "--header", "Authorization: Bearer $REMOTE_TOOL_API_KEY"
      ],
      "env": {
        "REMOTE_TOOL_API_KEY": "$REMOTE_TOOL_API_KEY"
      }
    }
  }
}
```

Define the API key in your `.env` file:

```env
REMOTE_TOOL_API_KEY=your-api-key-here
```

The `--header "Authorization: Bearer $REMOTE_TOOL_API_KEY"` flag injects the token into each outbound request. The env variable inside the `env` block ensures the process can read it.

#### Method 3: HTTP (Current Standard)

Streamable HTTP is the current standard MCP transport. Point DeerFlow at any running MCP HTTP endpoint:

```json
{
  "mcpServers": {
    "my-http-server": {
      "enabled": true,
      "type": "http",
      "url": "https://mcp.example.com/mcp",
      "headers": {
        "Authorization": "Bearer $MY_SERVICE_API_KEY"
      }
    }
  }
}
```

For services that require OAuth, DeerFlow supports automatic token acquisition and refresh:

```json
{
  "mcpServers": {
    "secure-api": {
      "enabled": true,
      "type": "http",
      "url": "https://api.example.com/mcp",
      "oauth": {
        "enabled": true,
        "token_url": "https://auth.example.com/oauth/token",
        "grant_type": "client_credentials",
        "client_id": "$MCP_OAUTH_CLIENT_ID",
        "client_secret": "$MCP_OAUTH_CLIENT_SECRET",
        "scope": "mcp.read mcp.write"
      }
    }
  }
}
```

#### Method 4: SSE (Deprecated)

SSE transport is still supported for backward compatibility but is deprecated. Migrate to HTTP (`"type": "http"`) when possible.

```json
{
  "mcpServers": {
    "legacy-sse-server": {
      "enabled": true,
      "type": "sse",
      "url": "https://legacy.example.com/sse"
    }
  }
}
```

#### Deferred Tool Loading (Large MCP Deployments)

When many MCP servers expose a large number of tools, loading all of them into the context window at once hurts performance. Enable deferred loading to list tools by name in the system prompt and only load them when the agent explicitly requests one:

```yaml
# config.yaml
tool_search:
  enabled: true
```

### 3. Model Configuration — Deploying Gemma 4

Self-hosted models (via SGLang or vLLM) connect to DeerFlow through LiteLLM's OpenAI-compatible interface. This is a one-time configuration change in `config.yaml`.

#### SGLang

```bash
# Start SGLang server
python -m sglang.launch_server \
  --model-path google/gemma-3-27b-it \
  --port 30000
```

```yaml
# config.yaml
models:
  - name: gemma4-sglang
    display_name: Gemma 4 27B (SGLang)
    use: langchain_openai:ChatOpenAI
    model: google/gemma-3-27b-it
    base_url: http://localhost:30000/v1
    api_key: dummy                      # SGLang does not require a real key
    request_timeout: 600.0
    max_retries: 2
    max_tokens: 8192
    temperature: 0.7
    supports_vision: true
```

#### vLLM

```bash
# Start vLLM server
vllm serve google/gemma-3-27b-it \
  --port 8000 \
  --reasoning-parser gemma
```

```yaml
# config.yaml
models:
  - name: gemma4-vllm
    display_name: Gemma 4 27B (vLLM)
    use: deerflow.models.vllm_provider:VllmChatModel
    model: google/gemma-3-27b-it
    base_url: http://localhost:8000/v1
    api_key: $VLLM_API_KEY
    request_timeout: 600.0
    max_retries: 2
    max_tokens: 8192
    supports_vision: true
```

#### LiteLLM Proxy (Multi-Model Gateway)

If you run a LiteLLM proxy in front of multiple backends, point DeerFlow at the proxy URL:

```yaml
models:
  - name: gemma4
    display_name: Gemma 4 (LiteLLM)
    use: langchain_openai:ChatOpenAI
    model: gemma4/gemma-3-27b-it       # model name as configured in LiteLLM
    base_url: http://localhost:4000/v1  # LiteLLM proxy
    api_key: $LITELLM_API_KEY
    request_timeout: 600.0
    supports_vision: true
```

---

## LangSmith Tracing

Enable LangSmith to get full visibility into every LLM call, tool invocation, and agent step. This is essential for iterating on skills and MCP tool prompts — you can see exactly what the model received and what it returned.

Add to your `.env` file:

```env
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=lsv2_pt_xxxxxxxxxxxxxxxx
LANGSMITH_PROJECT=deerflow-dev
```

No changes to `config.yaml` are needed. Tracing activates automatically when the environment variables are present.

Once enabled, every agent run appears in the LangSmith UI at `https://smith.langchain.com`. You can inspect the full message history the model saw, which tools were called with what inputs, and where latency is concentrated — all of which is useful when tuning skill instructions or debugging MCP tool outputs.

---

## LangGraph Middlewares

Middlewares are the extensibility layer of the LangGraph agent loop. They wrap each step of agent execution and can inspect or modify messages before and after the model is called.

If you are familiar with **Claude Code hooks**, middlewares serve the same purpose: they are interception points that let you enforce policies, transform outputs, or inject context without rewriting the core agent logic. Just as Claude Code hooks fire before and after tool use, LangGraph middlewares fire at defined points in the graph traversal.

The built-in middlewares live in [`backend/packages/harness/deerflow/agents/middlewares/`](./backend/packages/harness/deerflow/agents/middlewares/):

| Middleware | Purpose |
|---|---|
| `clarification_middleware.py` | Intercepts `ask_clarification` tool calls and presents questions to the user |
| `memory_middleware.py` | Reads and writes long-term memory around each agent turn |
| `summarization_middleware.py` | Compresses completed sub-task context to prevent context window overflow |
| `title_middleware.py` | Auto-generates thread titles from the first user message |
| `sandbox_audit_middleware.py` | Audits file and bash operations before they execute |
| `loop_detection_middleware.py` | Detects and breaks infinite tool-call loops |
| `token_usage_middleware.py` | Collects and surfaces token usage metadata |
| `tool_error_handling_middleware.py` | Normalizes tool errors into recoverable agent messages |
| `dangling_tool_call_middleware.py` | Injects placeholder results for tool calls that were never executed |
| `subagent_limit_middleware.py` | Enforces maximum sub-agent spawn counts |
| `deferred_tool_filter_middleware.py` | Filters deferred tool results based on tool search state |
| `llm_error_handling_middleware.py` | Catches and recovers from LLM API errors |
| `todo_middleware.py` | Tracks task progress across multi-step agent runs |
| `thread_data_middleware.py` | Manages per-thread state persistence |
| `uploads_middleware.py` | Injects uploaded file context into the agent's working state |
| `view_image_middleware.py` | Pre-processes image inputs for vision-capable models |

**When would you add a middleware?** If you need to enforce business rules across every agent turn — rate limiting, output filtering, domain-specific context injection, compliance logging — a middleware is the right place. Add new middleware files to the same directory and register them in the agent's middleware chain. You do not need to modify the core agent logic.

For most integrations, the built-in middlewares are sufficient and no additions are needed.

---

## IM Channels — Telegram & WhatsApp

DeerFlow supports receiving tasks from messaging platforms. All channels use long-polling or WebSocket connections — no public IP or webhook registration is required.

### Telegram (Fully Supported)

Telegram is the most straightforward channel to set up. See [LOCAL_DEV_GUIDE.md — Section 11](./LOCAL_DEV_GUIDE.md#11-connecting-a-telegram-channel) for complete setup instructions, including bot creation, token configuration, allowed user lists, and startup verification.

Summary:

1. Create a bot via `@BotFather` in Telegram and copy the token.
2. Add `TELEGRAM_BOT_TOKEN=...` to your `.env` file.
3. Enable the channel in `config.yaml`:

```yaml
channels:
  langgraph_url: http://localhost:2024
  gateway_url: http://localhost:8001

  telegram:
    enabled: true
    bot_token: $TELEGRAM_BOT_TOKEN
    allowed_users: []   # empty = allow anyone
```

4. Start only the LangGraph server and Gateway API — the frontend is not required for IM channels.

### WhatsApp (Planned)

WhatsApp integration is on the roadmap. When added, configuration will follow the same pattern as other channels in `config.yaml`. Contributions are welcome.

Available commands once a channel is connected:

| Command | Description |
|---|---|
| `/new` | Start a new conversation thread |
| `/status` | Show current thread info |
| `/models` | List configured models |
| `/memory` | View agent memory |
| `/help` | Show all commands |

---

## Security Notice

DeerFlow is designed for trusted local or private network deployments. The agent has write access to its sandbox filesystem and can execute tools with significant capabilities.

**Do not expose DeerFlow directly to the public internet without:**
- An authentication gateway in front (e.g., nginx with basic auth or OAuth proxy)
- An IP allowlist restricting access to known clients
- The `allowed_users` list configured for any IM channels

For production deployments, place DeerFlow behind a reverse proxy and apply access controls before traffic reaches the LangGraph or Gateway ports.

---

## Acknowledgments

DeerFlow is built on [LangChain](https://github.com/langchain-ai/langchain) and [LangGraph](https://github.com/langchain-ai/langgraph). The multi-agent orchestration primitives, streaming protocol, and tool-call infrastructure come from these projects.

- **[Daniel Walnut](https://github.com/hetaoBackend/)** — core author
- **[Henry Li](https://github.com/magiccube/)** — core author
