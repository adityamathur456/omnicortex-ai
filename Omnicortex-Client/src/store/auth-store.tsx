import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { login as loginRequest, register as registerRequest } from '@/api/auth';
import type { AuthSession, LoginPayload, RegisterPayload } from '@/types';
import {
  clearStoredSession,
  getStoredSession,
  setStoredSession,
} from '@/utils/storage';

type AuthContextValue = {
  session: AuthSession | null;
  isAuthenticated: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<AuthSession | null>(() => getStoredSession());

  const handleLogin = useCallback(async (payload: LoginPayload) => {
    const nextSession = await loginRequest(payload);
    setSession(nextSession);
    setStoredSession(nextSession);
  }, []);

  const handleRegister = useCallback(async (payload: RegisterPayload) => {
    await registerRequest(payload);
  }, []);

  const logout = useCallback(() => {
    setSession(null);
    clearStoredSession();
  }, []);

  const value = useMemo(
    () => ({
      session,
      isAuthenticated: Boolean(session?.accessToken),
      login: handleLogin,
      register: handleRegister,
      logout,
    }),
    [handleLogin, logout, session],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuth must be used within AuthProvider.');
  }

  return context;
}
