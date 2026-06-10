"use client";

import { accentMuted } from "../buildablesTheme";

type Props = {
  files: File[];
  onRemove: (index: number) => void;
};

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function AttachmentTray({ files, onRemove }: Props) {
  if (files.length === 0) return null;

  return (
    <div data-testid="attachment-tray" className="flex flex-wrap gap-1.5 px-1 pb-2">
      {files.map((file, index) => (
        <span
          key={`${file.name}-${file.size}-${index}`}
          className="inline-flex max-w-full items-center gap-1 rounded-full border border-slate-300 bg-slate-100 px-2 py-0.5 text-[10px] text-slate-800"
        >
          <span className={`truncate ${accentMuted}`} title={file.name}>
            {file.name}
          </span>
          <span className="shrink-0 text-[9px] text-slate-500">{formatSize(file.size)}</span>
          <button
            type="button"
            className="shrink-0 rounded-full px-1 text-slate-600 hover:bg-slate-200 hover:text-slate-900"
            aria-label={`Remove ${file.name}`}
            onClick={() => onRemove(index)}
          >
            ×
          </button>
        </span>
      ))}
    </div>
  );
}
