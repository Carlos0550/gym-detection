import { apiFetch } from "@/lib/api-client";
import type {
  CreateGymUserPayload,
  GymClient,
  UpdateGymUserPayload,
} from "@/lib/types/api";

export async function listGymClients(gymId: string): Promise<GymClient[]> {
  return apiFetch<GymClient[]>(`/gyms/${gymId}/users`);
}

export async function createGymUser(
  gymId: string,
  payload: CreateGymUserPayload,
): Promise<GymClient> {
  return apiFetch<GymClient>(`/gyms/${gymId}/users`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateGymUser(
  gymId: string,
  userId: string,
  payload: UpdateGymUserPayload,
): Promise<GymClient> {
  return apiFetch<GymClient>(`/gyms/${gymId}/users/${userId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}
