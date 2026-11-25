import { requestJson } from "@/shared/api/client";

export type Role = "owner" | "admin" | "member";
type ScheduleStatus = "missing" | "draft" | "confirmed";

export type Room = {
  id: string;
  name: string;
  description: string | null;
  code: string | null;
  current_user_role: Role;
  members_count: number;
  schedule_status: ScheduleStatus;
};

export type Member = {
  id: string;
  user_id: string;
  name: string;
  role: Role;
  schedule_status: ScheduleStatus;
};

export const roomKeys = {
  list: ["rooms"] as const,
  detail: (id: string) => ["rooms", id] as const,
  members: (id: string) => ["rooms", id, "members"] as const,
};

export const roles = {
  owner: "Propietario",
  admin: "Administrador",
  member: "Miembro",
};
export const schedules = {
  missing: "Sin horario",
  draft: "Borrador",
  confirmed: "Confirmado",
};

export function listRooms(signal?: AbortSignal) {
  return requestJson<Room[]>("/rooms", { signal });
}

export function readRoom(id: string, signal?: AbortSignal) {
  return requestJson<Room>(`/rooms/${id}`, { signal });
}

export function readMembers(id: string, signal?: AbortSignal) {
  return requestJson<{ members: Member[] }>(`/rooms/${id}/members`, { signal });
}

export function writeRoom<T>(
  path: string,
  method: "POST" | "PATCH" | "DELETE",
  csrfToken: string,
  body?: object,
) {
  return requestJson<T>(`/rooms${path}`, { method, csrfToken, body });
}
