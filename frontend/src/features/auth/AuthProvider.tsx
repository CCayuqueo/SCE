import {
  useQuery,
  useQueryClient,
  type QueryClient,
} from "@tanstack/react-query";
import { useEffect, type ReactNode } from "react";

import { unauthorizedEvent } from "@/shared/api/client";
import { readSession, signIn, signOut, signUp, type Session } from "./api";
import { AuthContext } from "./context";

const sessionKey = ["auth", "session"] as const;

function clearAccountQueries(client: QueryClient) {
  client.removeQueries({
    predicate: ({ queryKey }) => queryKey[0] !== sessionKey[0],
  });
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: sessionKey,
    queryFn: ({ signal }) => readSession(signal),
    retry: false,
  });

  useEffect(() => {
    function onUnauthorized() {
      void queryClient.cancelQueries();
      queryClient.setQueryData(sessionKey, null);
      clearAccountQueries(queryClient);
    }

    window.addEventListener(unauthorizedEvent, onUnauthorized);
    return () => window.removeEventListener(unauthorizedEvent, onUnauthorized);
  }, [queryClient]);

  useEffect(() => {
    // Una restauración que recibe 401 también invalida los datos privados.
    if (query.data === null) clearAccountQueries(queryClient);
  }, [query.data, queryClient]);

  async function setSession(session: Session | null) {
    await queryClient.cancelQueries();
    clearAccountQueries(queryClient);
    queryClient.setQueryData(sessionKey, session);
  }

  return (
    <AuthContext.Provider
      value={{
        session: query.data ?? null,
        checking: query.isPending,
        unavailable: query.isError,
        retry: () => void query.refetch(),
        clearSession: () => setSession(null),
        login: async (credentials) => setSession(await signIn(credentials)),
        register: async (registration) => {
          const session = await signUp(registration);
          if (session) await setSession(session);
          return session !== null;
        },
        logout: async () => {
          if (!query.data) return;
          await signOut(query.data.csrf_token);
          await setSession(null);
        },
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
