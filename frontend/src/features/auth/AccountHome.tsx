import { useState } from "react";
import { Link } from "react-router-dom";

import { Team } from "@/features/home/Presentation";

import { useAuth } from "./context";

export function AccountHome() {
  const auth = useAuth();
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  async function logout() {
    setPending(true);
    setError("");
    try {
      await auth.logout();
    } catch (error) {
      setError(
        error instanceof Error ? error.message : "No se pudo cerrar la sesión.",
      );
    } finally {
      setPending(false);
    }
  }

  return (
    <main className="mx-auto max-w-2xl px-6 py-16 text-slate-900">
      <h1 className="text-3xl font-bold">Inicio</h1>
      <section className="src-card mt-5">
        <h2 className="text-3xl font-black">SRC</h2>
        <p className="mt-2">
          Comparte tus horarios académicos y encuentra la disponibilidad de tu
          grupo.
        </p>
        <p className="mt-2 text-slate-700">
          Sesión iniciada como {auth.session?.user.name}.
        </p>
        <div className="mt-5 flex flex-wrap gap-3">
          <Link className="src-primary" to="/app/salas?accion=crear">
            Crear sala
          </Link>
          <Link className="src-secondary" to="/app/salas?accion=unirse">
            Unirse a sala
          </Link>
        </div>
      </section>
      <Team />
      <button
        onClick={logout}
        disabled={pending}
        className="src-secondary mt-6"
      >
        {pending ? "Cerrando sesión…" : "Cerrar sesión"}
      </button>
      {error && (
        <p role="alert" className="mt-4 text-red-800">
          {error}
        </p>
      )}
    </main>
  );
}
