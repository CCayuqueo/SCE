import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { useAuth } from "@/features/auth/context";
import { savePassword, saveProfile } from "./api";
import { DeletionDialog } from "./DeletionDialog";
import { button, errorMessage, field } from "./forms";

export function SettingsPage() {
  const auth = useAuth();
  const [pending, setPending] = useState(false);
  const [notice, setNotice] = useState<{
    message: string;
    failed: boolean;
  } | null>(null);
  const user = auth.session?.user;
  const csrf = auth.session?.csrf_token;

  async function submit(
    event: FormEvent<HTMLFormElement>,
    change: "profile" | "password",
  ) {
    event.preventDefault();
    if (!csrf || pending) return;
    const element = event.currentTarget;
    const data = new FormData(element);
    setPending(true);
    setNotice(null);
    try {
      const current_password = String(data.get("current_password") ?? "");
      let message = "Contraseña actualizada. Se cerraron las demás sesiones.";
      if (change === "profile") {
        const requestedEmail = String(data.get("email")).trim().toLowerCase();
        const profile = await saveProfile(
          {
            name: String(data.get("name")),
            email: requestedEmail,
            current_password: current_password || undefined,
          },
          csrf,
        );
        message =
          profile.email === requestedEmail
            ? "Perfil actualizado."
            : "Perfil actualizado. Revisa tu correo para confirmar el cambio de dirección.";
        auth.retry();
      } else {
        await savePassword(
          { current_password, new_password: String(data.get("new_password")) },
          csrf,
        );
        element.reset();
      }
      const password = element.elements.namedItem("current_password");
      if (password instanceof HTMLInputElement) password.value = "";
      setNotice({ message, failed: false });
    } catch (error) {
      setNotice({ message: errorMessage(error), failed: true });
    } finally {
      setPending(false);
    }
  }

  if (!user || !csrf) return null;
  return (
    <main className="mx-auto max-w-xl px-6 py-12 text-slate-900">
      <Link to="/app/inicio" className="text-blue-800 underline">
        Volver a Inicio
      </Link>
      <h1 className="mb-6 mt-3 text-3xl font-bold">Ajustes</h1>
      {notice && (
        <p
          className={
            notice.failed ? "mb-4 text-red-800" : "mb-4 text-green-800"
          }
          role={notice.failed ? "alert" : "status"}
        >
          {notice.message}
        </p>
      )}
      <form
        className="space-y-3"
        onSubmit={(event) => void submit(event, "profile")}
      >
        <h2 className="text-xl font-semibold">Perfil</h2>
        <label className="block">
          Nombre
          <input
            className={field}
            name="name"
            autoComplete="name"
            defaultValue={user.name}
            minLength={2}
            maxLength={100}
            required
          />
        </label>
        <label className="block">
          Correo electrónico
          <input
            className={field}
            name="email"
            type="email"
            autoComplete="email"
            defaultValue={user.email}
            maxLength={254}
            required
          />
        </label>
        <label className="block">
          Contraseña actual para cambiar el correo
          <input
            className={field}
            name="current_password"
            type="password"
            autoComplete="current-password"
            maxLength={128}
          />
        </label>
        <button className={button} disabled={pending} type="submit">
          Guardar perfil
        </button>
      </form>
      <form
        className="mt-8 space-y-3"
        onSubmit={(event) => void submit(event, "password")}
      >
        <h2 className="text-xl font-semibold">Cambiar contraseña</h2>
        <label className="block">
          Contraseña actual
          <input
            className={field}
            name="current_password"
            type="password"
            autoComplete="current-password"
            maxLength={128}
            required
          />
        </label>
        <label className="block">
          Nueva contraseña
          <input
            className={field}
            name="new_password"
            type="password"
            autoComplete="new-password"
            minLength={15}
            maxLength={128}
            required
          />
        </label>
        <button className={button} disabled={pending} type="submit">
          Guardar contraseña
        </button>
      </form>
      <DeletionDialog csrf={csrf} onDeleted={auth.clearSession} />
    </main>
  );
}
