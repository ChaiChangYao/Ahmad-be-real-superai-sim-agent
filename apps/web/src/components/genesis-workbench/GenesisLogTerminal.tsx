"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type Props = {
  lines: string[];
  onClear: () => void;
  /** When false, only the header bar is shown until the user expands. */
  defaultExpanded?: boolean;
};

function ChevronUpIcon() {
  return (
    <svg viewBox="0 0 16 16" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M4 10 L8 6 L12 10" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function ChevronDownIcon() {
  return (
    <svg viewBox="0 0 16 16" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M4 6 L8 10 L12 6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function GenesisLogTerminal({ lines, onClear, defaultExpanded = true }: Props) {
  const [expanded, setExpanded] = useState(defaultExpanded);
  const scrollRef = useRef<HTMLDivElement>(null);
  const stickToBottom = useRef(true);

  useEffect(() => {
    if (!expanded || !stickToBottom.current || !scrollRef.current) return;
    scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [lines, expanded]);

  const onScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    stickToBottom.current = el.scrollHeight - el.scrollTop - el.clientHeight < 48;
  }, []);

  const copyLogs = useCallback(async () => {
    const text = lines.join("\n");
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      const area = document.createElement("textarea");
      area.value = text;
      document.body.appendChild(area);
      area.select();
      document.execCommand("copy");
      document.body.removeChild(area);
    }
  }, [lines]);

  const toggleBtn =
    "flex h-6 w-6 items-center justify-center rounded border border-slate-300 text-slate-600 hover:bg-slate-100";

  return (
    <div className="shrink-0 border border-white bg-white shadow-[0_-1px_0_0_#e2e8f0]">
      <div className="flex items-center justify-between gap-2 px-3 py-1.5">
        <span className="text-[10px] font-medium tracking-wide text-slate-800">Session log</span>
        <div className="flex items-center gap-1.5">
          {expanded ? (
            <>
              <button
                type="button"
                className="rounded border border-slate-300 px-2 py-0.5 text-[10px] text-slate-700 hover:bg-slate-100 disabled:opacity-40"
                disabled={lines.length === 0}
                onClick={() => void copyLogs()}
              >
                Copy
              </button>
              <button
                type="button"
                className="rounded border border-slate-300 px-2 py-0.5 text-[10px] text-slate-700 hover:bg-slate-100 disabled:opacity-40"
                disabled={lines.length === 0}
                onClick={onClear}
              >
                Clear
              </button>
              <button
                type="button"
                className={toggleBtn}
                aria-label="Collapse session log"
                title="Collapse"
                onClick={() => setExpanded(false)}
              >
                <ChevronDownIcon />
              </button>
            </>
          ) : (
            <button
              type="button"
              className={toggleBtn}
              aria-label="Expand session log"
              title="Expand"
              onClick={() => setExpanded(true)}
            >
              <ChevronUpIcon />
            </button>
          )}
        </div>
      </div>
      {expanded ? (
        <div
          ref={scrollRef}
          onScroll={onScroll}
          className="max-h-40 min-h-[6rem] overflow-y-auto border-t border-slate-200 px-3 py-2 font-mono text-[10px] leading-relaxed text-slate-600"
        >
          {lines.length === 0 ? (
            <div className="text-slate-500">Launch output, backend stdout/stderr, and errors appear here.</div>
          ) : (
            lines.map((line, i) => (
              <div key={`${i}-${line.slice(0, 24)}`} className="whitespace-pre-wrap break-all">
                {line}
              </div>
            ))
          )}
        </div>
      ) : null}
    </div>
  );
}
