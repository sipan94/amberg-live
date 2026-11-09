/** Merkliste: saved events with fresh dates from the server (POST /favorites). */
import { useQuery } from "@tanstack/react-query";
import { router, Stack } from "expo-router";
import { ScrollView, Switch, View } from "react-native";

import { EventRow } from "@/components/cards";
import { AppText, Card, ErrorState, Loading } from "@/components/ui";
import { t } from "@/i18n/de";
import { api } from "@/lib/api";
import { useFavorites } from "@/lib/favorites";
import type { Occurrence } from "@/lib/types";
import { space, useTheme } from "@/theme";

export default function FavoritesScreen() {
  const theme = useTheme();
  const fav = useFavorites();
  const slugs = fav.items.map((f) => f.slug);
  const q = useQuery({
    queryKey: ["favorites", slugs],
    queryFn: ({ signal }) => api<{ items: (Occurrence & { past: boolean })[] }>("/favorites", { method: "POST", body: { slugs }, signal }),
    enabled: slugs.length > 0,
  });

  return (
    <ScrollView contentContainerStyle={{ paddingVertical: space.lg, gap: space.md }}>
      <Stack.Screen options={{ title: t.favorites.title }} />
      <AppText muted style={{ paddingHorizontal: space.lg }}>{t.favorites.intro}</AppText>

      <Card style={{ marginHorizontal: space.lg, padding: space.md }}>
        <View style={{ flexDirection: "row", alignItems: "center", gap: space.md }}>
          <View style={{ flex: 1, gap: 2 }}>
            <AppText style={{ fontFamily: "SchibstedGrotesk_600SemiBold" }}>{t.favorites.remindersOn}</AppText>
            <AppText variant="small" muted>{t.favorites.remindersHint}</AppText>
          </View>
          <Switch value={fav.remindersOn} onValueChange={(v) => void fav.setRemindersOn(v)} trackColor={{ true: theme.accent }}
            accessibilityLabel={t.favorites.remindersOn} />
        </View>
      </Card>

      {!slugs.length ? (
        <AppText muted style={{ paddingHorizontal: space.lg }}>{t.favorites.empty}</AppText>
      ) : q.isPending ? (
        <Loading />
      ) : q.isError ? (
        <ErrorState message={q.error.message} onRetry={() => q.refetch()} />
      ) : (
        q.data.items.map((e) => (
          <View key={e.slug} style={{ opacity: e.past ? 0.55 : 1 }}>
            {e.past ? <AppText variant="label" muted style={{ paddingHorizontal: space.lg, marginBottom: 4 }}>{t.favorites.past}</AppText> : null}
            <EventRow item={e} onPress={() => router.push({ pathname: "/events/[slug]", params: { slug: e.slug } })} />
          </View>
        ))
      )}
    </ScrollView>
  );
}
