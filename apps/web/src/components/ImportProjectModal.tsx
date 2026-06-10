"use client";

import { useEffect, useMemo, useState } from "react";
import { activateProject, getManifest, getProjectTestsAvailable, getProjectTestsCatalog, importProject, listScenarios } from "@/lib/api";
import { useSimStore } from "@/lib/state";
import { ImportValidationSummary } from "@/components/genesis-workbench/ImportValidationSummary";

type ImportProjectModalProps = {
  open?: boolean;
  onClose?: () => void;
};

const MOTION_ACCEPT = ".urdf,.xml,.mjcf,.xacro,.py,.yaml,.yml,.json,.zip";
const MODEL_ACCEPT = ".step,.stp,.stl,.obj,.glb,.gltf,.dae,.mtl,.png,.jpg,.jpeg,.zip";

function mergeFiles(motion: File[], model: File[]): File[] {
  const seen = new Set<string>();
  const out: File[] = [];
  for (const file of [...motion, ...model]) {
    const key = `${file.name}:${file.size}`;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(file);
  }
  return out;
}

function FileDropZone({
  title,
  hint,
  accept,
  files,
  onChange,
}: {
  title: string;
  hint: string;
  accept: string;
  files: File[];
  onChange: (files: File[]) => void;
}) {
  return (
    <div className="rounded border border-dashed border-slate-500 bg-slate-50 p-3">
      <div className="mb-1 text-[11px] font-semibold text-slate-900">{title}</div>
      <div className="mb-2 text-[10px] text-slate-600">{hint}</div>
      <input
        type="file"
        multiple
        accept={accept}
        className="mb-2 block w-full text-[10px] file:mr-2 file:rounded file:border-0 file:bg-sky-700 file:px-2 file:py-1 file:text-[10px] file:text-white"
        onChange={(e) => onChange(Array.from(e.target.files ?? []))}
      />
      <div className="max-h-16 overflow-auto rounded border border-slate-200 bg-white p-2 text-[10px]">
        {files.length === 0 ? <div className="text-slate-500">No files yet</div> : files.map((f) => <div key={`${f.name}-${f.size}`}>{f.name}</div>)}
      </div>
    </div>
  );
}

