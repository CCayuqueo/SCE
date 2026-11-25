import { Link } from "react-router-dom";

import example from "./assets/ejemplo-horario.png";

export function GuidePage() {
  return (
    <main className="mx-auto max-w-4xl space-y-6 px-6 py-12">
      <header>
        <h1 className="text-3xl font-bold">Guía / Cómo usar</h1>
        <p className="mt-2 text-slate-700">
          Comparte tu horario semanal y consulta la disponibilidad de tu grupo.
        </p>
      </header>
      <section className="src-card">
        <h2 className="text-xl font-semibold">
          1. Crea una cuenta y entra a una sala
        </h2>
        <p className="mt-2">
          Regístrate e inicia sesión. En{" "}
          <Link className="text-blue-800 underline" to="/app/salas">
            Salas
          </Link>
          , crea una sala para obtener un código o selecciona{" "}
          <strong>Unirse a sala</strong> e ingresa el código compartido.
        </p>
      </section>
      <section className="src-card">
        <h2 className="text-xl font-semibold">2. Carga una captura completa</h2>
        <p className="mt-2">
          En <strong>Mi horario</strong>, selecciona una captura y revisa la
          vista previa antes de cargarla. Usa preferentemente PNG. También se
          admite JPEG si conserva las líneas de la tabla.
        </p>
        <figure className="mt-4">
          <img
            src={example}
            alt="Captura compatible con encabezado azul, columnas de lunes a domingo y diez filas de horarios"
            width={707}
            height={259}
            className="h-auto max-w-full rounded border border-slate-300"
          />
          <figcaption className="mt-2 text-sm text-slate-700">
            Deja visibles las siete columnas y los diez bloques. La leyenda
            inferior es opcional.
          </figcaption>
        </figure>
      </section>
      <section className="src-card">
        <h2 className="text-xl font-semibold">
          3. Corrige y confirma el horario
        </h2>
        <p className="mt-2">
          La captura crea un borrador de 70 celdas. Selecciona una celda para
          alternar entre libre y ocupada. Usa <strong>Descartar cambios</strong>{" "}
          si quieres volver a la versión guardada o{" "}
          <strong>Guardar y confirmar</strong> para aportar tu disponibilidad a
          la sala.
        </p>
      </section>
      <section className="src-card">
        <h2 className="text-xl font-semibold">4. Lee la superposición</h2>
        <p className="mt-2">
          Propietarios y administradores pueden abrir{" "}
          <strong>Superposición</strong>. El número de un bloque indica cuántos
          integrantes confirmados están ocupados. El color representa esa
          cantidad dividida por el total de integrantes. Pulsa un bloque para
          ver las listas de ocupados, disponibles y pendientes.
        </p>
        <p className="mt-2">
          El peso cero solo significa disponibilidad total cuando todos
          confirmaron. En <strong>Horarios individuales</strong> puedes entrar
          al horario confirmado de un integrante en solo lectura.
        </p>
      </section>
      <section className="src-card">
        <h2 className="text-xl font-semibold">5. Administra la sala</h2>
        <p className="mt-2">
          En <strong>Integrantes</strong>, el propietario o un administrador
          puede promover miembros. El propietario también puede revocar roles,
          transferir la propiedad, expulsar integrantes o cerrar la sala.
        </p>
      </section>
      <section className="src-card">
        <h2 className="text-xl font-semibold">Problemas frecuentes</h2>
        <dl className="mt-3 space-y-3">
          <div>
            <dt className="font-semibold">La captura no se pudo leer.</dt>
            <dd>
              Captura la tabla completa en PNG con zoom normal y vuelve a
              cargarla.
            </dd>
          </div>
          <div>
            <dt className="font-semibold">El código no funciona.</dt>
            <dd>
              Comprueba sus 12 caracteres con un administrador de la sala.
            </dd>
          </div>
          <div>
            <dt className="font-semibold">No aparezco en la disponibilidad.</dt>
            <dd>Abre Mi horario y confirma el borrador.</dd>
          </div>
          <div>
            <dt className="font-semibold">El horario cambió.</dt>
            <dd>Recarga la última versión antes de repetir tus ajustes.</dd>
          </div>
        </dl>
      </section>
    </main>
  );
}
