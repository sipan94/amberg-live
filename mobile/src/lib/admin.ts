/** Admin actions (app/api/admin.py). Each one refreshes the admin screens afterwards. */
import { QueryClient } from "@tanstack/react-query";

import { api } from "./api";
import type { AdminKind } from "./types";

export const itemLabel = (i: { title?: string; name?: string }) => i.title ?? i.name ?? "";

export function refreshAdmin(queryClient: QueryClient) {
  return Promise.all([
    queryClient.invalidateQueries({ queryKey: ["admin"] }),
    queryClient.invalidateQueries({ queryKey: ["home"] }),
    queryClient.invalidateQueries({ queryKey: ["events"] }),
  ]);
}

export const adminApi = {
  approve: (kind: AdminKind, id: number) =>
    api<{ message: string; note: string | null }>(`/admin/${kind}/${id}/approve`, { method: "POST" }),
  reject: (kind: AdminKind, id: number, reason: string) =>
    api<{ message: string }>(`/admin/${kind}/${id}/reject`, { method: "POST", body: { reason } }),
  feature: (kind: AdminKind, id: number) =>
    api<{ is_featured: boolean }>(`/admin/${kind}/${id}/feature`, { method: "POST" }),
  premium: (orgId: number, until: string | null, off = false) =>
    api<{ is_premium: boolean; premium_until: string | null }>(`/admin/organization/${orgId}/premium`, {
      method: "POST", body: off ? { action: "off" } : { until: until ?? "" },
    }),
  remove: (kind: AdminKind, id: number) => api<{ message: string }>(`/admin/${kind}/${id}`, { method: "DELETE" }),
};
