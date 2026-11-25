export const input = "src-field";
export const action = "src-primary";
export const destructive =
  "rounded border border-red-800 px-3 py-2 text-red-800 disabled:opacity-50";

export function errorMessage(error: unknown) {
  return error instanceof Error
    ? error.message
    : "No se pudo completar la solicitud.";
}
