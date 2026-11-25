const baseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

export async function getJson<T>(
  path: string,
  signal?: AbortSignal,
): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, {
    headers: { Accept: "application/json" },
    credentials: "same-origin",
    signal,
  });
  if (!response.ok) {
    throw new Error(`La API respondió con HTTP ${response.status}`);
  }
  return response.json() as Promise<T>;
}
