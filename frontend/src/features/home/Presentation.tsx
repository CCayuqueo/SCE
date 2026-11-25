import { Link } from "react-router-dom";

export function Team() {
  return (
    <section
      className="mt-10 rounded-xl border border-slate-200 bg-white p-5 sm:p-6"
      aria-labelledby="team-title"
    >
      <h2 id="team-title" className="text-xl font-semibold">
        Equipo desarrollador
      </h2>
      <p className="mt-2 text-slate-700">
        Créditos de autoría pendientes de confirmación.
      </p>
    </section>
  );
}

export function Presentation() {
  return (
    <main className="mx-auto max-w-5xl px-6 py-12 sm:py-20">
      <section
        className="rounded-2xl bg-[#172333] px-6 py-12 text-white sm:px-12"
        aria-labelledby="public-title"
      >
        <h1
          id="public-title"
          className="text-5xl font-black tracking-tight sm:text-7xl"
        >
          SRC
        </h1>
        <p className="mt-5 max-w-2xl text-2xl font-semibold">
          Encuentra disponibilidad común a partir de horarios académicos.
        </p>
        <p className="mt-3 max-w-xl text-slate-200">
          Crea una sala, confirma tus bloques y consulta la disponibilidad de tu
          grupo.
        </p>
        <nav className="mt-7 flex flex-wrap gap-3" aria-label="Cuenta">
          <Link className="src-primary" to="/register">
            Crear cuenta
          </Link>
          <Link
            className="rounded-md border border-slate-300 px-4 py-2 font-medium"
            to="/login"
          >
            Iniciar sesión
          </Link>
        </nav>
      </section>
      <div className="mt-7 grid gap-4 sm:grid-cols-3">
        {[
          ["Salas", "Crea una sala o entra con el código del grupo."],
          [
            "Mi horario",
            "Carga una captura y revisa los bloques antes de confirmar.",
          ],
          [
            "Superposición",
            "Compara los horarios confirmados e identifica quién está disponible.",
          ],
        ].map(([title, summary]) => (
          <section
            key={title}
            className="rounded-xl border border-slate-200 bg-white p-5"
          >
            <h2 className="text-lg font-semibold">{title}</h2>
            <p className="mt-2 text-slate-700">{summary}</p>
          </section>
        ))}
      </div>
      <Team />
    </main>
  );
}
