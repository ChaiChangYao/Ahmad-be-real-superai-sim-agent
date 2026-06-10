import type { MeshReference } from "@/lib/agentic/types";
import { accentMuted } from "../buildablesTheme";

type Props = { meshes: MeshReference[]; maxRows?: number };

export function MissingMeshTable({ meshes, maxRows = 30 }: Props) {
  if (meshes.length === 0) return null;
  const rows = meshes.slice(0, maxRows);
  return (
    <div data-testid="missing-mesh-table" className="overflow-x-auto">
      <table className="w-full text-left text-[9px]">
        <thead>
          <tr className={`border-b border-slate-200 ${accentMuted}`}>
            <th className="py-1 pr-2 font-semibold">URDF path</th>
            <th className="py-1 pr-2 font-semibold">Usage</th>
            <th className="py-1 pr-2 font-semibold">Status</th>
            <th className="py-1 font-semibold">Action</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((m) => (
            <tr key={m.raw_path} className="border-b border-slate-200/80 text-slate-700">
              <td className="py-1 pr-2 font-mono text-red-200">{m.raw_path}</td>
              <td className="py-1 pr-2 text-slate-600">{m.usage}</td>
              <td className="py-1 pr-2 text-amber-800">{m.status}</td>
              <td className="py-1 text-slate-500">{m.action_needed || "Upload mesh"}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {meshes.length > maxRows ? (
        <div className="mt-1 text-[9px] text-slate-500">…and {meshes.length - maxRows} more</div>
      ) : null}
    </div>
  );
}
