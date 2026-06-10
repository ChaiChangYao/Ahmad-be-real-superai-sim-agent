"use client";

import { useState } from "react";
import { runScenario, saveManifest, startInteractive, stopInteractive, validateManifest } from "@/lib/api";
import { useSimStore } from "@/lib/state";
import { keyboardHelp } from "@/lib/keyboardControls";

export function RunControls() {
  const projectId = useSimStore((s) => s.selectedProjectId);
  const scenarioId = useSimStore((s) => s.selectedScenarioId);
  const manifest = useSimStore((s) => s.manifest);
  const dirty = useSimStore((s) => s.dirty);
  const setInteractiveSessionId = useSimStore((s) => s.setInteractiveSessionId);
  const setRunResult = useSimStore((s) => s.setRunResult);
  const markSaved = useSimStore((s) => s.markSaved);
  const setValidationErrors = useSimStore((s) => s.setValidationErrors);
  const addLog = useSimStore((s) => s.addLog);
  const setupError = useSimStore((s) => s.setupError);
  const [running, setRunning] = useState(false);

  async function onRun() {
    setRunning(true);
    try {
      if (!manifest) {
        throw new Error("No manifest loaded.");
      }
      if (dirty) {
        const saved = await saveManifest(projectId, manifest);
        markSaved(saved.manifest ?? { ...manifest, version: (manifest.version ?? 0) + 1, updated_at: new Date().toISOString() });
      }
      const validation = await validateManifest(projectId);
      setValidationErrors(validation.errors);
      if (!validation.valid) {
        throw new Error(validation.errors.join("; "));
      }
      const result = await runScenario(projectId, scenarioId);
      setRunResult(result);
    } catch (error) {
      addLog(`[Error] ${(error as Error).message}`);
    } finally {
      setRunning(false);
    }
  }

  async function onStartInteractive() {
    const session = await startInteractive(projectId);
    setInteractiveSessionId(session.session_id);
    addLog("[Interactive] Started. Use WASD / Space / R.");
  }

  async function onStopInteractive() {
    await stopInteractive(projectId);
    setInteractiveSessionId(null);
    addLog("[Interactive] Stopped.");
  }

  return (
    <div className="flex items-center gap-2 text-xs">
      <button className="rounded bg-accent px-2.5 py-1 text-white disabled:opacity-50" onClick={onRun} disabled={running || Boolean(setupError)}>
        {running ? "Running..." : "Run Simulation"}
      </button>
      <button className="rounded border border-border bg-white px-2.5 py-1 disabled:opacity-50" onClick={onStartInteractive} disabled={Boolean(setupError)}>
        Start Interactive (WASD)
      </button>
      <button className="rounded border border-border bg-white px-2.5 py-1" onClick={onStopInteractive}>
        Stop Interactive
      </button>
      <div className="text-textMuted">{keyboardHelp.join(" | ")} | Active command: {useSimStore.getState().currentCommand}</div>
    </div>
  );
}
