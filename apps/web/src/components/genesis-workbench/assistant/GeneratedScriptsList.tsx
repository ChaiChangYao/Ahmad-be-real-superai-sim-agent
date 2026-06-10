"use client";

import { useCallback, useEffect, useState } from "react";
import { deleteGeneratedScript, listGeneratedScripts } from "@/lib/agentic/api";
import { accent, accentBg, accentHover } from "../buildablesTheme";

type ScriptRow = {
  script_id: string;
  test_id?: string;
  template_id?: string;
  created_at?: string;
  script_path?: string;
};

type Props = {
  projectId: string | null;
  onView?: (scriptId: string) => void;
  onLog?: (msg: string) => void;
};

export function GeneratedScriptsList({ projectId, onView, onLog }: Props) {
  const [scripts, setScripts] = useState<ScriptRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!projectId) {
      setScripts([]);
      return;
    }
    setLoading(true);
    try {
      const res = await listGeneratedScripts(projectId);
      const rows = (res.scripts ?? []).map((s) => ({
        script_id: String(s.script_id ?? s.id ?? ""),
        test_id: s.test_id ? String(s.test_id) : undefined,
        template_id: s.template_id ? String(s.template_id) : undefined,
        created_at: s.created_at ? String(s.created_at) : undefined,
        script_path: s.script_path ? String(s.script_path) : undefined,
      }));
      setScripts(rows.filter((r) => r.script_id));
    } catch (err) {
      onLog?.(`[Scripts] ${err instanceof Error ? err.message : String(err)}`);
      setScripts([]);
    } finally {
      setLoading(false);
    }
  }, [projectId, onLog]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function onDelete(scriptId: string) {
    if (!projectId) return;
    setDeleting(scriptId);
    try {
      await deleteGeneratedScript(projectId, scriptId);
      onLog?.(`[Scripts] Deleted ${scriptId}`);
      await refresh();
    } catch (err) {
      onLog?.(`[Scripts][Delete] ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setDeleting(null);
    }
  }

  if (!projectId) return null;

  return (
    <div className="rounded border border-slate-200/80 bg-slate-50 p-2">
      <div className="flex items-center justify-between gap-2">
        <div className={`text-[10px] font-semibold ${accent}`}>Generated scripts</div>
        <button
          type="button"
          className="text-[9px] text-slate-600 hover:text-slate-800"
          disabled={loading}
          onClick={() => void refresh()}
        >
          Refresh
        </button>
      </div>
      {loading && scripts.length === 0 ? (
        <p className="mt-1 text-[9px] text-slate-500">Loading…</p>
      ) : scripts.length === 0 ? (
        <p className="mt-1 text-[9px] text-slate-500">No scripts yet — configure a test and generate.</p>
      ) : (
        <ul className="mt-2 max-h-28 space-y-1 overflow-auto">
          {scripts.map((s) => (
            <li
              key={s.script_id}
              className="flex items-center justify-between gap-2 rounded border border-slate-200/60 bg-white/50 px-2 py-1"
            >
              <div className="min-w-0 text-[9px] text-slate-700">
                <div className="truncate font-mono">{s.script_id}</div>
                <div className="text-slate-500">
                  {s.test_id ?? "—"} · {s.template_id ?? "template"}
                </div>
              </div>
              <div className="flex shrink-0 gap-1">
                {onView ? (
                  <button
                    type="button"
                    className={`rounded px-1.5 py-0.5 text-[9px] text-white ${accentBg} ${accentHover}`}
                    onClick={() => onView(s.script_id)}
                  >
                    View
                  </button>
                ) : null}
                <button
                  type="button"
                  disabled={deleting === s.script_id}
                  className="rounded border border-slate-300 px-1.5 py-0.5 text-[9px] text-slate-700 hover:bg-slate-100 disabled:opacity-40"
                  onClick={() => void onDelete(s.script_id)}
                >
                  {deleting === s.script_id ? "…" : "Delete"}
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
