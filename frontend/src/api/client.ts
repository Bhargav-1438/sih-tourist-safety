/**
 * Central fetch client for the SIH Tourist Safety backend.
 *
 * - Base URL comes from VITE_API_BASE_URL (see .env.example).
 * - GET/POST helpers parse JSON and throw a typed ApiError on non-2xx.
 */

const BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ??
  "http://localhost:8000";

export class ApiError extends Error {
  readonly status: number;
  /** Parsed `detail` from FastAPI when available (string or validation array). */
  readonly detail: unknown;

  constructor(status: number, detail: unknown) {
    const message =
      typeof detail === "string" && detail.length > 0
        ? detail
        : `Request failed with status ${status}`;
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

function buildQueryString(params?: object): string {
  if (!params) return "";
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) search.set(key, String(value));
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      headers: { Accept: "application/json", ...init?.headers },
      ...init,
    });
  } catch (cause) {
    throw new Error(
      `Network error while calling ${path}. Is the backend running at ${BASE_URL}?`,
      { cause },
    );
  }

  if (!response.ok) {
    let detail: unknown = null;
    try {
      detail = await response.json();
    } catch {
      // Non-JSON error body; keep detail null.
    }
    throw new ApiError(response.status, detail ?? response.statusText);
  }

  return (await response.json()) as T;
}

export function apiGet<T>(
  path: string,
  params?: object,
): Promise<T> {
  return request<T>(`${path}${buildQueryString(params)}`);
}

/** POST with a JSON body. Omit `body` for endpoints that take no payload. */
export function apiPost<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: "POST",
    headers:
      body === undefined
        ? { Accept: "application/json" }
        : { Accept: "application/json", "Content-Type": "application/json" },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
}
