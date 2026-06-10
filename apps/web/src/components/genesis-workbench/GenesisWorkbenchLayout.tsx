"use client";

import { Group, Panel, Separator } from "react-resizable-panels";
import { ReactNode, useCallback, useEffect, useState } from "react";

const STORAGE_KEY = "genesis-workbench-panel-sizes";

type StoredLayout = Record<string, number>;

type GenesisWorkbenchLayoutProps = {
  left: ReactNode;
  center: ReactNode;
  right: ReactNode;
  bottom?: ReactNode;
};

const colSep =
  "w-1.5 shrink-0 cursor-col-resize bg-slate-100 transition-colors hover:bg-[#FF6A1A]/40 active:bg-[#FF6A1A]/60";
const rowSep =
  "h-1.5 shrink-0 cursor-row-resize bg-slate-100 transition-colors hover:bg-[#FF6A1A]/40 active:bg-[#FF6A1A]/60";

function readStoredLayout(): StoredLayout | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as StoredLayout;
    return parsed && typeof parsed === "object" ? parsed : null;
  } catch {
    return null;
  }
}

export function GenesisWorkbenchLayout({ left, center, right, bottom }: GenesisWorkbenchLayoutProps) {
  const [stored, setStored] = useState<StoredLayout | null>(null);

  useEffect(() => {
    setStored(readStoredLayout());
  }, []);

  const onLayoutChanged = useCallback((layout: Record<string, number>) => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(layout));
  }, []);

  const leftDefault = stored?.["genesis-catalogue"] ?? 18;
  const centerDefault = stored?.["genesis-viewer"] ?? 58;
  const rightDefault = stored?.["genesis-inspector"] ?? 24;

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="min-h-0 flex-1">
        <Group
          orientation="horizontal"
          className="h-full"
          id="genesis-main-columns"
          onLayoutChanged={onLayoutChanged}
        >
          <Panel
            id="genesis-catalogue"
            defaultSize={`${leftDefault}%`}
            minSize="14%"
            maxSize="34%"
            className="min-w-0"
          >
            <aside className="h-full overflow-auto border-r border-slate-200 bg-white">{left}</aside>
          </Panel>
          <Separator className={colSep} />
          <Panel id="genesis-viewer" defaultSize={`${centerDefault}%`} minSize="28%" className="min-w-0">
            <section className="relative h-full overflow-hidden bg-slate-100">{center}</section>
          </Panel>
          <Separator className={colSep} />
          <Panel
            id="genesis-inspector"
            defaultSize={`${rightDefault}%`}
            minSize="16%"
            maxSize="40%"
            className="min-w-0"
          >
            <aside className="h-full overflow-auto border-l border-slate-200 bg-white p-2">{right}</aside>
          </Panel>
        </Group>
      </div>
      {bottom}
    </div>
  );
}

type SplitLayoutProps = {
  top: ReactNode;
  bottom: ReactNode;
  storageKey: string;
  defaultTop?: number;
};

export function GenesisVerticalSplit({
  top,
  bottom,
  storageKey,
  defaultTop = 62,
}: SplitLayoutProps) {
  const panelId = `genesis-split-${storageKey}`;
  const [topDefault, setTopDefault] = useState(defaultTop);

  useEffect(() => {
    const stored = readStoredLayout();
    if (stored?.[panelId] != null) {
      setTopDefault(stored[panelId]);
    }
  }, [panelId]);

  const onLayoutChanged = useCallback(
    (layout: Record<string, number>) => {
      if (typeof window === "undefined") return;
      const existing = readStoredLayout() ?? {};
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...existing, ...layout }));
    },
    [],
  );

  return (
    <Group orientation="vertical" className="h-full" id={`${panelId}-group`} onLayoutChanged={onLayoutChanged}>
      <Panel id={panelId} defaultSize={`${topDefault}%`} minSize="25%" className="min-h-0">
        {top}
      </Panel>
      <Separator className={rowSep} />
      <Panel id={`${panelId}-bottom`} defaultSize={`${100 - topDefault}%`} minSize="20%" className="min-h-0">
        {bottom}
      </Panel>
    </Group>
  );
}

type HorizontalSplitProps = {
  left: ReactNode;
  right: ReactNode;
  storageKey: string;
  defaultLeft?: number;
};

export function GenesisHorizontalSplit({
  left,
  right,
  storageKey,
  defaultLeft = 50,
}: HorizontalSplitProps) {
  const panelId = `genesis-hsplit-${storageKey}`;
  const [leftDefault, setLeftDefault] = useState(defaultLeft);

  useEffect(() => {
    const stored = readStoredLayout();
    if (stored?.[panelId] != null) {
      setLeftDefault(stored[panelId]);
    }
  }, [panelId]);

  const onLayoutChanged = useCallback((layout: Record<string, number>) => {
    if (typeof window === "undefined") return;
    const existing = readStoredLayout() ?? {};
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...existing, ...layout }));
  }, []);

  return (
    <Group orientation="horizontal" className="h-full" id={`${panelId}-group`} onLayoutChanged={onLayoutChanged}>
      <Panel id={panelId} defaultSize={`${leftDefault}%`} minSize="25%" className="min-w-0">
        {left}
      </Panel>
      <Separator className={colSep} />
      <Panel id={`${panelId}-right`} defaultSize={`${100 - leftDefault}%`} minSize="25%" className="min-w-0">
        {right}
      </Panel>
    </Group>
  );
}
