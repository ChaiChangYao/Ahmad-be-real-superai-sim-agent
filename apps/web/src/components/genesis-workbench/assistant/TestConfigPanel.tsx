import type { ProjectInspectionReport, SimulationTestSpec, TestReadinessResult } from "@/lib/agentic/types";
import { testCardStatus } from "@/lib/agentic/types";
import { accent, accentBg, accentHover } from "../buildablesTheme";

export type TestConfigValues = {
  fallback_mode: string;
  attach_link: string;
  sample_rate: number;
  duration_seconds: number;
  contact_links: string;
  depth_width: number;
  depth_height: number;
  depth_fov: number;
  thermal_grid_resolution: number;
};

type Props = {
  testId: string;
  spec?: SimulationTestSpec;
  readiness?: TestReadinessResult;
  inspection?: ProjectInspectionReport | null;
  values: TestConfigValues;
  onChange: (values: TestConfigValues) => void;
  onGenerate: () => void;
  generating?: boolean;
};

const DEFAULT_VALUES: TestConfigValues = {
  fallback_mode: "",
  attach_link: "",
  sample_rate: 100,
  duration_seconds: 4,
  contact_links: "",
  depth_width: 640,
  depth_height: 480,
  depth_fov: 60,
  thermal_grid_resolution: 16,
};

export function defaultTestConfig(): TestConfigValues {
  return { ...DEFAULT_VALUES };
}

export function TestConfigPanel({
  testId,
  spec,
  readiness,
  inspection,
  values,
  onChange,
  onGenerate,
  generating,
}: Props) {
  const status = readiness ? testCardStatus(readiness) : null;
  const linkNames = inspection?.robot_descriptions?.[0]?.link_names ?? [];
  const canGenerate = Boolean(
    !readiness ||
      readiness.can_run ||
      readiness.can_run_with_fallback ||
      values.fallback_mode !== "",
  );

  function set<K extends keyof TestConfigValues>(key: K, val: TestConfigValues[K]) {
    onChange({ ...values, [key]: val });
  }

  return (
    <div data-testid="test-config-panel" className="rounded border border-slate-200 bg-slate-50 p-2">
      <div className="text-xs font-semibold text-slate-800">
        Configure: {spec?.display_name ?? testId}
      </div>
      <p className="mt-0.5 text-[9px] text-slate-500">{spec?.description}</p>

      {(status === "ready_with_fallback" ||
        status === "needs_user_choice" ||
        (readiness?.fallback_modes?.length ?? 0) > 0) && (
        <label className="mt-2 block text-[9px] text-slate-600">
          Fallback mode
          <select
            className="mt-0.5 w-full rounded border border-slate-300 bg-white px-1.5 py-1 text-[10px] text-slate-800"
            value={values.fallback_mode}
            onChange={(e) => set("fallback_mode", e.target.value)}
          >
            <option value="">None (full visual)</option>
            <option value="skeleton">Skeleton (missing meshes)</option>
            <option value="static_mesh">Static mesh only</option>
          </select>
        </label>
      )}

      {testId === "imu_sensor" && linkNames.length > 0 && (
        <label className="mt-2 block text-[9px] text-slate-600">
          IMU attach link
          <select
            className="mt-0.5 w-full rounded border border-slate-300 bg-white px-1.5 py-1 text-[10px] text-slate-800"
            value={values.attach_link || linkNames[0]}
            onChange={(e) => set("attach_link", e.target.value)}
          >
            {linkNames.map((l) => (
              <option key={l} value={l}>
                {l}
              </option>
            ))}
          </select>
        </label>
      )}

      {testId === "contact_force" && linkNames.length > 0 && (
        <label className="mt-2 block text-[9px] text-slate-600">
          Contact links (comma-separated)
          <input
            type="text"
            placeholder={linkNames.slice(0, 3).join(", ")}
            className="mt-0.5 w-full rounded border border-slate-300 bg-white px-1.5 py-1 text-[10px] text-slate-800"
            value={values.contact_links}
            onChange={(e) => set("contact_links", e.target.value)}
          />
        </label>
      )}

      {testId === "depth_camera" && (
        <>
          <label className="mt-2 block text-[9px] text-slate-600">
            Resolution (width × height)
            <div className="mt-0.5 flex gap-1">
              <input
                type="number"
                min={64}
                max={1920}
                className="w-1/2 rounded border border-slate-300 bg-white px-1.5 py-1 text-[10px] text-slate-800"
                value={values.depth_width}
                onChange={(e) => set("depth_width", Number(e.target.value))}
              />
              <input
                type="number"
                min={64}
                max={1080}
                className="w-1/2 rounded border border-slate-300 bg-white px-1.5 py-1 text-[10px] text-slate-800"
                value={values.depth_height}
                onChange={(e) => set("depth_height", Number(e.target.value))}
              />
            </div>
          </label>
          <label className="mt-2 block text-[9px] text-slate-600">
            Field of view (degrees)
            <input
              type="number"
              min={30}
              max={120}
              className="mt-0.5 w-full rounded border border-slate-300 bg-white px-1.5 py-1 text-[10px] text-slate-800"
              value={values.depth_fov}
              onChange={(e) => set("depth_fov", Number(e.target.value))}
            />
          </label>
        </>
      )}

      {testId === "thermal_grid_readiness" && (
        <label className="mt-2 block text-[9px] text-slate-600">
          Grid resolution
          <input
            type="number"
            min={4}
            max={64}
            className="mt-0.5 w-full rounded border border-slate-300 bg-white px-1.5 py-1 text-[10px] text-slate-800"
            value={values.thermal_grid_resolution}
            onChange={(e) => set("thermal_grid_resolution", Number(e.target.value))}
          />
        </label>
      )}

      {testId === "imu_sensor" && (
        <label className="mt-2 block text-[9px] text-slate-600">
          Sample rate (Hz)
          <input
            type="number"
            min={1}
            max={1000}
            className="mt-0.5 w-full rounded border border-slate-300 bg-white px-1.5 py-1 text-[10px] text-slate-800"
            value={values.sample_rate}
            onChange={(e) => set("sample_rate", Number(e.target.value))}
          />
        </label>
      )}

      <label className="mt-2 block text-[9px] text-slate-600">
        Duration (seconds)
        <input
          type="number"
          min={0.5}
          max={60}
          step={0.5}
          className="mt-0.5 w-full rounded border border-slate-300 bg-white px-1.5 py-1 text-[10px] text-slate-800"
          value={values.duration_seconds}
          onChange={(e) => set("duration_seconds", Number(e.target.value))}
        />
      </label>

      {readiness?.warnings?.length ? (
        <ul className="mt-2 list-inside list-disc text-[9px] text-amber-400/90">
          {readiness.warnings.slice(0, 3).map((w) => (
            <li key={w}>{w}</li>
          ))}
        </ul>
      ) : null}

      <button
        type="button"
        data-testid="generate-script-button"
        disabled={!canGenerate || generating}
        className={`mt-3 w-full rounded px-2 py-1.5 text-[10px] font-medium text-white ${accentBg} ${accentHover} disabled:opacity-40`}
        onClick={onGenerate}
      >
        {generating ? "Generating…" : "Generate Genesis Script"}
      </button>
      {!canGenerate && readiness ? (
        <p className="mt-1 text-[9px] text-red-400">
          {readiness.blockers[0] ?? "Test blocked — upload assets or choose a fallback mode above."}
        </p>
      ) : null}
    </div>
  );
}
