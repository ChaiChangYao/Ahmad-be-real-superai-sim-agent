"use client";

import { ChangeEvent } from "react";
import { useSimStore } from "@/lib/state";
import { getRunResult, runSelectedTest } from "@/lib/api";

function Field({ label, value }: { label: string; value: string | number | boolean }) {
  return (
    <div className="grid grid-cols-[90px_1fr] gap-1 border-b border-border py-1 text-[11px]">
      <span className="text-textMuted">{label}</span>
      <span className="truncate text-textMain">{String(value)}</span>
    </div>
  );
}

export function InspectorPanel() {
  const selectedPartId = useSimStore((s) => s.selectedPartId);
  const selectedTestId = useSimStore((s) => s.selectedTestId);
  const manifest = useSimStore((s) => s.manifest);
  const projectId = useSimStore((s) => s.selectedProjectId);
  const testsCatalog = useSimStore((s) => s.testsCatalog);
  const patchManifest = useSimStore((s) => s.patchManifest);
  const setRunResult = useSimStore((s) => s.setRunResult);
  const addLog = useSimStore((s) => s.addLog);

  function updateNumber(value: string, fallback = 0) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  }

  const selectedLink = selectedPartId?.startsWith("link:") ? manifest?.links.find((l) => l.id === selectedPartId.replace("link:", "")) : null;
  const selectedJoint = selectedPartId?.startsWith("joint:") ? manifest?.joints.find((j) => j.id === selectedPartId.replace("joint:", "")) : null;
  const selectedActuator = selectedPartId?.startsWith("actuator:") ? manifest?.actuators.find((a) => a.id === selectedPartId.replace("actuator:", "")) : null;
  const selectedSensor = selectedPartId?.startsWith("sensor:") ? manifest?.sensors.find((s) => s.id === selectedPartId.replace("sensor:", "")) : null;
  const selectedMaterial = selectedLink ? manifest?.materials.find((m) => m.id === selectedLink.material_id) : null;
  const selectedTest = selectedTestId ? testsCatalog.find((t) => t.id === selectedTestId) : null;

  async function runSelectedTestFromInspector() {
    if (!selectedTestId) return;
    try {
      const result = await runSelectedTest(projectId, selectedTestId);
      const run = await getRunResult(result.run_id);
      setRunResult(run);
      addLog(`[Inspector] ${result.test_name} → ${result.status}`);
    } catch (error) {
      addLog(`[Inspector][Error] ${(error as Error).message}`);
    }
  }

  return (
    <div className="flex h-full min-h-0 flex-col overflow-auto bg-white text-textMain">
      <div className="border-b border-border px-2 py-2 text-xs font-semibold">Inspector</div>

      <div className="flex-1 overflow-auto px-2 py-1">
        {selectedLink ? (
          <>
            <Field label="Name" value={selectedLink.name ?? selectedLink.id} />
            <Field label="Type" value="link" />
            <Field label="Mass" value={`${selectedLink.mass_kg} kg`} />
            <Field label="Material" value={selectedMaterial?.name ?? selectedLink.material_id ?? "—"} />
            <label className="mt-2 block text-[11px]">
              <span className="text-textMuted">Mass (kg)</span>
              <input
                className="mt-0.5 w-full rounded border border-border bg-white px-2 py-1"
                type="number"
                step="0.01"
                value={selectedLink.mass_kg}
                onChange={(e: ChangeEvent<HTMLInputElement>) => {
                  const id = selectedLink.id;
                  patchManifest((m) => ({ ...m, links: m.links.map((link) => (link.id === id ? { ...link, mass_kg: updateNumber(e.target.value, link.mass_kg) } : link)) }));
                }}
              />
            </label>
          </>
        ) : null}

        {selectedJoint ? (
          <>
            <Field label="Name" value={selectedJoint.name ?? selectedJoint.id} />
            <Field label="Type" value={selectedJoint.type} />
            <Field label="Parent" value={selectedJoint.parent_link_id} />
            <Field label="Child" value={selectedJoint.child_link_id} />
            <Field label="Axis" value={`${selectedJoint.axis_xyz.x}, ${selectedJoint.axis_xyz.y}, ${selectedJoint.axis_xyz.z}`} />
            <Field label="Limits" value={`${selectedJoint.limit_lower_rad} … ${selectedJoint.limit_upper_rad}`} />
            <Field label="Damping" value={selectedJoint.damping} />
          </>
        ) : null}

        {selectedActuator ? (
          <>
            <Field label="Name" value={selectedActuator.name} />
            <Field label="Joint" value={selectedActuator.joint_id} />
            <Field label="Torque max" value={`${selectedActuator.max_torque_nm} Nm`} />
            <Field label="Velocity max" value={`${selectedActuator.max_velocity_rad_s} rad/s`} />
            <Field label="Control" value={selectedActuator.control_mode} />
          </>
        ) : null}

        {selectedSensor ? (
          <>
            <Field label="Name" value={selectedSensor.name ?? selectedSensor.id} />
            <Field label="Sensor" value={selectedSensor.sensor_type ?? selectedSensor.id} />
            <Field label="Position" value={`${selectedSensor.transform.position.x}, ${selectedSensor.transform.position.y}, ${selectedSensor.transform.position.z}`} />
          </>
        ) : null}

        {selectedTest ? (
          <>
            <Field label="Test" value={selectedTest.name} />
            <Field label="Category" value={selectedTest.category} />
            <Field label="Status" value={selectedTest.status ?? "unknown"} />
            <p className="mt-1 text-[10px] text-textMuted">{selectedTest.description}</p>
            <button type="button" className="mt-2 w-full rounded bg-accent py-1 text-xs text-white hover:bg-accent/90" onClick={() => void runSelectedTestFromInspector()}>
              Run Test
            </button>
          </>
        ) : null}

        {!selectedPartId && !selectedTest ? (
          <div className="space-y-1 py-2 text-[11px]">
            <Field label="Project" value={manifest?.project_name ?? "—"} />
            <Field label="Type" value={manifest?.project_type ?? "—"} />
            <Field label="Links" value={manifest?.links.length ?? 0} />
            <Field label="Joints" value={manifest?.joints.length ?? 0} />
            <p className="pt-2 text-textMuted">Select a link, joint, or test in the tree.</p>
          </div>
        ) : null}
      </div>
    </div>
  );
}
