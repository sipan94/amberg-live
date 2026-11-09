/** Event detail – full version comes in phase C. */
import { useQuery } from "@tanstack/react-query";
import { Stack, useLocalSearchParams } from "expo-router";
import { ScrollView, View } from "react-native";

import { Cover } from "@/components/cards";
import { AppText, ErrorState, Loading } from "@/components/ui";
import { api } from "@/lib/api";
import type { Occurrence } from "@/lib/types";
import { space } from "@/theme";

type EventDetail = Occurrence & { description_text: string; address: string | null };

export default function EventScreen() {
  const { slug } = useLocalSearchParams<{ slug: string }>();
  const q = useQuery({ queryKey: ["event", slug], queryFn: ({ signal }) => api<EventDetail>(`/events/${slug}`, { signal }) });
  if (q.isPending) return <Loading />;
  if (q.isError) return <ErrorState message={q.error.message} onRetry={() => q.refetch()} />;
  const e = q.data;
  return (
    <ScrollView contentContainerStyle={{ paddingBottom: space.xxl }}>
      <Stack.Screen options={{ title: e.title }} />
      <Cover image={e.image} category={e.category} height={220} />
      <View style={{ padding: space.lg, gap: space.sm }}>
        <AppText variant="label" muted>{e.when}</AppText>
        <AppText variant="title">{e.title}</AppText>
        <AppText muted>{e.location_name}{e.address ? ` · ${e.address}` : ""} · {e.price}</AppText>
        <AppText style={{ marginTop: space.md }}>{e.description_text}</AppText>
      </View>
    </ScrollView>
  );
}
