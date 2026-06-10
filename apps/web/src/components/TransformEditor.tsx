"use client";

export function TransformEditor() {
  return (
    <section className="panel p-2">
      <h3 className="text-sm font-semibold mb-2">Transform</h3>
      <div className="grid grid-cols-3 gap-1 text-xs">
        <input className="border border-border rounded px-1 py-1" placeholder="X" />
        <input className="border border-border rounded px-1 py-1" placeholder="Y" />
        <input className="border border-border rounded px-1 py-1" placeholder="Z" />
      </div>
    </section>
  );
}
