/** Offer detail. */
import { useQuery } from "@tanstack/react-query";
import { router, Stack, useLocalSearchParams } from "expo-router";
import { Pressable, ScrollView, View } from "react-native";

import { Cover } from "@/components/cards";
import { Action, InfoRow, LinkText } from "@/components/detail";
import { AppText, Badge, Card, ErrorState, Loading } from "@/components/ui";
import { t } from "@/i18n/de";
import { api } from "@/lib/api";
import { openWeb, share } from "@/lib/links";
import type { Offer } from "@/lib/types";
import { space } from "@/theme";

export default function OfferScreen() {
  const { slug } = useLocalSearchParams<{ slug: string }>();
  const q = useQuery({ queryKey: ["offer", slug], queryFn: ({ signal }) => api<Offer>(`/offers/${slug}`, { signal }) });
  if (q.isPending) return <Loading />;
  if (q.isError) return <ErrorState message={q.error.message} onRetry={() => q.refetch()} />;
  const o = q.data;
  const image = o.image ?? o.organization.logo;

  return (
    <ScrollView contentContainerStyle={{ paddingBottom: space.xxl }}>
      <Stack.Screen options={{ title: "" }} />
      <Cover image={image ? { url: image.url, small: image.url } : null} height={230} />
      <View style={{ padding: space.lg, gap: space.sm }}>
        {o.is_featured ? <View style={{ flexDirection: "row" }}><Badge kind="tip">{t.badges.tip}</Badge></View> : null}
        <AppText variant="title" accessibilityRole="header">{o.title}</AppText>
        <AppText muted>{o.validity}</AppText>

        <View style={{ flexDirection: "row", gap: space.sm, marginTop: space.sm }}>
          <Action icon="share" label={t.events.share} onPress={() => share(`${o.title} – ${o.web_url}`, o.web_url)} />
          <Action icon="globe" label={t.places.website} onPress={() => openWeb(o.web_url)} />
        </View>

        {o.description_text ? <AppText style={{ marginTop: space.md }} selectable>{o.description_text}</AppText> : null}

        <Card style={{ marginTop: space.lg }}>
          <InfoRow icon="shopping-bag" label={t.offers.from} value={o.organization.name} last
            onPress={() => router.push({ pathname: "/places/[slug]", params: { slug: o.organization.slug } })} />
        </Card>

        <Pressable onPress={() => openWeb(o.web_url)} accessibilityRole="link" style={{ marginTop: space.lg }}>
          <LinkText>{t.events.openWeb}</LinkText>
        </Pressable>
      </View>
    </ScrollView>
  );
}
