import { useQuery } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { overlapKeys, readCell, readOverlap, type Coordinate } from "./api";
import { CellPanel } from "./CellPanel";
import { Heatmap } from "./Heatmap";

const refreshInterval = 30_000;

export function OverlapPage() {
  const { roomId = "" } = useParams();
  const [selected, setSelected] = useState<Coordinate | null>(null);
  const checkedDetail = useRef(0);
  const group = useQuery({
    queryKey: overlapKeys.group(roomId),
    queryFn: ({ signal }) => readOverlap(roomId, signal),
    retry: false,
    refetchInterval: refreshInterval,
  });
  const detail = useQuery({
    queryKey: overlapKeys.cell(roomId, selected),
    queryFn: ({ signal }) =>
      selected ? readCell(roomId, selected, signal) : null,
    enabled:
      selected !== null && !!group.data?.confirmed_members && !group.isError,
    retry: false,
    refetchInterval: refreshInterval,
  });
  const groupData = group.data;
  const detailData = detail.data;
  const detailUpdatedAt = detail.dataUpdatedAt;
  const reloadGroup = group.refetch;
  useEffect(() => {
    if (
      !groupData ||
      !detailData ||
      !detailUpdatedAt ||
      checkedDetail.current === detailUpdatedAt
    )
      return;
    checkedDetail.current = detailUpdatedAt;
    const corresponding = groupData.cells.find(
      (cell) => cell.day === detailData.day && cell.block === detailData.block,
    );
    if (
      corresponding &&
      (groupData.total_members !== detailData.total_members ||
        corresponding.weight !== detailData.weight ||
        corresponding.available_count !== detailData.available_count ||
        corresponding.pending_count !== detailData.pending_count)
    ) {
      void reloadGroup();
    }
  }, [groupData, detailData, detailUpdatedAt, reloadGroup]);

  return (
    <main className="mx-auto max-w-5xl px-6 py-12 text-slate-900">
      <Link to={`/app/salas/${roomId}`} className="text-blue-800 underline">
        Volver a la sala
      </Link>
      <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-3xl font-bold">Superposición</h1>
        <button
          className="rounded border px-4 py-2"
          disabled={group.isFetching}
          onClick={() => {
            void group.refetch();
            if (selected && group.data?.confirmed_members)
              void detail.refetch();
          }}
        >
          Actualizar
        </button>
      </div>
      {group.isPending && (
        <p role="status" className="mt-4">
          Cargando disponibilidad…
        </p>
      )}
      {group.isError && (
        <p role="alert" className="mt-4">
          {group.error.message}
        </p>
      )}
      {groupData && !group.isError && (
        <>
          <dl className="my-5 grid grid-cols-2 gap-3 rounded bg-slate-100 p-4 sm:grid-cols-4">
            <div>
              <dt>Total</dt>
              <dd className="font-bold">{groupData.total_members}</dd>
            </div>
            <div>
              <dt>Confirmados</dt>
              <dd className="font-bold">{groupData.confirmed_members}</dd>
            </div>
            <div>
              <dt>Pendientes</dt>
              <dd className="font-bold">{groupData.pending_members}</dd>
            </div>
            <div>
              <dt>Cobertura</dt>
              <dd className="font-bold">
                {new Intl.NumberFormat("es", {
                  style: "percent",
                  maximumFractionDigits: 1,
                }).format(groupData.coverage)}
              </dd>
            </div>
          </dl>
          {!groupData.confirmed_members ? (
            <p role="status">
              Todavía no hay horarios confirmados. No se puede determinar la
              disponibilidad.
            </p>
          ) : (
            <>
              <p className="mb-4 text-sm">
                Selecciona un bloque para ver quién está ocupado, disponible o
                pendiente. Un bloque con peso cero solo indica disponibilidad
                total si todos confirmaron su horario.
              </p>
              <Heatmap
                cells={groupData.cells}
                selected={selected}
                onSelect={setSelected}
              />
              {selected && detail.isPending && (
                <p role="status" className="mt-4">
                  Cargando detalle…
                </p>
              )}
              {selected && detail.isError && (
                <p role="alert" className="mt-4">
                  {detail.error.message}
                </p>
              )}
              {selected && detailData && !detail.isError && (
                <CellPanel cell={detailData} />
              )}
            </>
          )}
        </>
      )}
    </main>
  );
}
