/** All content, searchable and filterable by status (GET /admin/content/<kind>). */
import { keepPreviousData, useInfiniteQuery } from "@tanstack/react-query";
import { router, Stack } from "expo-router";
import { useEffect, useState } from "react";
import { FlatList, View } from "react-native";

import { AdminItemCard } from "@/components/admin";
import { Chip, ChipRow, SearchField, Segmented } from "@/components/controls";
import { AppText, ErrorState, Loading } from "@/components/ui";
import { t } from "@/i18n/de";
import { api } from "@/lib/api";
import type { AdminItem, AdminKind, Paged } from "@/lib/types";
import { space } from "@/theme";

export default function ContentScreen() {
  const [kind, setKind] = useState<AdminKind>("event");
  const [status, setStatus] = useState("");
  const [search, setSearch] = useState("");
  const [q, setQ] = useState("");

  useEffect(() => {
    const id = setTimeout(() => setQ(search.trim()), 350);
    return () => clearTimeout(id);
  }, [search]);

  const list = useInfiniteQuery({
    queryKey: ["admin", "content", kind, status, q],
    queryFn: ({ pageParam, signal }) => api<Paged<AdminItem>>(`/admin/content/${kind}`, { params: { status, q, seite: pageParam }, signal }),
    initialPageParam: 1,
    getNextPageParam: (last) => (last.has_next ? last.page + 1 : undefined),
    placeholderData: keepPreviousData,
  });

  return (
    <View style={{ flex: 1 }}>
      <Stack.Screen options={{ title: t.admin.content }} />
      <View style={{ gap: space.sm, paddingVertical: space.md }}>
        <Segmented<AdminKind> value={kind} onChange={setKind}
          options={(["event", "offer", "organization"] as AdminKind[]).map((k) => ({ value: k, label: t.admin.kinds[k] }))} />
        <SearchField value={search} onChangeText={setSearch} placeholder={t.admin.search} />
        <ChipRow>
          {["", "pending", "approved", "rejected"].map((s) => (
            <Chip key={s} label={s ? t.admin.status[s] : t.admin.allStatus} active={status === s} onPress={() => setStatus(s)} />
          ))}
        </ChipRow>
      </View>
      {list.isPending ? <Loading /> : list.isError ? <ErrorState message={list.error.message} onRetry={() => list.refetch()} /> : (
        <FlatList
          data={list.data.pages.flatMap((p) => p.items)}
          keyExtractor={(i) => `${i.kind}-${i.id}`}
          contentContainerStyle={{ paddingHorizontal: space.lg, paddingBottom: space.xxl, gap: space.md }}
          keyboardShouldPersistTaps="handled"
          ListHeaderComponent={<AppText variant="small" muted>{list.data.pages[0]?.total ?? 0}</AppText>}
          ListEmptyComponent={<AppText muted>{t.places.empty}</AppText>}
          ListFooterComponent={list.isFetchingNextPage ? <Loading /> : undefined}
          onEndReached={() => list.hasNextPage && !list.isFetchingNextPage && list.fetchNextPage()}
          renderItem={({ item }) => (
            <AdminItemCard item={item} onPress={() => router.push({ pathname: "/admin/item", params: { kind: item.kind, id: String(item.id) } })} />
          )}
        />
      )}
    </View>
  );
}
