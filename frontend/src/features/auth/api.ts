import { ApiError, requestJson } from "@/shared/api/client";

export type User = { id: string; name: string; email: string };
export type Credentials = { email: string; password: string };
export type Registration = Credentials & { name: string };
export type Session = { user: User; csrf_token: string };

export async function readSession(
  signal?: AbortSignal,
): Promise<Session | null> {
  try {
    return await requestJson<Session>("/auth/me", {
      signal,
      notifyUnauthorized: false,
    });
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) return null;
    throw error;
  }
}

export function signIn(body: Credentials): Promise<Session> {
  return requestJson<Session>("/auth/login", {
    method: "POST",
    body,
    notifyUnauthorized: false,
  });
}

export async function signUp(body: Registration): Promise<Session | null> {
  const user = await requestJson<User | null>("/auth/register", {
    method: "POST",
    body,
  });
  if (user === null) return null;
  const session = await readSession();
  if (!session) {
    throw new Error("No se pudo abrir la sesión. Prueba iniciar sesión.");
  }
  return session;
}

export function signOut(csrfToken: string): Promise<void> {
  return requestJson<void>("/auth/logout", { method: "POST", csrfToken });
}
