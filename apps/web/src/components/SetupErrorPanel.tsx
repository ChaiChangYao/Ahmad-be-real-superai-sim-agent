"use client";

export function SetupErrorPanel({ message }: { message: string }) {
  const lower = message.toLowerCase();
  const isApiDown = lower.includes("cannot reach api");
  const isTimeout = lower.includes("timed out");

  return (
    <div className="rounded border border-amber-300 bg-amber-50 px-3 py-2 text-xs text-amber-950">
      <span className="font-semibold">Setup issue:</span> {message}
      <div className="mt-2 space-y-1 text-[10px] text-amber-900">
        {isApiDown ? (
          <>
            <div className="font-medium">Start the API in a separate terminal from the repo root:</div>
            <code className="block rounded bg-amber-100/80 px-2 py-1">uvicorn main:app --app-dir apps/api --host 127.0.0.1 --port 8000</code>
            <div>Then start the web UI: <code className="rounded bg-amber-100/80 px-1">npm run dev:web</code></div>
            <div className="text-amber-800">Tip: skip <code className="px-0.5">--reload</code> while running Genesis simulations (avoids LLVM threading crashes on Windows).</div>
            <div>If port 8000 is already in use, stop the old process or restart it so new routes load.</div>
          </>
        ) : isTimeout ? (
          <>
            <div className="font-medium">The API is slow to respond — often Genesis is initializing on first boot.</div>
            <div>Wait ~30–60s, refresh the page, and ensure only one uvicorn instance is running on port 8000.</div>
          </>
        ) : (
          <div>See docs/GENESIS_SETUP_WINDOWS.md for Python, PyTorch, and genesis-world setup.</div>
        )}
      </div>
    </div>
  );
}
