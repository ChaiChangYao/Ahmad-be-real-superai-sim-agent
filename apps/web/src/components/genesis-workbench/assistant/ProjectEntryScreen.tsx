"use client";

import { accent } from "../buildablesTheme";
import { PillComposer } from "./PillComposer";

type Props = {
  goal: string;
  onGoalChange: (value: string) => void;
  pendingFiles: File[];
  onAddFiles: (files: File[]) => void;
  onRemoveFile: (index: number) => void;
  onSubmit: () => void;
  submitting?: boolean;
  projectName: string;
  onProjectNameChange: (name: string) => void;
};

export function ProjectEntryScreen({
  goal,
  onGoalChange,
  pendingFiles,
  onAddFiles,
  onRemoveFile,
  onSubmit,
  submitting,
  projectName,
  onProjectNameChange,
}: Props) {
  return (
    <div data-testid="project-entry-screen" className="flex h-full min-h-0 flex-col items-center justify-center px-6 py-8">
      <div className="mb-8 max-w-lg text-center">
        <h2 className={`text-lg font-semibold ${accent}`}>My Projects</h2>
        <p className="mt-2 text-sm text-slate-600">
          Upload your robot files, describe what you want to simulate, and the assistant will scan your project and
          recommend tests — no Genesis required for preflight.
        </p>
      </div>
      <label className="mb-4 w-full max-w-2xl text-left text-[10px] text-slate-500">
        Project name
        <input
          data-testid="project-name-input"
          className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900"
          value={projectName}
          disabled={submitting}
          onChange={(e) => onProjectNameChange(e.target.value)}
        />
      </label>
      <PillComposer
        value={goal}
        onChange={onGoalChange}
        pendingFiles={pendingFiles}
        onAddFiles={onAddFiles}
        onRemoveFile={onRemoveFile}
        onSubmit={onSubmit}
        disabled={submitting}
        placeholder='e.g. "Can I run gravity, joint sweep, and IMU on this robot?"'
      />
      {submitting ? (
        <p className="mt-4 text-xs text-slate-500">Importing files and running preflight…</p>
      ) : null}
    </div>
  );
}
