from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.paths import ensure_base_paths
from app.routes import agentic, assets, genesis, genesis_catalog, genesis_controls, genesis_showcase, genesis_workbench, health, imports, manifests, projects, scenarios, settings, simulations, tests


ensure_base_paths()

app = FastAPI(title="Buildables Sim Sandbox API", version="0.1.0")


@app.on_event("startup")
def warm_genesis_runtime() -> None:
    """Warm Genesis in background so /health responds immediately for the web UI."""

    def _warm() -> None:
        try:
            from app.services.genesis.genesis_runtime import genesis_runtime
            from app.services.genesis_native.genesis_runtime import ensure_genesis_initialized

            status = genesis_runtime.status()
            if status.installed:
                ensure_genesis_initialized()
        except Exception:
            pass

    import threading

    threading.Thread(target=_warm, name="genesis-warm", daemon=True).start()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(agentic.router)
app.include_router(genesis.router)
app.include_router(genesis_showcase.router)
app.include_router(genesis_workbench.router)
app.include_router(genesis_controls.router)
app.include_router(projects.router)
app.include_router(settings.router)
app.include_router(manifests.router)
app.include_router(assets.router)
app.include_router(imports.router)
app.include_router(scenarios.router)
app.include_router(simulations.router)
app.include_router(genesis_catalog.router)
app.include_router(tests.router)
