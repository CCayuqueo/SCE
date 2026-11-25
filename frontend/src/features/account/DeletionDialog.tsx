import { useEffect, useRef, useState, type FormEvent } from "react";

import { ApiError } from "@/shared/api/client";
import { readDeletionPreview, removeAccount, type RoomAction } from "./api";
import { danger, errorMessage, field } from "./forms";

type Snapshot = Awaited<ReturnType<typeof readDeletionPreview>>;

export function DeletionDialog({
  csrf,
  onDeleted,
}: {
  csrf: string;
  onDeleted: () => Promise<void>;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (snapshot && !dialog.current?.open) dialog.current?.showModal();
  }, [snapshot]);

  async function open() {
    setPending(true);
    setError("");
    try {
      setSnapshot(await readDeletionPreview());
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setPending(false);
    }
  }

  async function confirm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!snapshot || pending) return;
    const form = new FormData(event.currentTarget);
    const room_actions = snapshot.preview.owned_rooms.flatMap(
      (room): RoomAction[] => {
        if (!room.requires_decision) return [];
        const choice = String(form.get(room.room_id) ?? "");
        return choice === "close"
          ? [{ room_id: room.room_id, action: "close" }]
          : [
              {
                room_id: room.room_id,
                action: "transfer",
                new_owner_id: choice,
              },
            ];
      },
    );
    setPending(true);
    setError("");
    try {
      await removeAccount(
        {
          current_password: String(form.get("password")),
          confirmation: String(form.get("confirmation")),
          room_actions,
        },
        csrf,
        snapshot.revision,
      );
      await onDeleted();
    } catch (err) {
      setError(errorMessage(err));
      if (err instanceof ApiError && err.status === 409) {
        dialog.current?.close();
        setSnapshot(null);
      }
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="mt-10 border-t border-slate-300 pt-6">
      <h2 className="text-xl font-semibold">Eliminar cuenta</h2>
      <button className={`mt-4 ${danger}`} disabled={pending} onClick={open}>
        Revisar eliminación
      </button>
      {!snapshot && error && (
        <p className="mt-3 text-red-800" role="alert">
          {error}
        </p>
      )}
      <dialog
        ref={dialog}
        className="m-auto max-h-[90vh] w-[min(42rem,95vw)] overflow-y-auto rounded p-6 backdrop:bg-black/50"
        aria-labelledby="deletion-title"
        onClose={() => setSnapshot(null)}
        onCancel={(event) => {
          if (pending) event.preventDefault();
        }}
      >
        {snapshot && (
          <form className="space-y-4" onSubmit={confirm}>
            <h3 id="deletion-title" className="text-xl font-bold">
              Eliminar cuenta permanentemente
            </h3>
            <p>
              Se eliminarán la cuenta, {snapshot.preview.memberships_count}{" "}
              membresías y {snapshot.preview.schedules_count} horarios tuyos.
            </p>
            {snapshot.preview.owned_rooms.map((room) => (
              <div
                key={room.room_id}
                className="rounded border border-slate-300 p-3"
              >
                <p className="font-semibold">
                  {room.name} · {room.members_count} integrantes
                </p>
                {room.requires_decision ? (
                  <label className="mt-2 block">
                    Decisión para {room.name}
                    <select
                      className={field}
                      name={room.room_id}
                      required
                      defaultValue=""
                    >
                      <option value="" disabled>
                        Elige una decisión
                      </option>
                      {room.candidates.map((candidate) => (
                        <option key={candidate.id} value={candidate.id}>
                          Transferir a {candidate.name} (
                          {candidate.role === "admin"
                            ? "administrador"
                            : "miembro"}
                          {candidate.id === room.suggested_new_owner_id
                            ? ", recomendado"
                            : ""}
                          )
                        </option>
                      ))}
                      <option value="close">
                        Cerrar sala y eliminar sus horarios
                      </option>
                    </select>
                  </label>
                ) : (
                  <p>La sala se cerrará al eliminar la cuenta.</p>
                )}
              </div>
            ))}
            <label className="block">
              Contraseña actual
              <input
                className={field}
                name="password"
                type="password"
                autoComplete="current-password"
                maxLength={128}
                required
              />
            </label>
            <label className="block">
              Escribe ELIMINAR para confirmar
              <input
                className={field}
                name="confirmation"
                pattern="ELIMINAR"
                autoComplete="off"
                required
              />
            </label>
            {error && (
              <p className="text-red-800" role="alert">
                {error}
              </p>
            )}
            <div className="flex flex-wrap gap-3">
              <button className={danger} disabled={pending} type="submit">
                {pending ? "Eliminando…" : "Eliminar permanentemente"}
              </button>
              <button
                className="rounded border px-4 py-2"
                type="button"
                disabled={pending}
                onClick={() => dialog.current?.close()}
              >
                Cancelar
              </button>
            </div>
          </form>
        )}
      </dialog>
    </section>
  );
}
