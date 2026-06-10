"use client";

import { useState } from "react";
import { guessToManifestJoint, type JointGuess } from "@/lib/jointGuesses";
import { saveManifest } from "@/lib/api";
import { useSimStore } from "@/lib/state";
import type { ManifestState } from "@/lib/types";
import type { BuildablesJoint } from "@schemas/types";

function guessDraft(guess: JointGuess) {
  return guessToManifestJoint(guess);
}

export function JointEditor() {
  const manifest = useSimStore((s) => s.manifest);
  const projectId = useSimStore((s) => s.selectedProjectId);
  const pending = useSimStore((s) => s.pendingJointGuesses);
  const patchManifest = useSimStore((s) => s.patchManifest);
  const markSaved = useSimStore((s) => s.markSaved);
  const removePending = useSimStore((s) => s.removePendingJointGuess);
  const [editingGuessId, setEditingGuessId] = useState<string | null>(null);
  const [draft, setDraft] = useState<BuildablesJoint | null>(null);
  const [status, setStatus] = useState("");

  if (!manifest) {
    return (
      <section className="panel p-2">
        <h3 className="mb-2 text-sm font-semibold">Joint Settings</h3>
        <div className="text-xs text-textMuted">Load a project to edit joints.</div>
      </section>
    );
  }

  async function persistManifest(nextManifest: ManifestState) {
    const saved = await saveManifest(projectId, nextManifest);
    if (saved.manifest) markSaved(saved.manifest);
    setStatus("Manifest saved.");
  }

  function startEditGuess(guess: JointGuess) {
    setEditingGuessId(guess.id);
    setDraft(guessDraft(guess));
  }

  async function acceptGuess(guess: JointGuess, joint: BuildablesJoint) {
    patchManifest((m) => ({
      ...m,
      joints: [...m.joints.filter((j) => j.id !== joint.id), joint]
    }));
    removePending(guess.id);
    setEditingGuessId(null);
    setDraft(null);
    const next = useSimStore.getState().manifest;
    if (next) await persistManifest(next);
  }

  return (
    <section className="panel p-2">
      <h3 className="mb-2 text-sm font-semibold">Joint Settings</h3>
      {status ? <div className="mb-1 text-xs text-textMuted">{status}</div> : null}

      {pending.length > 0 ? (
        <div className="mb-2 space-y-1 border-b border-border pb-2">
          <div className="text-xs font-medium">Pending auto-guesses ({pending.length})</div>
          {pending.map((guess) => (
            <div key={guess.id} className="rounded border border-border bg-white p-1 text-[10px]">
              <div>
                {guess.parent_link_id} → {guess.child_link_id} ({Math.round(guess.confidence * 100)}%)
              </div>
              <div className="text-textMuted">{guess.reasons[0]}</div>
              {editingGuessId === guess.id && draft ? (
                <div className="mt-1 grid grid-cols-2 gap-1">
                  <input
                    className="border border-border rounded px-1"
                    value={draft.id}
                    onChange={(e) => setDraft({ ...draft, id: e.target.value })}
                    placeholder="Joint ID"
                  />
                  <input
                    className="border border-border rounded px-1"
                    value={draft.limit_lower_rad}
                    onChange={(e) => setDraft({ ...draft, limit_lower_rad: Number(e.target.value) })}
                    placeholder="Lower limit"
                  />
                  <input
                    className="border border-border rounded px-1"
                    value={draft.limit_upper_rad}
                    onChange={(e) => setDraft({ ...draft, limit_upper_rad: Number(e.target.value) })}
                    placeholder="Upper limit"
                  />
                </div>
              ) : null}
              <div className="mt-1 flex gap-1">
                <button
                  type="button"
                  className="rounded border border-border px-1"
                  onClick={() => acceptGuess(guess, draft && editingGuessId === guess.id ? draft : guessDraft(guess))}
                >
                  Accept
                </button>
                <button type="button" className="rounded border border-border px-1" onClick={() => startEditGuess(guess)}>
                  Edit
                </button>
                <button type="button" className="rounded border border-border px-1" onClick={() => removePending(guess.id)}>
                  Reject
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : null}

      <div className="max-h-40 space-y-1 overflow-auto text-xs">
        {manifest.joints.slice(0, 12).map((joint) => (
          <div key={joint.id} className="rounded border border-border bg-white px-1 py-0.5">
            <span className="font-medium">{joint.id}</span> · {joint.parent_link_id} → {joint.child_link_id}
            {joint.auto_detected ? <span className="text-amber-700"> (auto)</span> : null}
          </div>
        ))}
        {manifest.joints.length > 12 ? <div className="text-textMuted">+{manifest.joints.length - 12} more joints</div> : null}
      </div>
    </section>
  );
}
