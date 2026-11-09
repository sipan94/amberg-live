/** Angebote: current offers from local businesses (GET /offers). */
import { useInfiniteQuery } from "@tanstack/react-query";
import { router } from "expo-router";
import { FlatList, RefreshControl, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { OfferCard } from "@/components/cards";
import { AppText, ErrorState, Loading } from "@/components/ui";
import { t } from "@/i18n/de";
import { api } from "@/lib/api";
import type { Offer, Paged } from "@/lib/types";
import { space } from "@/theme";

export default function OffersScreen() {
  const insets = useSafeAreaInsets();
  const q = useInfiniteQuery({
    queryKey: ["offers"],
    queryFn: ({ pageParam, signal }) => api<Paged<Offer>>("/offers", { params: { seite: pageParam }, signal }),
    initialPageParam: 1,
    getNextPageParam: (last) => (last.has_next ? last.page + 1 : undefined),
  });

  const header = (
    <AppText variant="title" accessibilityRole="header" style={{ paddingHorizontal: space.lg, marginBottom: space.sm }}>
      {t.offers.title}
    </AppText>
  );
  if (q.isPending) return <View style={{ flex: 1, paddingTop: insets.top + space.md }}>{header}<Loading /></View>;
  if (q.isError) return <ErrorState message={q.error.message} onRetry={() => q.refetch()} />;

  return (
    <FlatList
      data={q.data.pages.flatMap((p) => p.items)}
      keyExtractor={(o) => String(o.id)}
      contentContainerStyle={{ paddingTop: insets.top + space.md, paddingBottom: space.xxl, gap: space.md }}
      ListHeaderComponent={header}
      ListEmptyComponent={<AppText muted style={{ paddingHorizontal: space.lg }}>{t.offers.empty}</AppText>}
      ListFooterComponent={q.isFetchingNextPage ? <Loading /> : undefined}
      onEndReached={() => q.hasNextPage && !q.isFetchingNextPage && q.fetchNextPage()}
      refreshControl={<RefreshControl refreshing={q.isRefetching && !q.isFetchingNextPage} onRefresh={() => void q.refetch()} />}
      renderItem={({ item }) => (
        <View style={{ paddingHorizontal: space.lg }}>
          <OfferCard item={item} onPress={() => router.push({ pathname: "/offers/[slug]", params: { slug: item.slug } })} />
        </View>
      )}
    />
  );
}
