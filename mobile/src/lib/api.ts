/**
 * Talks to the website's JSON API (/api/v1, see docs/API.md in the main project).
 *
 * Server address:
 *  - EXPO_PUBLIC_API_URL if set (production builds, e.g. https://amberg-live.de)
 *  - otherwise in development: the computer running `expo start`, port 5000 (Flask).
 *    The phone already reaches that computer for the JavaScript bundle, so we reuse its address.
 */
import Constants from "expo-constants";

import { t } from "@/i18n/de";

function devServer(): string {
  const host = Constants.expoConfig?.hostUri?.split(":")[0];
  return `http://${host || "localhost"}:5000`;
}

export const API_ROOT = (process.env.EXPO_PUBLIC_API_URL || devServer()).replace(/\/$/, "");
const BASE = `${API_ROOT}/api/v1`;

/** An error from the API: German message from the server, plus per-field errors on 422. */
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public fields: Record<string, string[]> = {},
    public code?: string,
  ) {
    super(message);
  }
}

let authToken: string | null = null;
let onUnauthorized: (() => void) | null = null;

export function setAuthToken(token: string | null) {
  authToken = token;
}

/** Called when the server says the token is no longer valid (password changed, blocked, expired). */
export function setUnauthorizedHandler(handler: (() => void) | null) {
  onUnauthorized = handler;
}

type Options = {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: unknown; // plain object → JSON, FormData → multipart (image uploads)
  params?: Record<string, string | number | undefined | null>;
  signal?: AbortSignal;
};

export async function api<T>(path: string, { method = "GET", body, params, signal }: Options = {}): Promise<T> {
  const query = params
    ? Object.entries(params)
        .filter(([, v]) => v !== undefined && v !== null && v !== "")
        .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
        .join("&")
    : "";
  const headers: Record<string, string> = { Accept: "application/json" };
  if (authToken) headers.Authorization = `Bearer ${authToken}`;

  let payload: BodyInit | undefined;
  if (body instanceof FormData) {
    payload = body; // fetch sets the multipart boundary itself
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  let res: Response;
  try {
    res = await fetch(`${BASE}${path}${query ? `?${query}` : ""}`, { method, headers, body: payload, signal });
  } catch (e) {
    if ((e as Error).name === "AbortError") throw e;
    throw new ApiError(t.errors.offline, 0);
  }

  const data = await res.json().catch(() => null);
  if (!res.ok) {
    if (res.status === 401 && authToken) onUnauthorized?.();
    throw new ApiError(data?.error || t.errors.generic, res.status, data?.fields || {}, data?.code);
  }
  return data as T;
}
