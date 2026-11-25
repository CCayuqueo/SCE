export const field = "src-field";
export const button = "src-primary";
export const danger =
  "rounded bg-red-800 px-4 py-2 font-medium text-white disabled:opacity-50";

export function errorMessage(error: unknown) {
  return error instanceof Error
    ? error.message
    : "No se pudo completar la solicitud.";
}
