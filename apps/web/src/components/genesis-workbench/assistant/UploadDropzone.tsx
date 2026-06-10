"use client";

import { useRef, useState } from "react";
import { accentMuted } from "../buildablesTheme";

const ACCEPT =
  ".urdf,.xml,.mjcf,.xacro,.step,.stp,.stl,.obj,.dae,.glb,.gltf,.png,.jpg,.jpeg,.py,.json,.zip";

type Props = {
  onFiles: (files: File[]) => void;
  disabled?: boolean;
};

export function UploadDropzone({ onFiles, disabled }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [drag, setDrag] = useState(false);

  function handleFiles(list: FileList | null) {
    if (!list?.length) return;
    onFiles(Array.from(list));
  }

  return (
    <div
      className={`rounded border border-dashed px-3 py-4 text-center transition ${
        drag ? "border-[#FF6A1A] bg-[#FF6A1A]/5" : "border-slate-300 bg-slate-50"
      } ${disabled ? "opacity-50" : "cursor-pointer hover:border-[#FF6A1A]/60"}`}
      onDragOver={(e) => {
        e.preventDefault();
        setDrag(true);
      }}
      onDragLeave={() => setDrag(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDrag(false);
        if (!disabled) handleFiles(e.dataTransfer.files);
      }}
      onClick={() => !disabled && inputRef.current?.click()}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        className="hidden"
        multiple
        accept={ACCEPT}
        disabled={disabled}
        onChange={(e) => handleFiles(e.target.files)}
      />
      <div className={`text-[10px] font-medium ${accentMuted}`}>Drop files or click to upload</div>
      <div className="mt-1 text-[9px] text-slate-500">
        URDF, STEP, meshes, zip bundle, control scripts
      </div>
    </div>
  );
}
