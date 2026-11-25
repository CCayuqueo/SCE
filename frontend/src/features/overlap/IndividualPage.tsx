import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { readMembers, roomKeys } from "@/features/rooms/api";
import { ScheduleGrid } from "@/features/schedules/ScheduleGrid";
import { overlapKeys, readIndividual } from "./api";

export function IndividualPage() {
  const { roomId = "" } = useParams();
  const [requested, setRequested] = useState("");
  const roster = useQuery({
    queryKey: roomKeys.members(roomId),
    queryFn: ({ signal }) => readMembers(roomId, signal),
    retry: false,
  });
  const member = roster.data?.members.find(({ id }) => id === requested);
  const selected = member?.id ?? "";
  const schedule = useQuery({
    queryKey: overlapKeys.individual(roomId, selected),
    queryFn: ({ signal }) => readIndividual(roomId, selected, signal),
    enabled: !!selected && !roster.isError,
    retry: false,
  });

  return (
    <main className="mx-auto max-w-5xl px-6 py-12 text-slate-900">
      <Link to={`/app/salas/${roomId}`} className="text-blue-800 underline">
        Volver a la sala
      </Link>
      <h1 className="mb-5 mt-4 text-3xl font-bold">Horarios individuales</h1>
      {roster.isPending && <p role="status">Cargando integrantes…</p>}
      {roster.isError && <p role="alert">{roster.error.message}</p>}
      {roster.data && !roster.isError && (
        <>
          <div className="max-w-md">
            <label className="block" htmlFor="schedule-member">
              Integrante
            </label>
            <select
              id="schedule-member"
              value={selected}
              onChange={(event) => setRequested(event.target.value)}
              className="mt-1 w-full rounded border border-slate-400 px-3 py-2"
            >
              <option value="">Selecciona un integrante</option>
              {roster.data.members.map(({ id, name }) => (
                <option key={id} value={id}>
                  {name}
                </option>
              ))}
            </select>
          </div>
          {member && (
            <section className="mt-6">
              <h2 className="mb-3 text-xl font-semibold">{member.name}</h2>
              {schedule.isPending && <p role="status">Cargando horario…</p>}
              {schedule.isError && <p role="alert">{schedule.error.message}</p>}
              {schedule.data?.status === "missing" && !schedule.isError && (
                <p>Este integrante todavía no ha cargado un horario.</p>
              )}
              {schedule.data?.status === "draft" && !schedule.isError && (
                <p>Este integrante tiene un horario pendiente de confirmar.</p>
              )}
              {schedule.data?.status === "confirmed" && !schedule.isError && (
                <>
                  <p className="mb-3">Horario confirmado · Solo lectura</p>
                  <ScheduleGrid cells={schedule.data.blocks} />
                </>
              )}
            </section>
          )}
        </>
      )}
    </main>
  );
}
