import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link, useBlocker, useParams } from "react-router-dom";

import { useAuth } from "@/features/auth/context";
import { roomKeys } from "@/features/rooms/api";
import { RoomDialog } from "@/features/rooms/RoomDialog";
import { ApiError } from "@/shared/api/client";
import {
  confirmSchedule,
  deleteSchedule,
  getOwnSchedule,
  ownScheduleKey,
  uploadSchedule,
  type Cell,
  type Schedule,
} from "./api";
import { ImageSelection } from "./ImageSelection";
import { ScheduleGrid } from "./ScheduleGrid";

type Edit = { base: Schedule; cells: Cell[] };
type Operation = "upload" | "confirm" | "delete";
const statusLabels = {
  missing: "Sin horario",
  draft: "Borrador",
  confirmed: "Confirmado",
};
const primary =
  "rounded bg-blue-700 px-4 py-2 font-medium text-white disabled:opacity-50";
const secondary =
  "rounded border border-slate-400 px-4 py-2 disabled:opacity-50";

export function SchedulePage() {
  const { roomId = "" } = useParams();
  const { session } = useAuth();
  const cache = useQueryClient();
  const key = ownScheduleKey(roomId);
  const schedule = useQuery({
    queryKey: key,
    queryFn: ({ signal }) => getOwnSchedule(roomId, signal),
    retry: false,
  });
  const [file, setFile] = useState<File | null>(null);
  const [inputVersion, resetInput] = useState(0);
  const [edit, setEdit] = useState<Edit | null>(null);
  const [dialog, setDialog] = useState<"upload" | "delete" | null>(null);
  const base = edit?.base ?? schedule.data?.schedule;
  const cells = edit?.cells ?? base?.blocks ?? [];
  const csrf = session?.csrf_token ?? "";
  const dirty = edit !== null;
  const blocker = useBlocker(dirty);
  useEffect(() => {
    if (!dirty) return;
    function onClose(event: BeforeUnloadEvent) {
      event.preventDefault();
    }
    window.addEventListener("beforeunload", onClose);
    return () => window.removeEventListener("beforeunload", onClose);
  }, [dirty]);

  const mutation = useMutation({
    mutationFn: async (operation: Operation) => {
      if (!base) return;
      if (operation === "upload" && file)
        return uploadSchedule(roomId, file, base, csrf);
      if (operation === "confirm")
        return confirmSchedule(roomId, base, cells, csrf);
      if (operation === "delete") await deleteSchedule(roomId, base, csrf);
    },
    onSuccess: async (result, operation) => {
      setEdit(null);
      if (operation !== "confirm") {
        setFile(null);
        resetInput((count) => count + 1);
      }
      if (result) {
        await cache.cancelQueries({ queryKey: key });
        cache.setQueryData(key, {
          schedule: result,
          maxBytes: schedule.data?.maxBytes ?? 5 * 1024 ** 2,
        });
      } else {
        await cache.invalidateQueries({ queryKey: key });
      }
      await cache.invalidateQueries({ queryKey: roomKeys.list });
    },
  });
  const conflict =
    mutation.error instanceof ApiError && mutation.error.status === 409;
  const problem =
    mutation.error instanceof Error
      ? mutation.error.message
      : "No se pudo actualizar el horario.";

  function toggle(target: Cell) {
    if (!base) return;
    const changed = cells.map((cell) =>
      cell.day === target.day && cell.block === target.block
        ? { ...cell, is_occupied: !cell.is_occupied }
        : cell,
    );
    const changedFromBase = changed.some(
      (cell, index) => cell.is_occupied !== base.blocks[index]?.is_occupied,
    );
    setEdit(changedFromBase ? { base, cells: changed } : null);
  }

  function reload() {
    setEdit(null);
    mutation.reset();
    void schedule.refetch();
  }

  return (
    <main className="mx-auto max-w-5xl px-6 py-12 text-slate-900">
      <Link to={`/app/salas/${roomId}`} className="text-blue-800 underline">
        Volver a la sala
      </Link>
      <h1 className="my-4 text-3xl font-bold">Mi horario</h1>
      {schedule.isPending && <p role="status">Cargando horario…</p>}
      {schedule.isError && <p role="alert">{schedule.error.message}</p>}
      {base && schedule.data && !schedule.isError && (
        <>
          <section className="rounded border border-slate-300 p-4">
            <ImageSelection
              key={inputVersion}
              maxBytes={schedule.data.maxBytes}
              disabled={mutation.isPending}
              onSelect={setFile}
              file={file}
            />
            <button
              className={`mt-3 ${primary}`}
              disabled={!file || dirty || mutation.isPending}
              onClick={() => {
                if (base.status === "confirmed") setDialog("upload");
                else mutation.mutate("upload");
              }}
            >
              Cargar captura
            </button>
          </section>
          {mutation.isPending && (
            <p className="mt-4" role="status">
              {mutation.variables === "upload"
                ? "Cargando y procesando captura…"
                : "Guardando cambios…"}
            </p>
          )}
          {mutation.isError && (
            <div className="mt-4" role="alert">
              <p className="text-red-800">{problem}</p>
              {conflict && (
                <button
                  className="mt-2 text-blue-800 underline"
                  onClick={reload}
                >
                  Recargar horario y descartar cambios locales
                </button>
              )}
            </div>
          )}
          <section className="mt-8">
            <h2 className="mb-3 text-xl font-semibold">
              {statusLabels[base.status]}
            </h2>
            {base.status === "missing" ? (
              <p>Carga una captura para crear tu horario.</p>
            ) : (
              <>
                {base.status === "draft" && (
                  <p className="mb-3 text-slate-700">
                    Revisa las celdas y confirma el horario para compartir tu
                    disponibilidad.
                  </p>
                )}
                <ScheduleGrid
                  cells={cells}
                  onToggle={toggle}
                  disabled={mutation.isPending}
                />
                {dirty && (
                  <p className="my-2" role="status">
                    Cambios sin guardar.
                  </p>
                )}
                <div className="mt-4 flex flex-wrap gap-3">
                  <button
                    className={primary}
                    disabled={
                      mutation.isPending ||
                      (!dirty && base.status === "confirmed")
                    }
                    onClick={() => mutation.mutate("confirm")}
                  >
                    Guardar y confirmar
                  </button>
                  <button
                    className={secondary}
                    disabled={!dirty || mutation.isPending}
                    onClick={() => setEdit(null)}
                  >
                    Descartar cambios
                  </button>
                  <button
                    className={secondary}
                    disabled={dirty || mutation.isPending}
                    onClick={() => setDialog("delete")}
                  >
                    Eliminar horario
                  </button>
                </div>
              </>
            )}
          </section>
        </>
      )}
      {dialog && (
        <RoomDialog
          title={
            dialog === "upload"
              ? "Reemplazar horario confirmado"
              : "Eliminar horario"
          }
          busy={false}
          onClose={() => setDialog(null)}
        >
          <p className="mb-4">
            {dialog === "upload"
              ? "Si la carga funciona, el nuevo horario quedará como borrador hasta que lo confirmes."
              : "Se eliminará el horario de esta sala."}
          </p>
          <button
            className={primary}
            onClick={() => {
              mutation.mutate(dialog);
              setDialog(null);
            }}
          >
            {dialog === "upload" ? "Reemplazar" : "Confirmar eliminación"}
          </button>
        </RoomDialog>
      )}
      {blocker.state === "blocked" && (
        <RoomDialog
          title="Cambios sin guardar"
          busy={false}
          onClose={blocker.reset}
        >
          <p className="mb-4">
            Si sales, perderás las modificaciones de la grilla.
          </p>
          <button className={secondary} onClick={blocker.proceed}>
            Salir sin guardar
          </button>
        </RoomDialog>
      )}
    </main>
  );
}
