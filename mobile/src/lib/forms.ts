/**
 * Builds the multipart body for the website's forms. Same format as a browser form:
 * text fields as strings, ticked boxes as "y", unticked boxes left out, images as files.
 */
import { Platform } from "react-native";

import { api, ApiError } from "./api";

export type PickedImage = { uri: string; name: string; type: string; file?: File | null };
export type FieldErrors = Record<string, string[]>;

type Value = string | number | boolean | null | undefined;

export async function buildForm(fields: Record<string, Value>, images: Record<string, PickedImage | null> = {}): Promise<FormData> {
  const form = new FormData();
  for (const [key, value] of Object.entries(fields)) {
    if (value === true) form.append(key, "y");
    else if (value === false || value === null || value === undefined) continue;
    else form.append(key, String(value));
  }
  for (const [key, img] of Object.entries(images)) {
    if (!img) continue;
    if (Platform.OS === "web") {
      const blob = img.file ?? (await (await fetch(img.uri)).blob());
      form.append(key, blob, img.name);
    } else {
      // React Native's FormData sends {uri, name, type} as a real file upload.
      form.append(key, { uri: img.uri, name: img.name, type: img.type } as unknown as Blob);
    }
  }
  return form;
}

/** Sends a form; on failure returns the German messages (overall + per field) instead of throwing. */
export async function submitForm<T>(path: string, method: "POST" | "PUT", fields: Record<string, Value>, images?: Record<string, PickedImage | null>):
  Promise<{ ok: true; data: T } | { ok: false; error: string; fields: FieldErrors; code?: string }> {
  try {
    const data = await api<T>(path, { method, body: await buildForm(fields, images) });
    return { ok: true, data };
  } catch (e) {
    if (e instanceof ApiError) return { ok: false, error: e.message, fields: e.fields, code: e.code };
    throw e;
  }
}
