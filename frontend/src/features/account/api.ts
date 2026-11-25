import type { User } from "@/features/auth/api";
import { requestJson } from "@/shared/api/client";

type Candidate = { id: string; name: string; role: "member" | "admin" };

export type Preview = {
  memberships_count: number;
  schedules_count: number;
  owned_rooms: {
    room_id: string;
    name: string;
    members_count: number;
    requires_decision: boolean;
    suggested_new_owner_id: string | null;
    candidates: Candidate[];
  }[];
};

export type RoomAction =
  | { room_id: string; action: "close" }
  | { room_id: string; action: "transfer"; new_owner_id: string };

export function saveProfile(
  body: { name: string; email: string; current_password?: string },
  csrfToken: string,
) {
  return requestJson<User>("/users/me", { method: "PATCH", body, csrfToken });
}

export function savePassword(
  body: { current_password: string; new_password: string },
  csrfToken: string,
) {
  return requestJson<void>("/users/me/password", {
    method: "PUT",
    body,
    csrfToken,
  });
}

export async function readDeletionPreview() {
  let revision: string | null = null;
  const preview = await requestJson<Preview>("/users/me/deletion-preview", {
    onResponse: (response) => {
      revision = response.headers.get("ETag");
    },
  });
  if (!revision)
    throw new Error("No se pudo verificar el estado de las salas.");
  return { preview, revision };
}

export function removeAccount(
  body: {
    current_password: string;
    confirmation: string;
    room_actions: RoomAction[];
  },
  csrfToken: string,
  revision: string,
) {
  return requestJson<void>("/users/me/deletion", {
    method: "POST",
    body,
    csrfToken,
    ifMatch: revision,
  });
}
