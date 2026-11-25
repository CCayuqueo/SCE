import { BLOCKS, DAYS } from "@/shared/constants/schedule";
import type { CellDetails, MemberSummary } from "./api";

function Group({
  title,
  members,
}: {
  title: string;
  members: MemberSummary[];
}) {
  return (
    <div>
      <h3 className="font-semibold">
        {title} ({members.length})
      </h3>
      {members.length ? (
        <ul className="mt-1 list-inside list-disc">
          {members.map((member) => (
            <li key={member.id}>{member.name}</li>
          ))}
        </ul>
      ) : (
        <p className="mt-1 text-slate-700">Ninguno.</p>
      )}
    </div>
  );
}

export function CellPanel({ cell }: { cell: CellDetails }) {
  return (
    <section
      aria-label="Detalle del bloque"
      className="mt-6 rounded border border-slate-300 p-4"
    >
      <h2 className="mb-3 text-xl font-semibold">
        {DAYS[cell.day - 1]} {BLOCKS[cell.block - 1]}
      </h2>
      <div className="grid gap-4 sm:grid-cols-3">
        <Group title="Ocupados" members={cell.occupied_members} />
        <Group title="Disponibles" members={cell.available_members} />
        <Group title="Pendientes" members={cell.pending_members} />
      </div>
    </section>
  );
}
