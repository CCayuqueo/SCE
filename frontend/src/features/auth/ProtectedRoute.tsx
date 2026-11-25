import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "./context";

export function ProtectedRoute() {
  const auth = useAuth();
  if (auth.checking) {
    return (
      <p className="p-6" role="status">
        Comprobando sesión…
      </p>
    );
  }
  if (auth.unavailable) {
    return (
      <main className="p-6">
        <p role="alert">No se pudo comprobar la sesión.</p>
        <button className="mt-2 underline" onClick={auth.retry}>
          Reintentar
        </button>
      </main>
    );
  }
  return auth.session ? <Outlet /> : <Navigate to="/login" replace />;
}
