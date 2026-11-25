import { useQuery } from "@tanstack/react-query";
import { Link, Outlet, useParams } from "react-router-dom";

import { readRoom, roomKeys } from "@/features/rooms/api";

export function AdminRoomRoute() {
  const { roomId = "" } = useParams();
  const room = useQuery({
    queryKey: roomKeys.detail(roomId),
    queryFn: ({ signal }) => readRoom(roomId, signal),
    retry: false,
  });
  if (room.isSuccess && room.data.current_user_role !== "member")
    return <Outlet />;

  return (
    <main className="mx-auto max-w-4xl px-6 py-12">
      <Link className="text-blue-800 underline" to="/app/salas">
        Volver a Mis salas
      </Link>
      {room.isPending ? (
        <p role="status" className="mt-4">
          Comprobando acceso…
        </p>
      ) : (
        <p role="alert" className="mt-4">
          {room.error?.message ??
            "Esta vista requiere permisos de administración en la sala."}
        </p>
      )}
    </main>
  );
}
