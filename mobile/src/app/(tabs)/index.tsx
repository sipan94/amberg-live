/** Start screen: today, the weekend, upcoming events and current offers (GET /home). */
import { useQuery } from "@tanstack/react-query";
import { router } from "expo-router";
import { FlatList, RefreshControl, ScrollView, useWindowDimensions, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { EventCard, EventRow, OfferCard } from "@/components/cards";
import { AppText, ErrorState, Loading, Section } from "@/components/ui";
import { t } from "@/i18n/de";
import { api, ApiError } from "@/lib/api";
import type { HomeData, Occurrence, Offer } from "@/lib/types";
import { flag, gold, space, useTheme } from "@/theme";

export default function HomeScreen() {
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const { width } = useWindowDimensions();
  const cardWidth = Math.min(300, Math.round(width * 0.72));
  const home = useQuery({ queryKey: ["home"], queryFn: ({ signal }) => api<HomeData>("/home", { signal }) });

  if (home.isPending) return <Loading />;
  if (home.isError) {
    const msg = home.error instanceof ApiError ? home.error.message : t.errors.generic;
    return <ErrorState message={msg} onRetry={() => home.refetch()} />;
  }

  const data = home.data;
  const openEvent = (e: Occurrence) => router.push({ pathname: "/events/[slug]", params: { slug: e.slug } });
  const openOffer = (o: Offer) => router.push({ pathname: "/offers/[slug]", params: { slug: o.slug } });

  return (
    <ScrollView
      contentContainerStyle={{ paddingBottom: space.xxl }}
      refreshControl={<RefreshControl refreshing={home.isRefetching} onRefresh={() => void home.refetch()} tintColor={theme.accentText} />}
    >
      <View style={{ paddingTop: insets.top + space.lg, paddingHorizontal: space.lg, gap: space.sm }}>
        <FlagMark />
        <AppText variant="title" accessibilityRole="header">{t.home.greeting}</AppText>
        <AppText muted>{data.today_label}</AppText>
      </View>

      <Section title={t.home.today} action={t.home.allEvents} onAction={() => router.navigate("/events")}>
        {data.today.length ? (
          <View style={{ gap: space.md }}>
            {data.today.map((e) => <EventRow key={`${e.id}-${e.start}`} item={e} onPress={() => openEvent(e)} />)}
          </View>
        ) : (
          <AppText muted style={{ paddingHorizontal: space.lg }}>{t.home.nothingToday}</AppText>
        )}
      </Section>

      {data.weekend.length ? (
        <Section title={data.weekend_title}>
          <HorizontalRow data={data.weekend} render={(e) => <EventCard item={e} width={cardWidth} onPress={() => openEvent(e)} />} />
        </Section>
      ) : null}

      {data.upcoming.length ? (
        <Section title={t.home.upcoming}>
          <HorizontalRow data={data.upcoming} render={(e) => <EventCard item={e} width={cardWidth} onPress={() => openEvent(e)} />} />
        </Section>
      ) : null}

      {data.offers.length ? (
        <Section title={t.home.offers} action={t.home.allOffers} onAction={() => router.navigate("/offers")}>
          <HorizontalRow data={data.offers} render={(o) => <OfferCard item={o} width={cardWidth} onPress={() => openOffer(o)} />} />
        </Section>
      ) : null}
    </ScrollView>
  );
}

function HorizontalRow<T extends { id: number; start?: string }>({ data, render }: { data: T[]; render: (item: T) => React.ReactElement }) {
  return (
    <FlatList
      horizontal
      data={data}
      keyExtractor={(item) => `${item.id}-${item.start ?? ""}`}
      renderItem={({ item }) => render(item)}
      showsHorizontalScrollIndicator={false}
      contentContainerStyle={{ paddingHorizontal: space.lg, gap: space.md }}
      decelerationRate="fast"
    />
  );
}

/** The small city flag (dark – gold – dark), like the logo mark on the website. */
function FlagMark() {
  const theme = useTheme();
  const edge = theme.dark ? { borderWidth: 1, borderColor: "rgba(255,255,255,0.25)" } : {};
  return (
    <View style={[{ width: 28, height: 18, borderRadius: 3, overflow: "hidden" }, edge]} accessibilityElementsHidden importantForAccessibility="no">
      <View style={{ flex: 1, backgroundColor: flag }} />
      <View style={{ flex: 1, backgroundColor: gold[400] }} />
      <View style={{ flex: 1, backgroundColor: flag }} />
    </View>
  );
}
