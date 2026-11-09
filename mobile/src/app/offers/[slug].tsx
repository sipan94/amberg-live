/** Offer detail – full version comes in phase C. */
import { useQuery } from "@tanstack/react-query";
import { Stack, useLocalSearchParams } from "expo-router";
import { ScrollView, View } from "react-native";

import { Cover } from "@/components/cards";
import { AppText, ErrorState, Loading } from "@/components/ui";
import { api } from "@/lib/api";
import type { Offer } from "@/lib/types";
import { space } from "@/theme";

export default function OfferScreen() {
  const { slug } = useLocalSearchParams<{ slug: string }>();
  const q = useQuery({ queryKey: ["offer", slug], queryFn: ({ signal }) => api<Offer>(`/offers/${slug}`, { signal }) });
  if (q.isPending) return <Loading />;
  if (q.isError) return <ErrorState message={q.error.message} onRetry={() => q.refetch()} />;
  const o = q.data;
  return (
    <ScrollView contentContainerStyle={{ paddingBottom: space.xxl }}>
      <Stack.Screen options={{ title: o.organization.name }} />
      <Cover image={o.image ?? o.organization.logo} height={220} />
      <View style={{ padding: space.lg, gap: space.sm }}>
        <AppText variant="label" muted>{o.organization.name}</AppText>
        <AppText variant="title">{o.title}</AppText>
        <AppText muted>{o.validity}</AppText>
        <AppText style={{ marginTop: space.md }}>{o.description_text}</AppText>
      </View>
    </ScrollView>
  );
}
