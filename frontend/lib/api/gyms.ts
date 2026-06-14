import { apiFetch, setToken } from "@/lib/api-client";
import type { GymOnboardingRequest, GymOnboardingResponse, GymResponse } from "@/lib/types/api";

export async function listGyms(): Promise<GymResponse[]> {
  return apiFetch<GymResponse[]>("/gyms");
}

export async function getGym(gymId: string): Promise<GymResponse> {
  return apiFetch<GymResponse>(`/gyms/${gymId}`);
}

export async function onboardGym(
  payload: GymOnboardingRequest,
): Promise<GymOnboardingResponse> {
  const data = await apiFetch<GymOnboardingResponse>("/gyms/public/onboarding", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  setToken(data.owner_access_token);
  return data;
}
