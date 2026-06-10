type Row = { key: string; label: string; status: string; action: string };

type Props = { rows: Row[] };

export function MissingMetadataTable({ rows }: Props) {
  if (rows.length === 0) return null;
  return (
    <table className="w-full text-left text-[9px]">
      <thead>
        <tr className="border-b border-slate-200 text-[#c2410c]">
          <th className="py-1 pr-2">Metadata</th>
          <th className="py-1 pr-2">Status</th>
          <th className="py-1">Action</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.key} className="border-b border-slate-200/80 text-slate-700">
            <td className="py-1 pr-2">{r.label}</td>
            <td className="py-1 pr-2 text-amber-800">{r.status}</td>
            <td className="py-1 text-slate-500">{r.action}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
