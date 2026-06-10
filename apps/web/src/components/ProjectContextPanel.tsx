"use client";

import { useSimStore } from "@/lib/state";

export function ProjectContextPanel() {
  const manifest = useSimStore((s) => s.manifest);
  const projectId = useSimStore((s) => s.selectedProjectId);
  const lastSavedAt = useSimStore((s) => s.lastSavedAt);
  const dirty = useSimStore((s) => s.dirty);
  const lastRunManifestVersion = useSimStore((s) => s.lastRunManifestVersion);
  const manifestVersion = manifest?.version ?? null;
  const manifestStaleForRun =
    lastRunManifestVersion !== null && manifestVersion !== null && manifestVersion !== lastRunManifestVersion;

  if (!manifest) {
    return <div className="border-b border-border px-2 py-2 text-xs text-textMuted">No project loaded</div>;
  }

  const mode = manifest.project_mode === "imported_project" ? "Imported Project" : "Default Demo";
  const descFormat = manifest.robot_description?.preferred_format?.toUpperCase() ?? "Procedural";
  const descSource =
    manifest.project_mode === "imported_project"
      ? manifest.robot_description?.urdf_path || manifest.robot_description?.mjcf_path
        ? "Imported"
        : "Procedural fallback"
      : manifest.robot_description?.urdf_path
        ? "URDF"
        : "Procedural";

  return (
    <div className="border-b border-border bg-white px-2 py-2 text-[11px] text-textMain">
      <div className="font-medium">{manifest.project_name}</div>
      <div className="mt-1 grid grid-cols-[auto_1fr] gap-x-2 gap-y-0.5">
        <span className="text-textMuted">Mode</span>
        <span>{mode}</span>
        <span className="text-textMuted">Type</span>
        <span>{manifest.project_type ?? "generic"}</span>
        <span className="text-textMuted">Source</span>
        <span>
          {descSource} ({descFormat})
        </span>
        <span className="text-textMuted">ID</span>
        <span className="truncate font-mono text-[10px]">{projectId}</span>
        <span className="text-textMuted">Manifest</span>
        <span>
          {dirty ? "Unsaved edits" : manifestStaleForRun ? "Changed since last run" : `Saved ${lastSavedAt ? new Date(lastSavedAt).toLocaleTimeString() : ""}`}
        </span>
        {manifestVersion ? (
          <>
            <span className="text-textMuted">Version</span>
            <span>v{manifestVersion}{lastRunManifestVersion ? ` · last run v${lastRunManifestVersion}` : ""}</span>
          </>
        ) : null}
      </div>
    </div>
  );
}
