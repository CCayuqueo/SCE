import { roomKeys } from "@/features/rooms/api";
import type { Schedule } from "@/features/schedules/api";
import { getJson } from "@/shared/api/client";

export type Coordinate = { day: number; block: number };
type CellCounts = Coordinate & {
  weight: number;
  available_count: number;
  pending_count: number;
};
export type OverlapCell = CellCounts & {
  intensity: number;
  everyone_available: boolean;
};
export type MemberSummary = { id: string; name: string };
export type Overlap = {
  room_id: string;
  total_members: number;
  confirmed_members: number;
  pending_members: number;
  min_weight: number;
  max_weight: number;
  coverage: number;
  cells: OverlapCell[];
};
export type CellDetails = CellCounts & {
  total_members: number;
  occupied_members: MemberSummary[];
  available_members: MemberSummary[];
  pending_members: MemberSummary[];
};

export const overlapKeys = {
  group: (room: string) => [...roomKeys.detail(room), "overlap"] as const,
  cell: (room: string, cell: Coordinate | null) =>
    [
      ...roomKeys.detail(room),
      "overlap",
      "cell",
      cell?.day,
      cell?.block,
    ] as const,
  individual: (room: string, member: string) =>
    [...roomKeys.detail(room), "individual", member] as const,
};

export function readOverlap(room: string, signal?: AbortSignal) {
  return getJson<Overlap>(`/rooms/${room}/overlap`, signal);
}

export function readCell(
  room: string,
  { day, block }: Coordinate,
  signal?: AbortSignal,
) {
  return getJson<CellDetails>(
    `/rooms/${room}/overlap/cells/${day}/${block}`,
    signal,
  );
}

export function readIndividual(
  room: string,
  member: string,
  signal?: AbortSignal,
) {
  return getJson<Schedule>(`/rooms/${room}/members/${member}/schedule`, signal);
}
