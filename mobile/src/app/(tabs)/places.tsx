/** Orte: local businesses and clubs (GET /organizations). */
import { keepPreviousData, useInfiniteQuery } from "@tanstack/react-query";
import { Image } from "expo-image";
import { router } from "expo-router";
import { useEffect, useState } from "react";
import { FlatList, RefreshControl, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { SearchField, Segmented } from "@/components/controls";
import { AppText, Badge, Card, ErrorState, Icon, Loading } from "@/components/ui";
import { t } from "@/i18n/de";
import { api } from "@/lib/api";
import type { OrgListItem, Paged } from "@/lib/types";
import { radius, space, useTheme } from "@/theme";

type Typ = "" | "geschaefte" | "vereine";

export default function PlacesScreen() {
  const insets = useSafeAreaInsets();
  const [typ, setTyp] = useState<Typ>("");
  const [search, setSearch] = useState("");
  const [q, setQ] = useState("");

  useEffect(() => {
    const id = setTimeout(() => setQ(search.trim()), 350);
    return () => clearTimeout(id);
  }, [search]);

  const list = useInfiniteQuery({
    queryKey: ["organizations", typ, q],
    queryFn: ({ pageParam, signal }) => api<Paged<OrgListItem>>("/organizations", { params: { typ, q, seite: pageParam }, signal }),
    initialPageParam: 1,
    getNextPageParam: (last) => (last.has_next ? last.page + 1 : undefined),
    placeholderData: keepPreviousData,
  });

  return (
    <View style={{ flex: 1, paddingTop: insets.top + space.md }}>
      <AppText variant="title" accessibilityRole="header" style={{ paddingHorizontal: space.lg, marginBottom: space.md }}>
        {t.places.title}
      </AppText>
      <Segmented<Typ>
        value={typ}
        onChange={setTyp}
        options={[{ value: "", label: t.places.all }, { value: "geschaefte", label: t.places.businesses }, { value: "vereine", label: t.places.clubs }]}
      />
      <View style={{ paddingVertical: space.md }}>
        <SearchField value={search} onChangeText={setSearch} placeholder={t.places.search} />
      </View>
      {list.isPending ? (
        <Loading />
      ) : list.isError ? (
        <ErrorState message={list.error.message} onRetry={() => list.refetch()} />
      ) : (
        <FlatList
          data={list.data.pages.flatMap((p) => p.items)}
          keyExtractor={(o) => String(o.id)}
          contentContainerStyle={{ paddingBottom: space.xxl, gap: space.sm }}
          keyboardShouldPersistTaps="handled"
          ListEmptyComponent={<AppText muted style={{ paddingHorizontal: space.lg }}>{t.places.empty}</AppText>}
          ListFooterComponent={list.isFetchingNextPage ? <Loading /> : undefined}
          onEndReached={() => list.hasNextPage && !list.isFetchingNextPage && list.fetchNextPage()}
          refreshControl={<RefreshControl refreshing={list.isRefetching && !list.isFetchingNextPage} onRefresh={() => void list.refetch()} />}
          renderItem={({ item }) => <PlaceRow item={item} />}
        />
      )}
    </View>
  );
}

function PlaceRow({ item }: { item: OrgListItem }) {
  const theme = useTheme();
  return (
    <Card highlight={item.is_premium} style={{ marginHorizontal: space.lg }}
      onPress={() => router.push({ pathname: "/places/[slug]", params: { slug: item.slug } })}>
      <View style={{ flexDirection: "row", gap: space.md, padding: space.md, alignItems: "center" }}>
        <View style={{ width: 52, height: 52, borderRadius: radius.md, overflow: "hidden", backgroundColor: theme.dark ? "#34302b" : "#eeece7", alignItems: "center", justifyContent: "center" }}>
          {item.logo ? (
            <Image source={{ uri: item.logo.small }} style={{ width: 52, height: 52 }} contentFit="cover" />
          ) : (
            <Icon name={item.type === "club" ? "flag" : "shopping-bag"} size={22} color={theme.textMuted} />
          )}
        </View>
        <View style={{ flex: 1, gap: 3 }}>
          <View style={{ flexDirection: "row", gap: 6, flexWrap: "wrap" }}>
            <Badge kind="neutral">{item.type_label}</Badge>
            {item.is_premium ? <Badge kind="premium">{t.badges.premium}</Badge> : null}
          </View>
          <AppText variant="body" style={{ fontFamily: "SchibstedGrotesk_600SemiBold" }} numberOfLines={1}>{item.name}</AppText>
          {item.summary ? <AppText variant="small" muted numberOfLines={2}>{item.summary}</AppText> : null}
        </View>
        <Icon name="chevron-right" size={18} color={theme.textMuted} />
      </View>
    </Card>
  );
}
