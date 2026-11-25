export const field = "mt-1 w-full rounded border border-slate-400 px-3 py-2";
export const button =
  "rounded bg-blue-700 px-4 py-2 font-medium text-white disabled:opacity-50";
export const danger =
  "rounded bg-red-800 px-4 py-2 font-medium text-white disabled:opacity-50";

export function errorMessage(error: unknown) {
  return error instanceof Error
    ? error.message
    : "No se pudo completar la solicitud.";
}
