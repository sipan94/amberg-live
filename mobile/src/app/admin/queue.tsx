/** Review queue: approve or reject new and changed entries (GET /admin/queue). */
import { keepPreviousData, useQuery, useQueryClient } from "@tanstack/react-query";
import { router, Stack, useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { RefreshControl, ScrollView, View } from "react-native";

import { AdminItemCard, RejectDialog } from "@/components/admin";
import { Segmented } from "@/components/controls";
import { Notice, SmallButton } from "@/components/form";
import { AppText, ErrorState, Loading } from "@/components/ui";
import { t } from "@/i18n/de";
import { adminApi, itemLabel, refreshAdmin } from "@/lib/admin";
import { api, ApiError } from "@/lib/api";
import type { AdminItem, AdminKind, AdminQueue } from "@/lib/types";
import { space } from "@/theme";

export default function QueueScreen() {
  const params = useLocalSearchParams<{ kind?: AdminKind }>();
  const [kind, setKind] = useState<AdminKind>(params.kind ?? "event");
  const [rejecting, setRejecting] = useState<AdminItem | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const q = useQuery({
    queryKey: ["admin", "queue", kind],
    queryFn: ({ signal }) => api<AdminQueue>("/admin/queue", { params: { kind }, signal }),
    placeholderData: keepPreviousData,
  });

  const run = async (fn: () => Promise<{ message?: string; note?: string | null }>) => {
    try {
      const res = await fn();
      setNotice([res.message, res.note].filter(Boolean).join(" ") || null);
    } catch (e) {
      setNotice(e instanceof ApiError ? e.message : t.errors.generic);
    }
    await refreshAdmin(queryClient);
  };

  const counts = q.data?.counts;
  const tab = (k: AdminKind) => `${t.admin.kinds[k]}${counts ? ` (${counts[k]})` : ""}`;

  return (
    <ScrollView contentContainerStyle={{ paddingVertical: space.lg, gap: space.md, paddingBottom: space.xxl * 2 }}
      refreshControl={<RefreshControl refreshing={q.isRefetching} onRefresh={() => void q.refetch()} />}>
      <Stack.Screen options={{ title: t.admin.review }} />
      <Segmented<AdminKind> value={kind} onChange={(k) => { setKind(k); setNotice(null); }}
        options={(["event", "offer", "organization"] as AdminKind[]).map((k) => ({ value: k, label: tab(k) }))} />
      {notice ? <View style={{ marginHorizontal: space.lg }}><Notice message={notice} /></View> : null}

      {q.isPending ? <Loading /> : q.isError ? <ErrorState message={q.error.message} onRetry={() => q.refetch()} /> : (
        q.data.items.length ? q.data.items.map((item) => (
          <View key={item.id} style={{ marginHorizontal: space.lg }}>
            <AdminItemCard item={item}>
              <SmallButton icon="more-horizontal" label={t.admin.details}
                onPress={() => router.push({ pathname: "/admin/item", params: { kind: item.kind, id: String(item.id) } })} />
              <SmallButton icon="check" label={t.admin.approve} onPress={() => run(() => adminApi.approve(item.kind, item.id))} />
              <SmallButton icon="x" label={t.admin.reject} onPress={() => setRejecting(item)} danger />
              {item.kind !== "organization" ? (
                <SmallButton icon="star" label={item.is_featured ? t.admin.tipOff : t.admin.tip}
                  onPress={() => run(async () => ({ message: (await adminApi.feature(item.kind, item.id)).is_featured ? t.admin.tipOn : t.admin.tipOff }))} />
              ) : null}
            </AdminItemCard>
          </View>
        )) : <AppText muted style={{ paddingHorizontal: space.lg }}>{t.admin.queueEmpty}</AppText>
      )}

      <RejectDialog
        visible={!!rejecting}
        label={rejecting ? itemLabel(rejecting) : ""}
        presets={q.data?.reject_presets ?? []}
        onClose={() => setRejecting(null)}
        onSend={async (reason) => {
          if (!rejecting) return null;
          try {
            const res = await adminApi.reject(rejecting.kind, rejecting.id, reason);
            setRejecting(null);
            setNotice(res.message);
            await refreshAdmin(queryClient);
            return null;
          } catch (e) {
            return e instanceof ApiError ? (e.fields.reason?.[0] ?? e.message) : t.errors.generic;
          }
        }}
      />
    </ScrollView>
  );
}
