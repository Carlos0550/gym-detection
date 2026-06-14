import { apiFetch } from "@/lib/api-client";
import type { AccessLogListResponse, VerifyFaceResponse } from "@/lib/types/api";

export async function verifyFace(
  gymId: string,
  frames: Blob[],
): Promise<VerifyFaceResponse> {
  const formData = new FormData();
  frames.forEach((frame, index) => {
    formData.append("frames", frame, `frame-${index}.jpg`);
  });

  return apiFetch<VerifyFaceResponse>(`/gyms/${gymId}/access/verify-face`, {
    method: "POST",
    body: formData,
  });
}

export async function listAccessLogs(
  gymId: string,
  params?: { limit?: number; offset?: number },
): Promise<AccessLogListResponse> {
  const search = new URLSearchParams();
  if (params?.limit) search.set("limit", String(params.limit));
  if (params?.offset) search.set("offset", String(params.offset));
  const query = search.toString();

  return apiFetch<AccessLogListResponse>(
    `/gyms/${gymId}/access/logs${query ? `?${query}` : ""}`,
  );
}
