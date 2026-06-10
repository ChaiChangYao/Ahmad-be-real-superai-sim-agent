"use client";

export function MaterialEditor() {
  return (
    <section className="panel p-2">
      <h3 className="text-sm font-semibold mb-2">Material</h3>
      <div className="grid grid-cols-2 gap-1 text-xs">
        <input className="border border-border rounded px-1 py-1" placeholder="Density kg/m3" />
        <input className="border border-border rounded px-1 py-1" placeholder="Friction" />
      </div>
    </section>
  );
}
