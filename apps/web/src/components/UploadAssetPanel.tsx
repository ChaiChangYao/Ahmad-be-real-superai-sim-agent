"use client";

import { useState } from "react";
import type { JointGuess } from "@/lib/jointGuesses";
import { useSimStore } from "@/lib/state";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export function UploadAssetPanel() {
  const [message, setMessage] = useState("No file selected.");
  const [autoGuessNotice, setAutoGuessNotice] = useState("");
  const projectId = useSimStore((s) => s.selectedProjectId);
  const pending = useSimStore((s) => s.pendingJointGuesses);
  const setPendingJointGuesses = useSimStore((s) => s.setPendingJointGuesses);

  return (
    <div className="panel p-2">
      <h3 className="mb-2 text-sm font-semibold">Upload Asset</h3>
      <input
        type="file"
        onChange={(e) => {
          const file = e.target.files?.[0];
          setMessage(file ? `Ready to upload: ${file.name}` : "No file selected.");
        }}
      />
      <div className="mt-1 text-xs text-textMuted">{message}</div>
      <p className="mt-1 text-[10px] text-textMuted">
        STEP conversion requires a local converter. Default robot dog demo runs without uploads.
      </p>
      <div className="mt-2 flex gap-2">
        <button
          className="rounded border border-border bg-white px-2 py-1 text-xs"
          onClick={async () => {
            try {
              const res = await fetch(`${API_BASE}/projects/${projectId}/cad/auto-guess-joints`, { method: "POST" });
              if (!res.ok) throw new Error(`Auto-guess failed: ${res.status}`);
              const data = await res.json();
              const guesses = (data.guesses ?? []) as JointGuess[];
              setPendingJointGuesses(guesses);
              setAutoGuessNotice(
                guesses.length
                  ? `${guesses.length} joint guess(es). Review in Joint Settings — Accept, Edit, or Reject.`
                  : "No joint guesses met confidence threshold."
              );
            } catch (err) {
              setAutoGuessNotice(err instanceof Error ? err.message : "Auto-guess failed.");
            }
          }}
        >
          Auto Guess Joints
        </button>
        <button className="rounded border border-border bg-white px-2 py-1 text-xs" type="button" disabled title="Use CAD import API after uploading meshes">
          Generate Collision Primitives
        </button>
      </div>
      {autoGuessNotice ? <div className="mt-1 text-xs text-textMuted">{autoGuessNotice}</div> : null}
      {pending.length > 0 ? (
        <div className="mt-2 max-h-24 overflow-auto rounded border border-border bg-white p-1 text-xs">
          {pending.map((g) => (
            <div key={g.id}>
              {g.parent_link_id} → {g.child_link_id} ({g.confidence}) — {g.reasons[0]}
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
