"use client";

import { ReactNode } from "react";
import { Group, Panel, Separator } from "react-resizable-panels";

type WorkbenchLayoutProps = {
  left: ReactNode;
  center: ReactNode;
  right: ReactNode;
  bottom: ReactNode;
};

const colSep =
  "w-2 shrink-0 cursor-col-resize bg-slate-300 transition-colors hover:bg-accent/40 active:bg-accent/60";
const rowSep =
  "h-2 shrink-0 cursor-row-resize bg-slate-300 transition-colors hover:bg-accent/40 active:bg-accent/60";

export function WorkbenchLayout({ left, center, right, bottom }: WorkbenchLayoutProps) {
  return (
    <div className="min-h-0 flex-1">
      <Group orientation="vertical" className="h-full" id="workbench">
        <Panel id="main-row" defaultSize="78%" minSize="45%" className="min-h-0">
          <Group orientation="horizontal" className="h-full">
            <Panel id="sidebar" defaultSize="18%" minSize="14%" maxSize="34%" className="min-w-0">
              <aside className="panel h-full overflow-auto border-r border-border">{left}</aside>
            </Panel>
            <Separator className={colSep} />
            <Panel id="viewport" defaultSize="58%" minSize="28%" className="min-w-0">
              <section className="relative h-full overflow-hidden bg-slate-100 p-1">{center}</section>
            </Panel>
            <Separator className={colSep} />
            <Panel id="inspector" defaultSize="24%" minSize="16%" maxSize="36%" className="min-w-0">
              <aside className="panel h-full overflow-auto border-l border-border">{right}</aside>
            </Panel>
          </Group>
        </Panel>
        <Separator className={rowSep} />
        <Panel id="bottom-drawer" defaultSize="22%" minSize="8%" maxSize="55%" collapsible collapsedSize="3%" className="min-h-0">
          <footer className="panel h-full overflow-hidden border-t border-border">{bottom}</footer>
        </Panel>
      </Group>
    </div>
  );
}
