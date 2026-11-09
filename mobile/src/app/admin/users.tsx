/** Users: search, block / unblock (logs them out of the app at once), delete with all content. */
import { keepPreviousData, useInfiniteQuery, useQueryClient } from "@tanstack/react-query";
import { router, Stack } from "expo-router";
import { useEffect, useState } from "react";
import { FlatList, View } from "react-native";

import { confirm } from "@/components/admin";
import { SearchField } from "@/components/controls";
import { Notice, SmallButton } from "@/components/form";
import { AppText, Badge, Card, ErrorState, Loading, StatusBadge } from "@/components/ui";
import { t } from "@/i18n/de";
import { refreshAdmin } from "@/lib/admin";
import { api, ApiError } from "@/lib/api";
import type { AdminUser, Paged } from "@/lib/types";
import { space } from "@/theme";

const date = (iso: string | null) => (iso ? new Date(iso.endsWith("Z") ? iso : `${iso}Z`).toLocaleDateString("de-DE") : "–");

export default function UsersScreen() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [q, setQ] = useState("");
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    const id = setTimeout(() => setQ(search.trim()), 350);
    return () => clearTimeout(id);
  }, [search]);

  const list = useInfiniteQuery({
    queryKey: ["admin", "users", q],
    queryFn: ({ pageParam, signal }) => api<Paged<AdminUser>>("/admin/users", { params: { q, seite: pageParam }, signal }),
    initialPageParam: 1,
    getNextPageParam: (last) => (last.has_next ? last.page + 1 : undefined),
    placeholderData: keepPreviousData,
  });

  const run = async (fn: () => Promise<string>) => {
    try {
      setNotice(await fn());
    } catch (e) {
      setNotice(e instanceof ApiError ? e.message : t.errors.generic);
    }
    await refreshAdmin(queryClient);
  };

  return (
    <View style={{ flex: 1 }}>
      <Stack.Screen options={{ title: t.admin.users }} />
      <View style={{ paddingVertical: space.md, gap: space.sm }}>
        <SearchField value={search} onChangeText={setSearch} placeholder={t.admin.search} />
        {notice ? <View style={{ marginHorizontal: space.lg }}><Notice message={notice} /></View> : null}
      </View>
      {list.isPending ? <Loading /> : list.isError ? <ErrorState message={list.error.message} onRetry={() => list.refetch()} /> : (
        <FlatList
          data={list.data.pages.flatMap((p) => p.items)}
          keyExtractor={(u) => String(u.id)}
          contentContainerStyle={{ paddingHorizontal: space.lg, paddingBottom: space.xxl, gap: space.md }}
          keyboardShouldPersistTaps="handled"
          ListFooterComponent={list.isFetchingNextPage ? <Loading /> : undefined}
          onEndReached={() => list.hasNextPage && !list.isFetchingNextPage && list.fetchNextPage()}
          renderItem={({ item: u }) => (
            <Card style={{ padding: space.md, gap: 4 }}>
              <View style={{ flexDirection: "row", gap: 6, flexWrap: "wrap" }}>
                {u.is_admin ? <Badge kind="premium">Admin</Badge> : null}
                {u.is_me ? <Badge kind="neutral">{t.admin.you}</Badge> : null}
                {u.is_blocked ? <Badge kind="danger">{t.admin.blocked}</Badge> : null}
                {!u.is_verified ? <Badge kind="tip">{t.admin.unverified}</Badge> : null}
              </View>
              <AppText style={{ fontFamily: "SchibstedGrotesk_600SemiBold" }} selectable>{u.email}</AppText>
              <AppText variant="small" muted>{t.admin.lastLogin}: {date(u.last_login_at)}</AppText>
              {u.organizations.map((o) => (
                <View key={o.id} style={{ flexDirection: "row", gap: 6, alignItems: "center" }}>
                  <StatusBadge status={o.status} label={t.admin.status[o.status] ?? o.status} />
                  <AppText variant="small" style={{ flex: 1 }} numberOfLines={1}
                    onPress={() => router.push({ pathname: "/admin/item", params: { kind: "organization", id: String(o.id) } })}>{o.name}</AppText>
                </View>
              ))}
              {!u.is_me ? (
                <View style={{ flexDirection: "row", gap: space.sm, marginTop: space.sm }}>
                  <SmallButton icon={u.is_blocked ? "unlock" : "lock"} label={u.is_blocked ? t.admin.unblock : t.admin.block}
                    onPress={() => run(async () => ((await api<{ is_blocked: boolean }>(`/admin/users/${u.id}/block`, { method: "POST" })).is_blocked ? t.admin.blocked : t.admin.unblock))} />
                  <SmallButton icon="trash-2" label={t.admin.delete} danger onPress={() => confirm(t.admin.delete, t.admin.deleteUserConfirm(u.email), t.admin.delete,
                    () => void run(async () => (await api<{ message: string }>(`/admin/users/${u.id}`, { method: "DELETE" })).message))} />
                </View>
              ) : null}
            </Card>
          )}
        />
      )}
    </View>
  );
}
