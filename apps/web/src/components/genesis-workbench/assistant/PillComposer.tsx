"use client";

import { useRef, type KeyboardEvent } from "react";
import { accentBg, accentHover, BUILDABLES_ORANGE } from "../buildablesTheme";
import { AttachmentTray } from "./AttachmentTray";

const FILE_ACCEPT =
  ".urdf,.xml,.mjcf,.xacro,.step,.stp,.stl,.obj,.glb,.gltf,.dae,.mtl,.png,.jpg,.jpeg,.py,.yaml,.yml,.json,.zip";

type Props = {
  value: string;
  onChange: (value: string) => void;
  pendingFiles: File[];
  onAddFiles: (files: File[]) => void;
  onRemoveFile: (index: number) => void;
  onSubmit: () => void;
  disabled?: boolean;
  placeholder?: string;
};

export function PillComposer({
  value,
  onChange,
  pendingFiles,
  onAddFiles,
  onRemoveFile,
  onSubmit,
  disabled,
  placeholder = "Describe your robot simulation goal…",
}: Props) {
  const fileRef = useRef<HTMLInputElement>(null);
  const canSubmit = !disabled && (value.trim().length > 0 || pendingFiles.length > 0);

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (canSubmit) onSubmit();
    }
  }

  function onFilePick(list: FileList | null) {
    if (!list?.length) return;
    onAddFiles(Array.from(list));
    if (fileRef.current) fileRef.current.value = "";
  }

  return (
    <div data-testid="pill-composer" className="w-full max-w-2xl">
      <div
        className="rounded-[28px] border border-slate-300/80 bg-white shadow-lg shadow-slate-200/80"
        style={{ boxShadow: `0 0 0 1px ${BUILDABLES_ORANGE}22` }}
      >
        <AttachmentTray files={pendingFiles} onRemove={onRemoveFile} />
        <div className="flex items-end gap-1 px-2 pb-2 pt-1">
          <input
            ref={fileRef}
            data-testid="pill-file-input"
            type="file"
            multiple
            accept={FILE_ACCEPT}
            className="hidden"
            onChange={(e) => onFilePick(e.target.files)}
          />
          <button
            type="button"
            disabled={disabled}
            className="mb-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-slate-300 text-lg text-slate-700 hover:border-[#FF6A1A] hover:text-[#FF6A1A] disabled:opacity-40"
            aria-label="Attach files"
            onClick={() => fileRef.current?.click()}
          >
            +
          </button>
          <textarea
            data-testid="pill-textarea"
            rows={1}
            value={value}
            disabled={disabled}
            placeholder={placeholder}
            className="min-h-[36px] max-h-32 min-w-0 flex-1 resize-none bg-transparent px-1 py-2 text-sm leading-snug text-slate-900 placeholder:text-slate-500 focus:outline-none"
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={onKeyDown}
          />
          <button
            type="button"
            data-testid="pill-submit"
            disabled={!canSubmit}
            className={`mb-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-white ${accentBg} ${accentHover} disabled:opacity-40`}
            aria-label="Submit"
            onClick={onSubmit}
          >
            ↑
          </button>
        </div>
      </div>
      <p className="mt-2 text-center text-[10px] text-slate-500">
        Attach URDF, STEP, meshes, or zip above the text — files upload when you press Enter or ↑
      </p>
    </div>
  );
}
