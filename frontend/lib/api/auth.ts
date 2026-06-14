import { apiFetch, setToken } from "@/lib/api-client";
import type { MeResponse, TokenResponse } from "@/lib/types/api";

export async function login(email: string, password: string): Promise<TokenResponse> {
  const data = await apiFetch<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  setToken(data.access_token);
  return data;
}

export async function getMe(): Promise<MeResponse> {
  return apiFetch<MeResponse>("/auth/me");
}
