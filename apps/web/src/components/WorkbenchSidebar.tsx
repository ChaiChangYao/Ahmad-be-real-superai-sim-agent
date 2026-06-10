"use client";

import { useState } from "react";
import { useSimStore } from "@/lib/state";
import { GenesisTestLab } from "./GenesisTestLab";
import { GenesisShowcasePanel } from "./GenesisShowcasePanel";
import { ProjectTree } from "./ProjectTree";
import { ProjectContextPanel } from "./ProjectContextPanel";
import { ForcesLoadsPanel } from "./ForcesLoadsPanel";
import { JointControlsPanel } from "./simulation/JointControlsPanel";

type SidebarTab = "scene" | "entities" | "dofs" | "tests" | "showcase" | "forces" | "sensors" | "materials" | "render" | "import";
type BaseMode = "fixed_to_world" | "free_floating" | "ground_contact" | "anchored_mechanism";

const TABS: SidebarTab[] = ["scene", "entities", "dofs", "tests", "showcase", "forces", "sensors", "materials", "render", "import"];

const TAB_LABEL: Record<SidebarTab, string> = {
  scene: "Scene",
  entities: "Entities",
  dofs: "DOFs",
  tests: "Tests",
  showcase: "Showcase",
  forces: "Forces",
  sensors: "Sensors",
  materials: "Materials",
  render: "Render",
  import: "Import",
};

const tabBtn = (active: boolean) =>
  `rounded px-1.5 py-0.5 text-[10px] ${
    active ? "bg-accent text-white" : "text-textMuted hover:bg-slate-100 hover:text-textMain"
  }`;

const fieldSelect = "mt-0.5 w-full rounded border border-border bg-white px-2 py-1 text-textMain";

export function WorkbenchSidebar() {
  const [tab, setTab] = useState<SidebarTab>("scene");
  const [baseMode, setBaseMode] = useState<BaseMode>("free_floating");
  const manifest = useSimStore((s) => s.manifest);
  const controlMode = useSimStore((s) => s.controlMode);
  const setControlMode = useSimStore((s) => s.setControlMode);
  const setShowSkeleton = useSimStore((s) => s.setShowSkeleton);
  const showSkeleton = useSimStore((s) => s.showSkeleton);
  const projectType = manifest?.project_type ?? "generic";

  return (
    <div className="flex h-full min-h-0 flex-col text-textMain">
      <ProjectContextPanel />

      <div className="flex flex-wrap gap-0.5 border-b border-border bg-panel px-1 py-1">
        {TABS.map((item) => (
          <button key={item} type="button" className={tabBtn(tab === item)} onClick={() => setTab(item)}>
            {TAB_LABEL[item]}
          </button>
        ))}
      </div>

      <div className="min-h-0 flex-1 overflow-auto bg-white">
        {tab === "scene" ? (
          <div className="space-y-2 p-2 text-[11px]">
            <div className="text-xs font-semibold">Scene</div>
            <label className="block">
              <span className="text-textMuted">Base mode</span>
              <select className={fieldSelect} value={baseMode} onChange={(e) => setBaseMode(e.target.value as BaseMode)}>
                <option value="fixed_to_world">Fixed base</option>
                <option value="free_floating">Free base</option>
                <option value="ground_contact">Ground contact</option>
                <option value="anchored_mechanism">Anchored mechanism</option>
              </select>
            </label>
            <div className="grid grid-cols-2 gap-1 text-textMuted">
              <span>Gravity</span>
              <span>-9.81 m/s²</span>
              <span>Time step</span>
              <span>1/60 s</span>
              <span>Floor friction</span>
              <span>0.8</span>
            </div>
            {baseMode === "fixed_to_world" ? (
              <div className="rounded border border-amber-200 bg-amber-50 px-2 py-1 text-amber-900">
                Fixed base — robot will not topple under gravity.
              </div>
            ) : null}
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={showSkeleton} onChange={(e) => setShowSkeleton(e.target.checked)} />
              <span>Skeleton / joint axes overlay</span>
            </label>
          </div>
        ) : null}

        {tab === "entities" ? <ProjectTree /> : null}
        {tab === "dofs" ? (
          <div className="p-2">
            <div className="mb-1 text-xs font-semibold">DOFs / Joints</div>
            <JointControlsPanel />
          </div>
        ) : null}
        {tab === "forces" ? <ForcesLoadsPanel /> : null}
        {tab === "tests" ? <GenesisTestLab /> : null}
        {tab === "showcase" ? <GenesisShowcasePanel /> : null}

        {tab === "sensors" ? (
          <div className="p-2 text-[11px] text-textMuted">Sensor outputs appear in bottom drawer after a Genesis run.</div>
        ) : null}
        {tab === "materials" ? (
          <div className="p-2 text-[11px] text-textMuted">Select a link in the tree to edit material properties in the inspector.</div>
        ) : null}
        {tab === "render" ? (
          <div className="space-y-2 p-2 text-[11px]">
            <div className="text-xs font-semibold">Control</div>
            <label className="block">
              <span className="text-textMuted">Control mode</span>
              <select className={fieldSelect} value={controlMode} onChange={(e) => setControlMode(e.target.value as typeof controlMode)}>
                {projectType === "robot_dog" ? <option value="remote_control">Remote Control (WASD)</option> : null}
                <option value="joint_command_table">Joint Command Table</option>
                <option value="built_in_behavior">Built-in Behavior</option>
                <option value="control_script">Control Script</option>
                <option value="trajectory_test">Trajectory Test</option>
              </select>
            </label>
          </div>
        ) : null}
        {tab === "import" ? (
          <div className="space-y-1 p-2 text-[11px]">
            <div className="text-xs font-semibold">Imported Assets</div>
            {(manifest?.assets ?? []).map((asset) => (
              <div key={asset.id} className="rounded border border-border bg-panel px-2 py-1">
                <div className="font-medium">{asset.name}</div>
                <div className="text-textMuted">{asset.type}</div>
              </div>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}
