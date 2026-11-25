import { useState } from "react";
import { Link } from "react-router-dom";

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
      <p className="mt-4">Sesión iniciada como {auth.session?.user.name}.</p>
      <Link to="/app/ajustes" className="mt-6 block text-blue-800 underline">
        Ajustes
      </Link>
      <button
        onClick={logout}
        disabled={pending}
        className="mt-6 rounded bg-blue-700 px-4 py-2 font-medium text-white disabled:opacity-60"
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