export function ImportProjectModal({ open: controlledOpen, onClose }: ImportProjectModalProps = {}) {
  const [internalOpen, setInternalOpen] = useState(false);
  const open = controlledOpen ?? internalOpen;
  const [projectName, setProjectName] = useState("Imported Project");
  const [importMode, setImportMode] = useState<"robot_mechanism" | "cad_geometry_only" | "buildables_package">("robot_mechanism");
  const [motionFiles, setMotionFiles] = useState<File[]>([]);
  const [modelFiles, setModelFiles] = useState<File[]>([]);
  const [validation, setValidation] = useState<Record<string, unknown> | null>(null);
  const [importedProjectId, setImportedProjectId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const addLog = useSimStore((s) => s.addLog);
  const setSelectedProjectId = useSimStore((s) => s.setSelectedProjectId);
  const setSelectedPartId = useSimStore((s) => s.setSelectedPartId);
  const setManifest = useSimStore((s) => s.setManifest);
  const setSelectedScenarioId = useSimStore((s) => s.setSelectedScenarioId);
  const setTestsCatalog = useSimStore((s) => s.setTestsCatalog);
  const setAvailableTests = useSimStore((s) => s.setAvailableTests);

  const files = useMemo(() => mergeFiles(motionFiles, modelFiles), [motionFiles, modelFiles]);
  const hasMainRobotFile = motionFiles.some((file) => [".urdf", ".xml", ".mjcf", ".xacro"].some((ext) => file.name.toLowerCase().endsWith(ext)));
  const importDisabled = loading || files.length === 0 || (importMode === "robot_mechanism" && !hasMainRobotFile);

  function closeModal() {
    if (onClose) onClose();
    else setInternalOpen(false);
  }

  useEffect(() => {
    if (!open) return;
    setValidation(null);
    setImportedProjectId(null);
    setMotionFiles([]);
    setModelFiles([]);
  }, [open]);

  async function onImport() {
    try {
      setLoading(true);
      const result = await importProject(files, { projectName, importMode });
      setValidation((result.import_validation as Record<string, unknown>) ?? null);
      const pid = String(result.project_id);
      setImportedProjectId(pid);
      addLog(`[Import] Project imported: ${pid}`);
    } catch (error) {
      addLog(`[Import][Error] ${(error as Error).message}`);
    } finally {
      setLoading(false);
    }
  }

  async function onLoadImported() {
    if (!importedProjectId) return;
    try {
      setLoading(true);
      await activateProject(importedProjectId);
      setSelectedProjectId(importedProjectId);
      setSelectedPartId(null);
      const manifest = await getManifest(importedProjectId);
      setManifest(manifest);
      const scenarios = await listScenarios(importedProjectId);
      if (scenarios.length > 0) setSelectedScenarioId(scenarios[0].id);
      const testsCatalog = await getProjectTestsCatalog(importedProjectId);
      const available = await getProjectTestsAvailable(importedProjectId);
      setTestsCatalog(testsCatalog.tests);
      setAvailableTests(available.tests);
      addLog(`[Import] Active project: ${importedProjectId}`);
      closeModal();
    } catch (error) {
      addLog(`[Import][Error] ${(error as Error).message}`);
    } finally {
      setLoading(false);
    }
  }

  if (!open) {
    if (controlledOpen === undefined) {
      return (
        <button type="button" className="rounded border border-slate-300 px-2 py-1 text-xs" onClick={() => setInternalOpen(true)}>
          Import Project
        </button>
      );
    }
    return null;
  }

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 p-4">
      <div className="max-h-[90vh] w-full max-w-2xl overflow-auto rounded-lg border border-slate-300 bg-[#1e2838] p-4 text-xs text-slate-800 shadow-2xl">
        <div className="mb-3 flex items-center justify-between">
          <div>
            <div className="font-semibold text-slate-900">Import Custom Robot</div>
            <div className="mt-0.5 text-[10px] text-slate-600">Upload motion files and visual/collision model files separately.</div>
          </div>
          <button type="button" className="text-slate-600 hover:text-slate-800" onClick={closeModal}>
            ✕
          </button>
        </div>

        <label className="mb-3 block">
          Project Name
          <input className="mt-1 w-full rounded border border-slate-300 bg-slate-50 px-2 py-1" value={projectName} onChange={(e) => setProjectName(e.target.value)} />
        </label>

        <label className="mb-3 block">
          Import Mode
          <select className="mt-1 w-full rounded border border-slate-300 bg-slate-50 px-2 py-1" value={importMode} onChange={(e) => setImportMode(e.target.value as typeof importMode)}>
            <option value="robot_mechanism">Robot / mechanism project</option>
            <option value="cad_geometry_only">CAD geometry only</option>
            <option value="buildables_package">Existing Buildables physics package</option>
          </select>
        </label>

        <div className="mb-3 grid gap-3 md:grid-cols-2">
          <FileDropZone
            title="1) Robot motion (required for simulation)"
            hint="URDF or MJCF with joints, limits, and actuators. Optional: control script (.py), manifest (.json)."
            accept={MOTION_ACCEPT}
            files={motionFiles}
            onChange={setMotionFiles}
          />
          <FileDropZone
            title="2) Robot model / visuals (optional but recommended)"
            hint="STEP/STL/OBJ/GLB meshes and textures. Put mesh files in a meshes/ folder when zipping, or upload all STLs here."
            accept={MODEL_ACCEPT}
            files={modelFiles}
            onChange={setModelFiles}
          />
        </div>

        {importMode === "robot_mechanism" && !hasMainRobotFile ? (
          <div className="mb-3 rounded border border-amber-500/40 bg-amber-50 px-2 py-1.5 text-amber-800">
            Box 1 needs at least one URDF or MJCF file so Genesis can move the robot.
          </div>
        ) : null}

        <div className="flex flex-wrap gap-2">
          <button type="button" className="rounded bg-sky-600 px-3 py-1 text-white disabled:opacity-50" onClick={() => void onImport()} disabled={importDisabled}>
            {loading ? "Importing…" : "Import"}
          </button>
          <button type="button" className="rounded border border-slate-300 px-3 py-1 disabled:opacity-50" onClick={() => void onLoadImported()} disabled={!importedProjectId || loading}>
            Load Imported Project
          </button>
        </div>

        {validation ? <ImportValidationSummary validation={validation} /> : null}
      </div>
    </div>
  );
}
