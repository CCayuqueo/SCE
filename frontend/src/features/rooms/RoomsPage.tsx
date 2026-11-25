import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { type FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { useAuth } from "@/features/auth/context";
import {
  listRooms,
  roles,
  roomKeys,
  schedules,
  writeRoom,
  type Room,
} from "./api";
import { RoomDialog } from "./RoomDialog";
import { action, errorMessage, input } from "./styles";

function RoomList({ title, rooms }: { title: string; rooms: Room[] }) {
  return (
    <section className="mt-8">
      <h2 className="text-xl font-semibold">{title}</h2>
      {rooms.length ? (
        <ul className="mt-3 grid gap-3 sm:grid-cols-2">
          {rooms.map((room) => (
            <li key={room.id} className="rounded border border-slate-300 p-4">
              <Link
                className="font-semibold text-blue-800 underline"
                to={`/app/salas/${room.id}`}
              >
                {room.name}
              </Link>
              {room.description && <p className="mt-1">{room.description}</p>}
              <p className="mt-2 text-sm text-slate-700">
                {roles[room.current_user_role]} · {room.members_count}{" "}
                integrantes · {schedules[room.schedule_status]}
              </p>
              {room.code && (
                <p className="mt-2 text-sm">
                  Código <code>{room.code}</code>
                </p>
              )}
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-3 text-slate-700">Aún no hay salas en esta sección.</p>
      )}
    </section>
  );
}

export function RoomsPage() {
  const { session } = useAuth();
  const [search, setSearch] = useSearchParams();
  const selection = search.get("accion");
  const mode =
    selection === "crear" ? "create" : selection === "unirse" ? "join" : null;
  const navigate = useNavigate();
  const cache = useQueryClient();
  const rooms = useQuery({
    queryKey: roomKeys.list,
    queryFn: ({ signal }) => listRooms(signal),
  });
  const mutation = useMutation({
    mutationFn: ({ path, body }: { path: string; body: object }) =>
      writeRoom<Room>(path, "POST", session?.csrf_token ?? "", body),
    onSuccess: async (room) => {
      await cache.invalidateQueries({ queryKey: roomKeys.list });
      navigate(`/app/salas/${room.id}`);
    },
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    if (mode === "create") {
      mutation.mutate({
        path: "",
        body: {
          name: String(form.get("name")),
          description: String(form.get("description")) || null,
        },
      });
    } else {
      mutation.mutate({
        path: "/join",
        body: { code: String(form.get("code")) },
      });
    }
  }

  function setDialog(next: typeof mode) {
    mutation.reset();
    setSearch(next ? { accion: next === "create" ? "crear" : "unirse" } : {}, {
      replace: true,
    });
  }

  const values = rooms.data ?? [];
  return (
    <main className="mx-auto max-w-4xl px-6 py-12 text-slate-900">
      <Link to="/app/inicio" className="text-blue-800 underline">
        Volver a Inicio
      </Link>
      <h1 className="mt-3 text-3xl font-bold">Mis salas</h1>
      <div className="mt-5 flex flex-wrap gap-3">
        <button className={action} onClick={() => setDialog("create")}>
          Crear sala
        </button>
        <button
          className="rounded border px-4 py-2"
          onClick={() => setDialog("join")}
        >
          Unirse a sala
        </button>
      </div>
      {rooms.isPending && (
        <p role="status" className="mt-4">
          Cargando salas…
        </p>
      )}
      {rooms.isError && (
        <p role="alert" className="mt-4">
          {errorMessage(rooms.error)}
        </p>
      )}
      {rooms.isSuccess && (
        <>
          <RoomList
            title="Salas creadas"
            rooms={values.filter((room) => room.current_user_role === "owner")}
          />
          <RoomList
            title="Salas unidas"
            rooms={values.filter((room) => room.current_user_role !== "owner")}
          />
        </>
      )}
      {mode && (
        <RoomDialog
          title={mode === "create" ? "Crear sala" : "Unirse a sala"}
          busy={mutation.isPending}
          onClose={() => setDialog(null)}
        >
          <form className="space-y-3" onSubmit={submit}>
            {mode === "create" ? (
              <>
                <label className="block">
                  Nombre de la sala
                  <input
                    className={input}
                    name="name"
                    maxLength={100}
                    required
                  />
                </label>
                <label className="block">
                  Descripción (opcional)
                  <textarea
                    className={input}
                    name="description"
                    maxLength={500}
                  />
                </label>
              </>
            ) : (
              <label className="block">
                Código de sala
                <input
                  className={input}
                  name="code"
                  autoComplete="off"
                  required
                />
              </label>
            )}
            {mutation.isError && (
              <p role="alert" className="text-red-800">
                {errorMessage(mutation.error)}
              </p>
            )}
            <button
              className={action}
              type="submit"
              disabled={mutation.isPending}
            >
              {mode === "create" ? "Crear sala" : "Unirse"}
            </button>
          </form>
        </RoomDialog>
      )}
    </main>
  );
}
