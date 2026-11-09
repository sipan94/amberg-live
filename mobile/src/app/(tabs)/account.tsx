/** Konto: Merkliste, area for businesses (login comes in phase D), legal pages. */
import { useQuery } from "@tanstack/react-query";
import Constants from "expo-constants";
import { router } from "expo-router";
import { Pressable, ScrollView, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { AppText, Card, Icon } from "@/components/ui";
import { t } from "@/i18n/de";
import { api } from "@/lib/api";
import { useFavorites } from "@/lib/favorites";
import { openWeb } from "@/lib/links";
import type { Meta } from "@/lib/types";
import { space, useTheme } from "@/theme";

export default function AccountScreen() {
  const insets = useSafeAreaInsets();
  const fav = useFavorites();
  const meta = useQuery({ queryKey: ["meta"], queryFn: () => api<Meta>("/meta"), staleTime: 60 * 60_000 });
  const legal = meta.data?.legal;

  return (
    <ScrollView contentContainerStyle={{ paddingTop: insets.top + space.md, paddingBottom: space.xxl, paddingHorizontal: space.lg, gap: space.lg }}>
      <AppText variant="title" accessibilityRole="header">{t.account.title}</AppText>

      <Card>
        <MenuRow icon="heart" label={t.account.favorites} value={fav.items.length ? String(fav.items.length) : undefined} onPress={() => router.push("/favorites")} last />
      </Card>

      <Card style={{ padding: space.lg, gap: space.sm }}>
        <AppText variant="heading">{t.account.forBusinesses}</AppText>
        <AppText muted>{t.account.forBusinessesText}</AppText>
        <AppText variant="small" muted>{t.account.loginSoon}</AppText>
      </Card>

      <View style={{ gap: space.sm }}>
        <AppText variant="label" muted style={{ textTransform: "uppercase" }}>{t.account.legal}</AppText>
        <Card>
          <MenuRow icon="info" label={t.account.impressum} onPress={() => legal && openWeb(legal.impressum)} />
          <MenuRow icon="shield" label={t.account.datenschutz} onPress={() => legal && openWeb(legal.datenschutz)} />
          <MenuRow icon="file-text" label={t.account.agb} onPress={() => legal && openWeb(legal.agb)} />
          <MenuRow icon="mail" label={t.account.kontakt} onPress={() => legal && openWeb(legal.kontakt)} />
          <MenuRow icon="globe" label={t.account.website} onPress={() => meta.data && openWeb(meta.data.web_url)} last />
        </Card>
      </View>

      <AppText variant="small" muted style={{ textAlign: "center" }}>
        {t.appName} · {t.account.version(Constants.expoConfig?.version ?? "1.0.0")}
      </AppText>
    </ScrollView>
  );
}

function MenuRow({ icon, label, value, onPress, last }: {
  icon: React.ComponentProps<typeof Icon>["name"]; label: string; value?: string; onPress: () => void; last?: boolean;
}) {
  const theme = useTheme();
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      style={({ pressed }) => ({
        flexDirection: "row", alignItems: "center", gap: space.md, padding: space.md,
        borderBottomWidth: last ? 0 : 1, borderBottomColor: theme.cardBorder, opacity: pressed ? 0.7 : 1,
      })}
    >
      <Icon name={icon} size={19} color={theme.textMuted} />
      <AppText style={{ flex: 1 }}>{label}</AppText>
      {value ? <AppText muted>{value}</AppText> : null}
      <Icon name="chevron-right" size={18} color={theme.textMuted} />
    </Pressable>
  );
}
