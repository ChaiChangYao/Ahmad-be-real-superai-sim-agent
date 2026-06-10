type ImportUserMessage = {
  severity?: string;
  issue?: string;
  fix?: string;
};

type MeshTableRow = {
  urdf_path?: string;
  resolved_local_path?: string;
  usage?: string;
  file_type?: string;
  status?: string;
  action_needed?: string;
};

type LaunchSummary = {
  urdfParsed?: boolean;
  links?: number;
  joints?: number;
  meshReferencesFound?: number;
  meshesFound?: number;
  meshesMissing?: number;
  unsupportedFormats?: number;
  stepUploaded?: boolean;
  launchable?: boolean;
  reason?: string | null;
  actions?: string[];
  autoMapLog?: string[];
};

export function importUserMessages(validation: Record<string, unknown> | null | undefined): ImportUserMessage[] {
  const raw = validation?.user_messages;
  if (!Array.isArray(raw)) return [];
  return raw.filter((item): item is ImportUserMessage => typeof item === "object" && item !== null);
}

function launchSummary(validation: Record<string, unknown>): LaunchSummary {
  const nested = validation.launch_summary as LaunchSummary | undefined;
  if (nested && typeof nested === "object") return nested;
  return {
    urdfParsed: Boolean((validation.robot_description as Record<string, unknown>)?.urdf_found),
    links: Number((validation.robot_description as Record<string, unknown>)?.links_count ?? 0),
    joints: Number((validation.robot_description as Record<string, unknown>)?.joints_count ?? 0),
    meshesMissing: ((validation.geometry as Record<string, unknown>)?.missing_mesh_references as string[] | undefined)?.length ?? 0,
    stepUploaded: Boolean((validation.geometry as Record<string, unknown>)?.step_source_found),
    launchable: false,
  };
}

function meshTable(validation: Record<string, unknown>): MeshTableRow[] {
  const geometry = (validation.geometry ?? {}) as Record<string, unknown>;
  const table = geometry.mesh_table;
  if (Array.isArray(table)) return table as MeshTableRow[];
  const refs = validation.meshReferences;
  if (Array.isArray(refs)) {
    return refs.map((row) => {
      const r = row as Record<string, unknown>;
      return {
        urdf_path: String(r.path ?? ""),
        resolved_local_path: String(r.resolvedPath ?? ""),
        usage: String(r.source ?? ""),
        file_type: String(r.fileType ?? ""),
        status: String(r.status ?? ""),
        action_needed: String(r.actionNeeded ?? ""),
      };
    });
  }
  return [];
}

function statusClass(status: string | undefined): string {
  if (status === "found" || status === "auto_mapped") return "text-[#c2410c]";
  if (status === "unsupported") return "text-amber-800";
  return "text-red-700";
}

export function ImportValidationSummary({ validation }: { validation: Record<string, unknown> | null }) {
  if (!validation) return null;

  const messages = importUserMessages(validation);
  const geometry = (validation.geometry ?? {}) as Record<string, unknown>;
  const summary = launchSummary(validation);
  const rows = meshTable(validation);
  const missingMeshes = (geometry.missing_mesh_references as string[] | undefined) ?? [];
  const autoMapLog = summary.autoMapLog ?? [];

  return (
    <div className="mt-3 space-y-3 rounded border border-slate-300 bg-slate-50 p-3 text-[10px]">
      <div className="font-semibold text-slate-900">Import validation (immediate — before launch)</div>

      <div className="grid gap-1 text-slate-600 sm:grid-cols-2">
        <div>URDF parsed: {summary.urdfParsed ? "yes" : "no"}</div>
        <div>Links: {String(summary.links ?? 0)} · Joints: {String(summary.joints ?? 0)}</div>
        <div>Mesh refs: {String(summary.meshReferencesFound ?? rows.length)}</div>
        <div>
          Meshes found: {String(summary.meshesFound ?? 0)} · Missing: {String(summary.meshesMissing ?? missingMeshes.length)}
        </div>
        <div>STEP uploaded: {summary.stepUploaded ? "yes" : "no"}</div>
        <div>Launchable: {summary.launchable ? "yes" : "no"}</div>
      </div>

      {summary.reason ? <div className="rounded border border-amber-500/40 bg-amber-50 px-2 py-1.5 text-amber-800">{summary.reason}</div> : null}

      {String(geometry.step_note ?? "") ? <div className="text-slate-500">{String(geometry.step_note)}</div> : null}

      {autoMapLog.length > 0 ? (
        <ul className="list-disc space-y-1 pl-4 text-sky-200">
          {autoMapLog.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      ) : null}

      {rows.length > 0 ? (
        <div className="max-h-48 overflow-auto rounded border border-slate-200">
          <table className="w-full text-left">
            <thead className="sticky top-0 bg-white text-slate-600">
              <tr>
                <th className="px-2 py-1">URDF mesh path</th>
                <th className="px-2 py-1">Usage</th>
                <th className="px-2 py-1">Type</th>
                <th className="px-2 py-1">Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.urdf_path} className="border-t border-slate-200">
                  <td className="px-2 py-1 font-mono text-[9px] text-slate-700">{row.urdf_path}</td>
                  <td className="px-2 py-1">{row.usage}</td>
                  <td className="px-2 py-1">{row.file_type}</td>
                  <td className={`px-2 py-1 ${statusClass(row.status)}`}>{row.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {messages.length > 0 ? (
        <ul className="list-disc space-y-2 pl-4">
          {messages.slice(0, 8).map((msg, idx) => {
            const tone =
              msg.severity === "error" ? "text-red-700" : msg.severity === "warning" ? "text-amber-800" : "text-slate-700";
            return (
              <li key={`${msg.issue ?? "msg"}-${idx}`} className={tone}>
                <div className="font-medium">{msg.issue}</div>
                {msg.fix ? <div className="text-slate-600">{msg.fix}</div> : null}
              </li>
            );
          })}
        </ul>
      ) : summary.launchable ? (
        <div className="text-[#c2410c]">All URDF mesh references resolved. Full launch is enabled.</div>
      ) : null}
    </div>
  );
}
