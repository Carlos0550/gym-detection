"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getMe } from "@/lib/api/auth";
import { listGyms } from "@/lib/api/gyms";
import { clearToken, getToken } from "@/lib/api-client";
import type { GymMembership, MeResponse } from "@/lib/types/api";

const GYM_KEY = "gym_detection_gym_id";

type AuthContextValue = {
  user: MeResponse | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  logout: () => void;
  refetch: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const hasToken = typeof window !== "undefined" && !!getToken();

  const { data, isLoading } = useQuery({
    queryKey: ["auth", "me"],
    queryFn: getMe,
    enabled: hasToken,
    retry: false,
  });

  const logout = useCallback(() => {
    clearToken();
    queryClient.clear();
    window.location.href = "/login";
  }, [queryClient]);

  const value = useMemo(
    () => ({
      user: data ?? null,
      isLoading: hasToken && isLoading,
      isAuthenticated: !!data,
      logout,
      refetch: () => {
        void queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
      },
    }),
    [data, hasToken, isLoading, logout, queryClient],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de AuthProvider");
  return ctx;
}

type GymContextValue = {
  gymId: string | null;
  setGymId: (id: string) => void;
  manageableGyms: MeResponse["memberships"];
};

const GymContext = createContext<GymContextValue | null>(null);

export function GymProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const [gymId, setGymIdState] = useState<string | null>(null);

  const { data: gyms = [] } = useQuery({
    queryKey: ["gyms"],
    queryFn: listGyms,
    enabled: !!user,
  });

  const manageableGyms: GymMembership[] = useMemo(() => {
    if (!user) return [];

    if (user.is_superadmin) {
      return gyms.map((gym) => ({
        gym_id: gym.id,
        gym_name: gym.name,
        role: "owner",
      }));
    }

    return user.memberships.filter((m) => ["owner", "manager"].includes(m.role));
  }, [user, gyms]);

  useEffect(() => {
    if (manageableGyms.length === 0) {
      setGymIdState(null);
      return;
    }

    const stored = localStorage.getItem(GYM_KEY);
    const valid = manageableGyms.some((g) => g.gym_id === stored);
    setGymIdState(valid ? stored : manageableGyms[0].gym_id);
  }, [manageableGyms]);

  const setGymId = useCallback((id: string) => {
    localStorage.setItem(GYM_KEY, id);
    setGymIdState(id);
  }, []);

  const value = useMemo(
    () => ({ gymId, setGymId, manageableGyms }),
    [gymId, setGymId, manageableGyms],
  );

  return <GymContext.Provider value={value}>{children}</GymContext.Provider>;
}

export function useGym() {
  const ctx = useContext(GymContext);
  if (!ctx) throw new Error("useGym debe usarse dentro de GymProvider");
  return ctx;
}
