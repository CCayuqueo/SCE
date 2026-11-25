import { createContext, useContext } from "react";

import type { Credentials, Registration, Session } from "./api";

type AuthState = {
  session: Session | null;
  checking: boolean;
  unavailable: boolean;
  retry: () => void;
  login: (credentials: Credentials) => Promise<void>;
  register: (registration: Registration) => Promise<void>;
  logout: () => Promise<void>;
  clearSession: () => Promise<void>;
};

export const AuthContext = createContext<AuthState | null>(null);

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("AuthProvider es obligatorio");
  return context;
}
