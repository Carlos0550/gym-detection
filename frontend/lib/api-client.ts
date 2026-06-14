import { humanizeError } from "@/lib/errors";
import type { ApiError } from "@/lib/types/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
const TOKEN_KEY = "gym_detection_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
}

function handleUnauthorized(): void {
  clearToken();
  if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
    window.location.href = "/login?session=expired";
  }
}

function formatDetail(detail: unknown): string {
  let raw: string;
  if (typeof detail === "string") {
    raw = detail;
  } else if (Array.isArray(detail)) {
    raw = detail
      .map((item) => {
        if (typeof item === "object" && item !== null && "msg" in item) {
          return String((item as { msg: string }).msg);
        }
        return String(item);
      })
      .join(". ");
  } else {
    raw = "Error desconocido";
  }
  return humanizeError(raw);
}

export function formatApiError(
  detail: string,
  context?: "enroll" | "reception" | "general",
): string {
  return humanizeError(detail, context);
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...(init.body && !(init.body instanceof FormData)
      ? { "Content-Type": "application/json" }
      : {}),
    ...(init.headers as Record<string, string> | undefined),
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...init,
      headers,
    });
  } catch (err) {
    if (err instanceof TypeError) {
      const error: ApiError = {
        status: 0,
        detail: "Sin conexión. Revisá tu internet e intentá de nuevo.",
      };
      throw error;
    }
    throw err;
  }

  if (response.status === 401) {
    handleUnauthorized();
    const error: ApiError = { status: 401, detail: "Sesión expirada" };
    throw error;
  }

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const data = await response.json();
      detail = formatDetail(data.detail ?? detail);
    } catch {
      // ignore
    }
    const error: ApiError = { status: response.status, detail };
    throw error;
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export { API_URL };
