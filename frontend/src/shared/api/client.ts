const baseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";
export const unauthorizedEvent = "src:unauthorized";

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type RequestOptions = {
  method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
  body?: object;
  signal?: AbortSignal;
  csrfToken?: string;
  ifMatch?: string;
  onResponse?: (response: Response) => void;
  notifyUnauthorized?: boolean;
};

export async function requestJson<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const headers = new Headers({ Accept: "application/json" });
  if (options.body) headers.set("Content-Type", "application/json");
  if (options.csrfToken) headers.set("X-CSRF-Token", options.csrfToken);
  if (options.ifMatch) headers.set("If-Match", options.ifMatch);

  const response = await fetch(`${baseUrl}${path}`, {
    method: options.method ?? "GET",
    body: options.body ? JSON.stringify(options.body) : undefined,
    credentials: "same-origin",
    headers,
    signal: options.signal,
  });
  if (!response.ok) {
    if (response.status === 401 && options.notifyUnauthorized !== false) {
      if (typeof window !== "undefined") {
        window.dispatchEvent(new Event(unauthorizedEvent));
      }
    }
    const payload = await response.json().catch(() => null);
    const message = payload?.error?.message;
    throw new ApiError(
      response.status,
      typeof message === "string"
        ? message
        : `La API respondió con HTTP ${response.status}`,
    );
  }
  options.onResponse?.(response);
  return (response.status === 204 ? undefined : await response.json()) as T;
}

export function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  return requestJson<T>(path, { signal });
}
