import { useState, type FormEvent } from "react";
import { Link, Navigate } from "react-router-dom";

import { useAuth } from "./context";

const inputClass = "src-field";

export function AuthPage({ mode }: { mode: "login" | "register" }) {
  const auth = useAuth();
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const [confirmationPending, setConfirmationPending] = useState(false);
  const registering = mode === "register";
  const title = registering ? "Crear cuenta" : "Iniciar sesión";

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const email = String(form.get("email")).trim();
    const password = String(form.get("password"));
    const name = String(form.get("name") ?? "").trim();
    if (registering && name.length < 2) {
      setError("El nombre debe tener al menos dos caracteres.");
      return;
    }
    setPending(true);
    setError("");
    try {
      if (registering) {
        setConfirmationPending(
          !(await auth.register({ name, email, password })),
        );
      } else await auth.login({ email, password });
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "No se pudo completar la solicitud.",
      );
    } finally {
      setPending(false);
    }
  }

  if (auth.session) return <Navigate to="/app/inicio" replace />;

  return (
    <main className="mx-auto max-w-md px-6 py-16 text-slate-900">
      <Link to="/" className="font-bold text-blue-800">
        SRC
      </Link>
      <h1 className="mt-4 text-3xl font-bold">{title}</h1>
      {registering && confirmationPending ? (
        <p role="status" className="mt-6 text-slate-700">
          Revisa tu correo. Si recibes un enlace de confirmación, ábrelo y luego
          inicia sesión.
        </p>
      ) : (
        <form className="mt-6 space-y-4" onSubmit={submit}>
          {registering && (
            <label className="block">
              Nombre
              <input
                className={inputClass}
                name="name"
                autoComplete="name"
                minLength={2}
                maxLength={100}
                required
              />
            </label>
          )}
          <label className="block">
            Correo electrónico
            <input
              className={inputClass}
              name="email"
              type="email"
              autoComplete="email"
              maxLength={254}
              required
            />
          </label>
          <label className="block">
            Contraseña
            <input
              className={inputClass}
              name="password"
              type="password"
              autoComplete={registering ? "new-password" : "current-password"}
              minLength={registering ? 15 : 1}
              maxLength={128}
              aria-describedby={registering ? "password-help" : undefined}
              required
            />
            {registering && (
              <span id="password-help" className="text-sm text-slate-700">
                Usa al menos 15 caracteres.
              </span>
            )}
          </label>
          {error && (
            <p role="alert" className="text-red-800">
              {error}
            </p>
          )}
          <button type="submit" disabled={pending} className="src-primary">
            {pending ? "Enviando…" : title}
          </button>
        </form>
      )}
      <p className="mt-6">
        <Link
          className="text-blue-800 underline"
          to={registering ? "/login" : "/register"}
        >
          {registering ? "Ya tengo una cuenta" : "Crear una cuenta"}
        </Link>
      </p>
    </main>
  );
}
