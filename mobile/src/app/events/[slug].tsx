/** Event detail: everything from the website's event page, plus phone actions. */
import { useQuery } from "@tanstack/react-query";
import { router, Stack, useLocalSearchParams } from "expo-router";
import { Pressable, ScrollView, View } from "react-native";

import { Cover, EventCard } from "@/components/cards";
import { EventMap } from "@/components/EventMap";
import { Action, InfoRow, LinkText } from "@/components/detail";
import { AppText, Badge, Card, ErrorState, Icon, Loading } from "@/components/ui";
import { t } from "@/i18n/de";
import { api } from "@/lib/api";
import { useFavorites } from "@/lib/favorites";
import { addToCalendar, openWeb, route, share } from "@/lib/links";
import type { EventDetail } from "@/lib/types";
import { space, useTheme } from "@/theme";

export default function EventScreen() {
  const { slug } = useLocalSearchParams<{ slug: string }>();
  const q = useQuery({ queryKey: ["event", slug], queryFn: ({ signal }) => api<EventDetail>(`/events/${slug}`, { signal }) });
  const fav = useFavorites();

  if (q.isPending) return <Loading />;
  if (q.isError) return <ErrorState message={q.error.message} onRetry={() => q.refetch()} />;
  const e = q.data;
  const saved = fav.isFavorite(e.slug);
  const toggleFav = () => fav.toggle({ slug: e.slug, title: e.title, start: e.start, when: e.when });

  return (
    <ScrollView contentContainerStyle={{ paddingBottom: space.xxl }}>
      <Stack.Screen
        options={{
          title: "",
          headerRight: () => (
            <Pressable onPress={toggleFav} hitSlop={12} accessibilityRole="button" accessibilityLabel={saved ? t.favorites.remove : t.favorites.add}>
              <HeartIcon filled={saved} />
            </Pressable>
          ),
        }}
      />
      <Cover image={e.image ? { url: e.image.url, small: e.image.url } : null} category={e.category} height={230} />

      <View style={{ padding: space.lg, gap: space.sm }}>
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 6 }}>
          {e.category ? <Badge kind="neutral">{e.category.name}</Badge> : null}
          {e.is_featured ? <Badge kind="tip">{t.badges.tip}</Badge> : null}
          {e.organization.is_premium ? <Badge kind="premium">{t.badges.premium}</Badge> : null}
        </View>
        <AppText variant="title" accessibilityRole="header">{e.title}</AppText>
        {e.is_past ? <AppText style={{ color: "#b42318" }}>{t.events.pastNotice}</AppText> : null}

        <View style={{ flexDirection: "row", gap: space.sm, marginTop: space.sm }}>
          <Action icon="calendar" label={t.events.addCalendar} onPress={() => addToCalendar(e.ics_url)} />
          <Action icon="share" label={t.events.share} onPress={() => share(e.share_text, e.web_url)} />
          <Action icon="navigation" label={t.events.route} onPress={() => route({ lat: e.lat, lng: e.lng, address: e.address, label: e.location_name })} />
          <Action icon="heart" label={saved ? t.favorites.saved : t.favorites.save} active={saved} onPress={toggleFav} />
        </View>

        <Card style={{ marginTop: space.md }}>
          <InfoRow icon="clock" label={t.events.when} value={e.when}
            extra={e.recurrence_label ? `${e.recurrence_label}${e.recurrence_until ? ` · bis ${formatDate(e.recurrence_until)}` : ""}` : undefined} />
          <InfoRow icon="map-pin" label={t.events.location} value={e.location_name} extra={e.address ?? undefined} />
          <InfoRow icon="tag" label={t.events.priceLabel} value={e.price} />
          <InfoRow icon="users" label={t.events.organizer} value={e.organization.name} last
            onPress={() => router.push({ pathname: "/places/[slug]", params: { slug: e.organization.slug } })} />
        </Card>

        {e.description_text ? <AppText style={{ marginTop: space.md }} selectable>{e.description_text}</AppText> : null}

        {e.next_dates.length > 1 ? (
          <View style={{ marginTop: space.lg, gap: space.sm }}>
            <AppText variant="heading">{t.events.nextDates}</AppText>
            {e.next_dates.map((d) => <AppText key={d.start} muted>• {d.when}</AppText>)}
          </View>
        ) : null}

        {e.lat != null && e.lng != null ? (
          <View style={{ marginTop: space.lg }}>
            <EventMap height={200} zoom={16} center={{ lat: e.lat, lng: e.lng }}
              tilesUrl="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
              markers={[{ slug: e.slug, title: e.title, when: e.when, lat: e.lat, lng: e.lng, category: e.category }]} />
          </View>
        ) : null}

        <Pressable onPress={() => openWeb(e.web_url)} accessibilityRole="link" style={{ marginTop: space.lg }}>
          <LinkText>{t.events.openWeb}</LinkText>
        </Pressable>
      </View>

      {e.more_from_organizer.length ? (
        <View style={{ gap: space.md }}>
          <AppText variant="heading" style={{ paddingHorizontal: space.lg }}>{t.events.moreFrom(e.organization.name)}</AppText>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ paddingHorizontal: space.lg, gap: space.md }}>
            {e.more_from_organizer.map((o) => (
              <EventCard key={`${o.id}-${o.start}`} item={o} width={240} onPress={() => router.push({ pathname: "/events/[slug]", params: { slug: o.slug } })} />
            ))}
          </ScrollView>
        </View>
      ) : null}
    </ScrollView>
  );
}

function formatDate(iso: string) {
  const [y, m, d] = iso.split("-");
  return `${d}.${m}.${y}`;
}

function HeartIcon({ filled }: { filled: boolean }) {
  const theme = useTheme();
  // Feather has no filled heart; a gold heart marks "saved".
  return <Icon name="heart" size={22} color={filled ? theme.accent : theme.text} />;
}
