import { SchedulePage } from "@/features/schedules/SchedulePage";
import { RoomPage } from "@/features/rooms/RoomPage";
import { RoomsPage } from "@/features/rooms/RoomsPage";
import { Link, Route, Routes } from "react-router-dom";

import { AdminRoomRoute } from "@/features/overlap/AdminRoomRoute";
import { IndividualPage } from "@/features/overlap/IndividualPage";
import { OverlapPage } from "@/features/overlap/OverlapPage";

import { AppShell } from "@/app/AppShell";
import { GuidePage } from "@/features/guide/GuidePage";
import { Presentation } from "@/features/home/Presentation";
import { AccountHome } from "@/features/auth/AccountHome";
import { SettingsPage } from "@/features/account/SettingsPage";
import { AuthPage } from "@/features/auth/AuthPage";
import { ProtectedRoute } from "@/features/auth/ProtectedRoute";

export function App() {
  return (
    <Routes>
      <Route path="/" element={<Presentation />} />
      <Route path="/login" element={<AuthPage key="login" mode="login" />} />
      <Route
        path="/register"
        element={<AuthPage key="register" mode="register" />}
      />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route path="/app/guia" element={<GuidePage />} />
          <Route path="/app/inicio" element={<AccountHome />} />
          <Route path="/app/ajustes" element={<SettingsPage />} />
          <Route path="/app/salas" element={<RoomsPage />} />
          <Route path="/app/salas/:roomId" element={<RoomPage />} />
          <Route element={<AdminRoomRoute />}>
            <Route
              path="/app/salas/:roomId/superposicion"
              element={<OverlapPage />}
            />
            <Route
              path="/app/salas/:roomId/horarios"
              element={<IndividualPage />}
            />
          </Route>
          <Route
            path="/app/salas/:roomId/mi-horario"
            element={<SchedulePage />}
          />
        </Route>
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
