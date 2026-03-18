"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { PartnerSwitchResponse, User } from "@/lib/types";

interface AuthCtx {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<{ requires_2fa?: boolean; totp_token?: string }>;
  register: (email: string, password: string, companyName: string, accountType?: "company" | "partner") => Promise<void>;
  logout: () => Promise<void>;
  switchToClient: (switchResponse: PartnerSwitchResponse) => Promise<void>;
  exitClientContext: () => Promise<void>;
}

const AuthContext = createContext<AuthCtx | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    api.me()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  const login = async (email: string, password: string) => {
    const result = await api.login(email, password);
    if (result.requires_2fa) return result;
    setUser(await api.me());
    return result;
  };

  const register = async (email: string, password: string, companyName: string, accountType: "company" | "partner" = "company") => {
    await api.register(email, password, companyName, accountType);
    setUser(await api.me());
  };

  const logout = async () => {
    api.restorePartnerToken(); // clean up any client context
    await api.logout();
    setUser(null);
  };

  const switchToClient = async (switchResponse: PartnerSwitchResponse) => {
    api.activateClientContext(switchResponse);
    setUser(await api.me());
    router.push("/dashboard");
  };

  const exitClientContext = async () => {
    api.restorePartnerToken();
    setUser(await api.me());
    router.push("/partner/clients");
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, switchToClient, exitClientContext }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
