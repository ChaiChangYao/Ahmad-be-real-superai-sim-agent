"use client";

export function SensorEditor() {
  return (
    <section className="panel p-2">
      <h3 className="text-sm font-semibold mb-2">Sensor Config</h3>
      <div className="grid grid-cols-2 gap-1 text-xs">
        <input className="border border-border rounded px-1 py-1" placeholder="Range m" />
        <input className="border border-border rounded px-1 py-1" placeholder="FOV deg" />
      </div>
    </section>
  );
}
