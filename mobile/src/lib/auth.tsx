/**
 * Login state. The token lives in the phone's secure storage (iOS Keychain / Android Keystore),
 * never in plain app storage. If the server rejects it (password changed, account blocked,
 * expired after 90 days), the app logs out by itself.
 */
import * as SecureStore from "expo-secure-store";
import { Platform } from "react-native";
import { createContext, ReactNode, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { api, setAuthToken, setUnauthorizedHandler } from "./api";
import type { User } from "./types";

const TOKEN_KEY = "amberg_live_token";

type AuthState = {
  ready: boolean; // false while the stored token is being checked at start
  user: User | null;
  login: (email: string, password: string) => Promise<User>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
};

const AuthContext = createContext<AuthState | null>(null);

// SecureStore has no web version; the web preview just keeps the token in memory.
const store = {
  get: () => (Platform.OS === "web" ? Promise.resolve(null) : SecureStore.getItemAsync(TOKEN_KEY)),
  set: (v: string) => (Platform.OS === "web" ? Promise.resolve() : SecureStore.setItemAsync(TOKEN_KEY, v)),
  clear: () => (Platform.OS === "web" ? Promise.resolve() : SecureStore.deleteItemAsync(TOKEN_KEY)),
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);
  const [user, setUser] = useState<User | null>(null);

  const forget = useCallback(async () => {
    setAuthToken(null);
    setUser(null);
    await store.clear();
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(() => void forget());
    (async () => {
      const token = await store.get();
      if (token) {
        setAuthToken(token);
        try {
          setUser(await api<User>("/auth/me"));
        } catch {
          // 401 → handler above clears it. Offline → keep the token, try again later.
        }
      }
      setReady(true);
    })();
    return () => setUnauthorizedHandler(null);
  }, [forget]);

  const login = useCallback(async (email: string, password: string) => {
    const res = await api<{ token: string; user: User }>("/auth/login", {
      method: "POST",
      body: { email, password, device: `${Platform.OS} app` },
    });
    setAuthToken(res.token);
    await store.set(res.token);
    setUser(res.user);
    return res.user;
  }, []);

  const logout = useCallback(async () => {
    try {
      await api("/auth/logout", { method: "POST" });
    } catch {
      // Already invalid or offline – forget it locally anyway.
    }
    await forget();
  }, [forget]);

  const refresh = useCallback(async () => {
    setUser(await api<User>("/auth/me"));
  }, []);

  const value = useMemo(() => ({ ready, user, login, logout, refresh }), [ready, user, login, logout, refresh]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth outside AuthProvider");
  return ctx;
}
