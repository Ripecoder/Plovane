# backend

Everything that runs between the frontend and the models: the whiteboard
backend, and Nirmal's handbook blocks. The ML models themselves are in `ml/`.

```
backend/
├── README.md          this file
├── mcp_server/        B04 MCP interface: models and whiteboard as tools for AI agents      BUILT
├── whiteboard/        whiteboard backend: board, slash commands, local API, agent tools   BUILT
├── local_backend/     B03 local Python backend: the app's API on 127.0.0.1              BUILT (recommendation path)
├── cloud_server/      B05 rate limiter + B07 verified-library access (Flask)             B05 BUILT, no auth yet
├── validator/         B11 deterministic diagram validator (library, transport open)      BUILT
├── library_db/        B08 permanent verified library database                           skeleton
└── credits/           B16 contribution and credits backend                              skeleton
```

**Built** folders have working, tested code. **Skeleton** folders hold only
a README: what the block does, the handbook contracts it must follow, what it
connects to, and which gaps are still open. Nirmal owns the blocks marked
above (handbook §2.2).

## How the pieces connect

```
frontend (B01 desktop, B02 CLI)
      │ HTTP 127.0.0.1 /api/v1, §4.1 envelope
      ▼
local_backend (B03) ──── whiteboard (board + project files)
      │                         │
      │                  mcp_server (B04) ──── AI agents (Claude Code, Claude Desktop)
      │                         │ also serves the models (ml/serving)
      │ HTTPS, §8
      ▼
cloud_server (B05 rate limiter + auth) ──► ml/serving/service (B06 recommender)
      │                                          │
      └──► library access (B07) ──► library_db (B08) ◄── credits (B16)
```

## Run what exists

```sh
python -m backend.whiteboard.server --project /path/to/project   # whiteboard API, 127.0.0.1:8700
python -m ml.serving.service.app                                 # recommender API, 127.0.0.1:8600
python -m backend.cloud_server.app                               # B05, 127.0.0.1:8500
python -m backend.local_backend.app                              # B03, 127.0.0.1:8701
claude mcp add plovane -- python -m backend.mcp_server           # tools for Claude Code
```

The local app talks to the cloud, so the recommendation path is: desktop/CLI
→ `local_backend:8701` → `cloud_server:8500` → `ml/serving:8600`.
