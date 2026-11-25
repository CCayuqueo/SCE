import { requestJson } from "@/shared/api/client";

export type Cell = { day: number; block: number; is_occupied: boolean };
export type Schedule = {
  schedule_id: string | null;
  status: "missing" | "draft" | "confirmed";
  version: number;
  blocks: Cell[];
};

const path = (room: string) => `/rooms/${room}/schedules/me`;
const versionTag = (schedule: Schedule) =>
  schedule.schedule_id
    ? `"${schedule.schedule_id}:${schedule.version}"`
    : undefined;
export const ownScheduleKey = (room: string) =>
  ["schedule", room, "me"] as const;

export async function getOwnSchedule(room: string, signal?: AbortSignal) {
  let maxBytes = 5 * 1024 ** 2;
  const schedule = await requestJson<Schedule>(path(room), {
    signal,
    onResponse: (response) => {
      const limit = Number(response.headers.get("X-Max-Upload-Bytes"));
      if (limit > 0) maxBytes = limit;
    },
  });
  return { schedule, maxBytes };
}

export function uploadSchedule(
  room: string,
  file: File,
  base: Schedule,
  csrfToken: string,
) {
  const form = new FormData();
  form.set("file", file);
  form.set("expected_version", String(base.version));
  return requestJson<Schedule>(path(room) + "/upload", {
    method: "POST",
    form,
    csrfToken,
    ifMatch: versionTag(base),
  });
}

export function confirmSchedule(
  room: string,
  base: Schedule,
  blocks: Cell[],
  csrfToken: string,
) {
  return requestJson<Schedule>(path(room), {
    method: "PUT",
    body: { expected_version: base.version, blocks },
    csrfToken,
    ifMatch: versionTag(base),
  });
}

export function deleteSchedule(
  room: string,
  base: Schedule,
  csrfToken: string,
) {
  return requestJson<void>(path(room), {
    method: "DELETE",
    csrfToken,
    ifMatch: versionTag(base),
  });
}
