import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { useAuth } from "@/features/auth/context";
import { ApiError } from "@/shared/api/client";
import {
  readMembers,
  readRoom,
  roles,
  roomKeys,
  schedules,
  writeRoom,
  type Member,
} from "./api";
import { RoomDialog } from "./RoomDialog";
import { action, destructive, errorMessage, input } from "./styles";

type Command = {
  path: string;
  method: "PATCH" | "POST" | "DELETE";
  body?: object;
  exit?: boolean;
};
type Confirmation = {
  title: string;
  message: string;
  button: string;
  command: Command;
};

export function RoomPage() {
  const { roomId = "" } = useParams();
  const { session } = useAuth();
  const navigate = useNavigate();
  const cache = useQueryClient();
  const [dialog, setDialog] = useState<Confirmation | null>(null);
  const [copyNotice, setCopyNotice] = useState("");
  const room = useQuery({
    queryKey: roomKeys.detail(roomId),
    queryFn: ({ signal }) => readRoom(roomId, signal),
    retry: false,
  });
  const role = room.data?.current_user_role;
  const canAdmin = role === "admin" || role === "owner";
  const roster = useQuery({
    queryKey: roomKeys.members(roomId),
    queryFn: ({ signal }) => readMembers(roomId, signal),
    enabled: canAdmin,
    retry: false,
  });
  const mutation = useMutation({
    mutationFn: (cmd: Command) =>
      writeRoom(cmd.path, cmd.method, session?.csrf_token ?? "", cmd.body),
    onSuccess: async (_, cmd) => {
      setDialog(null);
      if (cmd.exit) navigate("/app/salas", { replace: true });
      await cache.invalidateQueries({ queryKey: roomKeys.list });
    },
    onError: async (error) => {
      if (error instanceof ApiError && [403, 404, 409].includes(error.status)) {
        await cache.invalidateQueries({ queryKey: roomKeys.list });
      }
    },
  });
  const root = `/${roomId}`;

  function confirm(options: Confirmation) {
    mutation.reset();
    setDialog(options);
  }

  function edit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    mutation.mutate({
      path: root,
      method: "PATCH",
      body: {
        name: String(form.get("name")),
        description: String(form.get("description")) || null,
      },
    });
  }

  async function copy(code: string) {
    try {
      await navigator.clipboard.writeText(code);
      setCopyNotice("Código copiado.");
    } catch {
      setCopyNotice(
        "No se pudo copiar automáticamente. Puedes seleccionar el código.",
      );
    }
  }

  function transfer(member: Member) {
    confirm({
      title: "Transferir propiedad",
      message: `La propiedad pasará a ${member.name}. Conservarás el rol de administrador.`,
      button: "Confirmar transferencia",
      command: {
        path: `${root}/transfer-ownership`,
        method: "POST",
        body: { new_owner_id: member.user_id },
      },
    });
  }

  return (
    <main className="mx-auto max-w-4xl px-6 py-12 text-slate-900">
      <Link to="/app/salas" className="text-blue-800 underline">
        Volver a Mis salas
      </Link>
      {room.isPending && (
        <p role="status" className="mt-4">
          Cargando sala…
        </p>
      )}
      {room.isError && (
        <p role="alert" className="mt-4">
          {errorMessage(room.error)}
        </p>
      )}
      {room.data && !room.isError && (
        <>
          <h1 className="mt-3 text-3xl font-bold">{room.data.name}</h1>
          {room.data.description && (
            <p className="mt-2">{room.data.description}</p>
          )}
          <p className="mt-2">
            {roles[room.data.current_user_role]} · {room.data.members_count}{" "}
            integrantes · {schedules[room.data.schedule_status]}
          </p>
          {room.data.code && (
            <div className="mt-4 flex flex-wrap items-center gap-3">
              <span>
                Código{" "}
                <code className="rounded bg-slate-100 px-2 py-1">
                  <Link
                    className="mt-3 inline-block text-blue-800 underline"
                    to={`/app/salas/${roomId}/mi-horario`}
                  >
                    Mi horario
                  </Link>
                  {room.data.code}
                </code>
              </span>
              <button
                className="text-blue-800 underline"
                onClick={() => void copy(room.data?.code ?? "")}
              >
                Copiar código
              </button>
              {copyNotice && <span role="status">{copyNotice}</span>}
            </div>
          )}
          {mutation.isError && !dialog && (
            <p role="alert" className="mt-4 text-red-800">
              {errorMessage(mutation.error)}
            </p>
          )}
          {canAdmin && (
            <>
              <section className="mt-8">
                <h2 className="text-xl font-semibold">Configuración de sala</h2>
                <form
                  key={JSON.stringify([room.data.name, room.data.description])}
                  className="mt-3 max-w-md space-y-3"
                  onSubmit={edit}
                >
                  <label className="block">
                    Nombre de la sala
                    <input
                      className={input}
                      name="name"
                      defaultValue={room.data.name}
                      required
                      maxLength={100}
                    />
                  </label>
                  <label className="block">
                    Descripción
                    <textarea
                      className={input}
                      name="description"
                      defaultValue={room.data.description ?? ""}
                      maxLength={500}
                    />
                  </label>
                  <button
                    className={action}
                    type="submit"
                    disabled={mutation.isPending}
                  >
                    Guardar sala
                  </button>
                </form>
              </section>
              <section className="mt-8">
                <h2 className="text-xl font-semibold">Integrantes</h2>
                {roster.isPending && <p role="status">Cargando integrantes…</p>}
                {roster.isError && (
                  <p role="alert">{errorMessage(roster.error)}</p>
                )}
                {roster.data && !roster.isError && (
                  <div className="mt-3 overflow-x-auto">
                    <table className="w-full min-w-lg text-left">
                      <thead>
                        <tr className="border-b border-slate-300">
                          <th scope="col" className="p-2">
                            Nombre
                          </th>
                          <th scope="col" className="p-2">
                            Rol
                          </th>
                          <th scope="col" className="p-2">
                            Horario
                          </th>
                          <th scope="col" className="p-2">
                            Acciones
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {roster.data.members.map((member) => (
                          <tr
                            key={member.id}
                            className="border-b border-slate-200"
                          >
                            <th scope="row" className="p-2 font-medium">
                              {member.name}
                            </th>
                            <td className="p-2">{roles[member.role]}</td>
                            <td className="p-2">
                              {schedules[member.schedule_status]}
                            </td>
                            <td className="p-2">
                              {member.role !== "owner" && (
                                <div className="flex flex-wrap gap-3">
                                  {(member.role === "member" ||
                                    role === "owner") && (
                                    <button
                                      className="text-blue-800 underline"
                                      disabled={mutation.isPending}
                                      onClick={() =>
                                        mutation.mutate({
                                          path: `${root}/members/${member.id}/role`,
                                          method: "PATCH",
                                          body: {
                                            role:
                                              member.role === "member"
                                                ? "admin"
                                                : "member",
                                          },
                                        })
                                      }
                                    >
                                      {member.role === "member"
                                        ? "Promover"
                                        : "Revocar rol de administrador"}
                                    </button>
                                  )}
                                  {role === "owner" && (
                                    <>
                                      <button
                                        className="text-blue-800 underline"
                                        onClick={() => transfer(member)}
                                      >
                                        Transferir propiedad
                                      </button>
                                      <button
                                        className="text-red-800 underline"
                                        onClick={() =>
                                          confirm({
                                            title: "Expulsar integrante",
                                            message: `Se retirará a ${member.name} y se eliminará su horario de esta sala.`,
                                            button: "Confirmar expulsión",
                                            command: {
                                              path: `${root}/members/${member.id}`,
                                              method: "DELETE",
                                            },
                                          })
                                        }
                                      >
                                        Expulsar
                                      </button>
                                    </>
                                  )}
                                </div>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </section>
            </>
          )}
          <div className="mt-8 border-t border-slate-300 pt-4">
            {role === "owner" ? (
              <button
                className={destructive}
                onClick={() =>
                  confirm({
                    title: "Eliminar sala",
                    message:
                      "Se eliminarán la sala, sus membresías y sus horarios.",
                    button: "Confirmar eliminación",
                    command: { path: root, method: "DELETE", exit: true },
                  })
                }
              >
                Eliminar sala
              </button>
            ) : (
              <button
                className={destructive}
                onClick={() =>
                  confirm({
                    title: "Abandonar sala",
                    message:
                      "Se eliminará tu membresía y tu horario de esta sala.",
                    button: "Confirmar abandono",
                    command: {
                      path: `${root}/membership/me`,
                      method: "DELETE",
                      exit: true,
                    },
                  })
                }
              >
                Abandonar sala
              </button>
            )}
          </div>
        </>
      )}
      {dialog && (
        <RoomDialog
          title={dialog.title}
          busy={mutation.isPending}
          onClose={() => {
            setDialog(null);
            mutation.reset();
          }}
        >
          <p className="mb-4">{dialog.message}</p>
          {mutation.isError && (
            <p role="alert" className="mb-3 text-red-800">
              {errorMessage(mutation.error)}
            </p>
          )}
          <button
            className={action}
            disabled={mutation.isPending}
            onClick={() => mutation.mutate(dialog.command)}
          >
            {dialog.button}
          </button>
        </RoomDialog>
      )}
    </main>
  );
}
