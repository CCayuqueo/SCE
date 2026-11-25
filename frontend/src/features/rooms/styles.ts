export const input = "mt-1 w-full rounded border border-slate-400 px-3 py-2";
export const action =
  "rounded bg-blue-700 px-4 py-2 font-medium text-white disabled:opacity-50";
export const destructive =
  "rounded border border-red-800 px-3 py-2 text-red-800 disabled:opacity-50";

export function errorMessage(error: unknown) {
  return error instanceof Error
    ? error.message
    : "No se pudo completar la solicitud.";
}
