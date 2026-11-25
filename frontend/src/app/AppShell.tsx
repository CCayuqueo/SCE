import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";

const navStyle = ({ isActive }: { isActive: boolean }) =>
  `block rounded-md px-3 py-2 font-medium ${isActive ? "bg-white text-slate-950" : "text-slate-100 hover:bg-white/10"}`;

export function AppShell() {
  const [menu, setMenu] = useState(false);

  return (
    <div className="min-h-dvh lg:grid lg:grid-cols-[15rem_minmax(0,1fr)]">
      <a
        href="#app-content"
        className="sr-only z-10 focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:rounded focus:bg-white focus:p-3"
      >
        Saltar al contenido
      </a>
      <aside className="self-start bg-[#172333] text-white lg:sticky lg:top-0 lg:flex lg:h-dvh lg:flex-col">
        <div className="flex items-center justify-between p-4 lg:p-6">
          <NavLink
            to="/app/inicio"
            className="text-2xl font-black tracking-wide"
            onClick={() => setMenu(false)}
          >
            SRC
          </NavLink>
          <button
            type="button"
            className="rounded border border-white/60 px-3 py-2 lg:hidden"
            aria-expanded={menu}
            aria-controls="app-navigation"
            onClick={() => setMenu(!menu)}
          >
            {menu ? "Cerrar menú" : "Abrir menú"}
          </button>
        </div>
        <nav
          id="app-navigation"
          aria-label="Navegación principal"
          className={`${menu ? "flex" : "hidden"} flex-1 flex-col gap-1 px-4 pb-4 lg:flex`}
        >
          <NavLink
            to="/app/inicio"
            className={navStyle}
            onClick={() => setMenu(false)}
          >
            Inicio
          </NavLink>
          <NavLink
            to="/app/salas"
            className={navStyle}
            onClick={() => setMenu(false)}
          >
            Salas
          </NavLink>
          <NavLink
            to="/app/ajustes"
            className={navStyle}
            onClick={() => setMenu(false)}
          >
            Ajustes
          </NavLink>
          <div className="mt-3 border-t border-white/30 pt-3 lg:mt-auto">
            <NavLink
              to="/app/guia"
              className={navStyle}
              onClick={() => setMenu(false)}
            >
              Guía / Cómo usar
            </NavLink>
          </div>
        </nav>
      </aside>
      <div id="app-content" tabIndex={-1} className="min-w-0">
        <Outlet />
      </div>
    </div>
  );
}
