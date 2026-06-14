import { apiFetch } from "@/lib/api-client";
import type { FaceEmbedding, FaceEnrollResponse } from "@/lib/types/api";

export async function listFaceEmbeddings(
  gymId: string,
  userId: string,
): Promise<FaceEmbedding[]> {
  return apiFetch<FaceEmbedding[]>(`/gyms/${gymId}/users/${userId}/face`);
}

export async function validateEnrollPose(
  gymId: string,
  userId: string,
  step: "center" | "left" | "right",
  imageBlob: Blob,
): Promise<void> {
  const formData = new FormData();
  formData.append("step", step);
  formData.append("image", imageBlob, "pose.jpg");

  await apiFetch(`/gyms/${gymId}/users/${userId}/face/enroll/validate-pose`, {
    method: "POST",
    body: formData,
  });
}

export async function enrollFace(
  gymId: string,
  userId: string,
  frames: Blob[],
): Promise<FaceEnrollResponse> {
  const formData = new FormData();
  frames.forEach((frame, index) => {
    formData.append("frames", frame, `frame-${index}.jpg`);
  });

  return apiFetch<FaceEnrollResponse>(`/gyms/${gymId}/users/${userId}/face/enroll`, {
    method: "POST",
    body: formData,
  });
}
