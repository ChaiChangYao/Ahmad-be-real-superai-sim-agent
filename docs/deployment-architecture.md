# Deployment Architecture

## Split

| Component | Host | Notes |
|-----------|------|-------|
| Frontend (`apps/web`) | Vercel or static CDN | Next.js UI only |
| Python API (`apps/api`) | Long-running worker VM/container | FastAPI + Genesis subprocess |
| Simulation runs | Same host as API (local backend) | Not Vercel serverless |

Genesis simulations are **long-running subprocesses** and must not run inside Vercel serverless functions.

## Environment variables

| Variable | Purpose |
|----------|---------|
| `NEXT_PUBLIC_API_BASE_URL` | Frontend → API base URL |
| `NEXT_PUBLIC_AGENTIC_API_URL` | Optional override for agentic endpoints (defaults to API base) |
| `BUILDABLES_EXECUTION_BACKEND` | `local` \| `docker` \| `e2b` |
| `E2B_API_KEY` | Optional cloud sandbox |
| `GENESIS_WORLD_ROOT` | Optional Genesis examples path |

## CORS

API enables `allow_origins=["*"]` for dev. Production should restrict to Vercel frontend origin.

## Artifact storage

Run artifacts live on API host filesystem under `sim-data/projects/`. For multi-instance deployment, use shared storage or object store (future).

## Optional backends

- **Docker**: not configured in MVP — returns structured `backend_unavailable`
- **E2B**: requires `e2b` package + `E2B_API_KEY`; Genesis GPU support unverified
