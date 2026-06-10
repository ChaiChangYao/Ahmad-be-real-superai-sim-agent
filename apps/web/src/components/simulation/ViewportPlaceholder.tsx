"use client";

export function ViewportPlaceholder({ message = "Loading 3D viewer…" }: { message?: string }) {
  return (
    <div className="flex h-full min-h-[280px] w-full flex-col items-center justify-center gap-3 rounded-md border-2 border-dashed border-sky-500/50 bg-slate-100 text-slate-700">
      <div className="text-sm font-medium text-sky-300">Genesis Simulator Viewport</div>
      <div className="text-xs text-slate-600">{message}</div>
      <div className="text-[10px] text-slate-500">Grid + robot appear here once WebGL loads</div>
    </div>
  );
}
