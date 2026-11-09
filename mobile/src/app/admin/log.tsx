/** Log of all admin actions (GET /admin/log). */
import { useInfiniteQuery } from "@tanstack/react-query";
import { Stack } from "expo-router";
import { FlatList, View } from "react-native";

import { AppText, Card, ErrorState, Loading } from "@/components/ui";
import { t } from "@/i18n/de";
import { api } from "@/lib/api";
import type { LogEntry, Paged } from "@/lib/types";
import { space } from "@/theme";

const when = (iso: string) => new Date(iso.endsWith("Z") ? iso : `${iso}Z`)
  .toLocaleString("de-DE", { day: "2-digit", month: "2-digit", year: "2-digit", hour: "2-digit", minute: "2-digit" });

export default function LogScreen() {
  const list = useInfiniteQuery({
    queryKey: ["admin", "log"],
    queryFn: ({ pageParam, signal }) => api<Paged<LogEntry>>("/admin/log", { params: { seite: pageParam }, signal }),
    initialPageParam: 1,
    getNextPageParam: (last) => (last.has_next ? last.page + 1 : undefined),
  });

  if (list.isPending) return <Loading />;
  if (list.isError) return <ErrorState message={list.error.message} onRetry={() => list.refetch()} />;

  return (
    <View style={{ flex: 1 }}>
      <Stack.Screen options={{ title: t.admin.log }} />
      <FlatList
        data={list.data.pages.flatMap((p) => p.items)}
        keyExtractor={(e, i) => `${e.at}-${i}`}
        contentContainerStyle={{ padding: space.lg, gap: space.sm, paddingBottom: space.xxl }}
        ListFooterComponent={list.isFetchingNextPage ? <Loading /> : undefined}
        onEndReached={() => list.hasNextPage && !list.isFetchingNextPage && list.fetchNextPage()}
        renderItem={({ item: e }) => (
          <Card style={{ padding: space.md, gap: 2 }}>
            <AppText variant="label" muted>{when(e.at)} · {e.admin}</AppText>
            <AppText><AppText style={{ fontFamily: "SchibstedGrotesk_600SemiBold" }}>{e.action}</AppText> · {e.type}</AppText>
            <AppText variant="small" selectable>{e.label}</AppText>
            {e.reason ? <AppText variant="small" muted selectable>{e.reason}</AppText> : null}
          </Card>
        )}
      />
    </View>
  );
}
