import { useQuery } from "@tanstack/react-query";
import { Link, Route, Routes } from "react-router-dom";

import { getJson } from "@/shared/api/client";
import { AccountHome } from "@/features/auth/AccountHome";
import { AuthPage } from "@/features/auth/AuthPage";
import { ProtectedRoute } from "@/features/auth/ProtectedRoute";

function StatusPage() {
  const health = useQuery({
    queryKey: ["health", "ready"],
    queryFn: ({ signal }) => getJson<{ status: "ok" }>("/health/ready", signal),
    retry: false,
  });

  const status = health.isPending
    ? "Comprobando servicios…"
    : health.isError
      ? "Servicios no disponibles."
      : "API y base de datos disponibles.";

  return (
    <main className="mx-auto max-w-2xl px-6 py-16">
      <h1 className="text-4xl font-bold text-slate-900">SRC</h1>
      <p className="mt-4 text-slate-700">
        Análisis de disponibilidad horaria académica.
      </p>
      <p role="status" className="mt-6 text-slate-800">
        {status}
      </p>
      <nav className="mt-6 flex gap-4" aria-label="Cuenta">
        <Link className="text-blue-800 underline" to="/login">
          Iniciar sesión
        </Link>
        <Link className="text-blue-800 underline" to="/register">
          Crear cuenta
        </Link>
      </nav>
    </main>
  );
}

export function App() {
  return (
    <Routes>
      <Route path="/" element={<StatusPage />} />
      <Route path="/login" element={<AuthPage key="login" mode="login" />} />
      <Route
        path="/register"
        element={<AuthPage key="register" mode="register" />}
      />
      <Route element={<ProtectedRoute />}>
        <Route path="/app/inicio" element={<AccountHome />} />
      </Route>
      <Route
        path="*"
        element={
          <main className="p-6">
            <h1>Página no encontrada</h1>
            <Link to="/">Volver a SRC</Link>
          </main>
        }
      />
    </Routes>
  );
}
