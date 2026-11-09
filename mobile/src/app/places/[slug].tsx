/** Business / club profile: info, opening hours, contact, events and offers. */
import { useQuery } from "@tanstack/react-query";
import { Image } from "expo-image";
import { router, Stack, useLocalSearchParams } from "expo-router";
import { Pressable, ScrollView, View } from "react-native";

import { EventCard, OfferCard } from "@/components/cards";
import { Action, InfoRow, LinkText } from "@/components/detail";
import { EventMap } from "@/components/EventMap";
import { AppText, Badge, Card, ErrorState, Icon, Loading } from "@/components/ui";
import { t } from "@/i18n/de";
import { api } from "@/lib/api";
import { call, mail, openWeb, route, share } from "@/lib/links";
import type { Organization } from "@/lib/types";
import { radius, space, tint, useTheme } from "@/theme";

export default function PlaceScreen() {
  const theme = useTheme();
  const { slug } = useLocalSearchParams<{ slug: string }>();
  const q = useQuery({ queryKey: ["organization", slug], queryFn: ({ signal }) => api<Organization>(`/organizations/${slug}`, { signal }) });
  if (q.isPending) return <Loading />;
  if (q.isError) return <ErrorState message={q.error.message} onRetry={() => q.refetch()} />;
  const o = q.data;
  const club = o.type === "club";

  return (
    <ScrollView contentContainerStyle={{ paddingBottom: space.xxl }}>
      <Stack.Screen options={{ title: "" }} />
      {o.cover_image ? (
        <Image source={{ uri: o.cover_image.url }} style={{ width: "100%", height: 180 }} contentFit="cover" />
      ) : (
        <View style={{ height: 110, backgroundColor: tint("#e3a92b", theme.dark ? 0.12 : 0.12, theme.dark ? "#24211d" : "#fbfaf8") }} />
      )}

      <View style={{ paddingHorizontal: space.lg, gap: space.sm }}>
        <View style={{
          width: 76, height: 76, borderRadius: radius.lg, marginTop: -38, overflow: "hidden", borderWidth: 3, borderColor: theme.bg,
          backgroundColor: theme.card, alignItems: "center", justifyContent: "center",
        }}>
          {o.logo ? <Image source={{ uri: o.logo.small }} style={{ width: 70, height: 70 }} contentFit="cover" />
            : <Icon name={club ? "flag" : "shopping-bag"} size={28} color={theme.textMuted} />}
        </View>
        <View style={{ flexDirection: "row", gap: 6 }}>
          <Badge kind="neutral">{club ? t.places.club : t.places.business}</Badge>
          {o.is_premium ? <Badge kind="premium">{t.badges.premium}</Badge> : null}
        </View>
        <AppText variant="title" accessibilityRole="header">{o.name}</AppText>

        <View style={{ flexDirection: "row", gap: space.sm, marginTop: space.sm }}>
          {o.phone ? <Action icon="phone" label={t.places.call} onPress={() => call(o.phone!)} /> : null}
          {o.address || o.lat != null ? <Action icon="navigation" label={t.events.route} onPress={() => route({ lat: o.lat, lng: o.lng, address: o.address, label: o.name })} /> : null}
          {o.website ? <Action icon="globe" label={t.places.website} onPress={() => openWeb(o.website!)} /> : null}
          <Action icon="share" label={t.events.share} onPress={() => share(`${o.name} – ${o.web_url}`, o.web_url)} />
        </View>

        {o.description_text ? <AppText style={{ marginTop: space.md }} selectable>{o.description_text}</AppText> : null}

        {o.opening_hours.length ? (
          <Card style={{ marginTop: space.lg, padding: space.md, gap: 6 }}>
            <AppText variant="heading" style={{ fontSize: 16, marginBottom: 4 }}>{t.places.hours}</AppText>
            {o.opening_hours.map((h) => (
              <View key={h.day} style={{ flexDirection: "row", justifyContent: "space-between", gap: space.md }}>
                <AppText muted>{h.label}</AppText>
                <AppText style={{ flexShrink: 1, textAlign: "right" }}>{h.value}</AppText>
              </View>
            ))}
          </Card>
        ) : null}

        {o.address || o.phone || o.email ? (
          <Card style={{ marginTop: space.md }}>
            {o.address ? <InfoRow icon="map-pin" label={t.events.location} value={o.address} last={!o.phone && !o.email} /> : null}
            {o.phone ? <InfoRow icon="phone" label={t.places.call} value={o.phone} onPress={() => call(o.phone!)} last={!o.email} /> : null}
            {o.email ? <InfoRow icon="mail" label={t.places.email} value={o.email} onPress={() => mail(o.email!)} last /> : null}
          </Card>
        ) : null}

        {o.lat != null && o.lng != null ? (
          <View style={{ marginTop: space.md }}>
            <EventMap height={190} zoom={16} center={{ lat: o.lat, lng: o.lng }} tilesUrl="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
              markers={[{ slug: o.slug, title: o.name, when: o.address ?? "", lat: o.lat, lng: o.lng, category: null }]} />
          </View>
        ) : null}
      </View>

      {o.events.length ? (
        <View style={{ marginTop: space.xl, gap: space.md }}>
          <AppText variant="heading" style={{ paddingHorizontal: space.lg }}>{t.places.events}</AppText>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ paddingHorizontal: space.lg, gap: space.md }}>
            {o.events.map((e) => (
              <EventCard key={`${e.id}-${e.start}`} item={e} width={240} onPress={() => router.push({ pathname: "/events/[slug]", params: { slug: e.slug } })} />
            ))}
          </ScrollView>
        </View>
      ) : null}

      {o.offers.length ? (
        <View style={{ marginTop: space.xl, gap: space.md }}>
          <AppText variant="heading" style={{ paddingHorizontal: space.lg }}>{t.places.offers}</AppText>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ paddingHorizontal: space.lg, gap: space.md }}>
            {o.offers.map((of) => (
              <OfferCard key={of.id} item={of} width={240} onPress={() => router.push({ pathname: "/offers/[slug]", params: { slug: of.slug } })} />
            ))}
          </ScrollView>
        </View>
      ) : null}

      <Pressable onPress={() => openWeb(o.web_url)} accessibilityRole="link" style={{ margin: space.lg }}>
        <LinkText>{t.events.openWeb}</LinkText>
      </Pressable>
    </ScrollView>
  );
}
