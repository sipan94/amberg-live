/** Konto: Merkliste, login / business area, account settings, legal pages. */
import { useQuery, useQueryClient } from "@tanstack/react-query";
import Constants from "expo-constants";
import { router, useFocusEffect } from "expo-router";
import { useCallback, useState } from "react";
import { Alert, Platform, Pressable, ScrollView, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { Notice } from "@/components/form";
import { AppText, Badge, Button, Card, Icon } from "@/components/ui";
import { t } from "@/i18n/de";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useFavorites } from "@/lib/favorites";
import { openWeb } from "@/lib/links";
import type { Meta } from "@/lib/types";
import { space, useTheme } from "@/theme";

export default function AccountScreen() {
  const insets = useSafeAreaInsets();
  const fav = useFavorites();
  const { user, logout, refresh } = useAuth();
  const queryClient = useQueryClient();
  const meta = useQuery({ queryKey: ["meta"], queryFn: () => api<Meta>("/meta"), staleTime: 60 * 60_000 });
  const legal = meta.data?.legal;
  const [notice, setNotice] = useState<string | null>(null);

  // Fresh numbers (open reviews, verification) each time the tab is shown.
  useFocusEffect(useCallback(() => {
    if (user) void refresh().catch(() => undefined);
  }, [user?.id])); // eslint-disable-line react-hooks/exhaustive-deps

  const confirmLogout = () => {
    const go = async () => {
      await logout();
      queryClient.removeQueries({ queryKey: ["overview"] });
    };
    if (Platform.OS === "web") return void go();
    Alert.alert(t.auth.logout, t.auth.logoutConfirm, [
      { text: t.forms.cancel, style: "cancel" },
      { text: t.auth.logout, style: "destructive", onPress: () => void go() },
    ]);
  };

  const resend = async () => {
    try {
      setNotice((await api<{ message: string }>("/auth/resend-verification", { method: "POST" })).message);
    } catch (e) {
      setNotice(e instanceof ApiError ? e.message : t.errors.generic);
    }
  };

  return (
    <ScrollView contentContainerStyle={{ paddingTop: insets.top + space.md, paddingBottom: space.xxl, paddingHorizontal: space.lg, gap: space.lg }}>
      <AppText variant="title" accessibilityRole="header">{t.account.title}</AppText>

      <Card>
        <MenuRow icon="heart" label={t.account.favorites} value={fav.items.length ? String(fav.items.length) : undefined} onPress={() => router.push("/favorites")} last />
      </Card>

      {user ? (
        <>
          <Card style={{ padding: space.lg, gap: space.sm }}>
            <View style={{ flexDirection: "row", alignItems: "center", gap: space.sm, flexWrap: "wrap" }}>
              <AppText variant="heading" style={{ flexShrink: 1 }} numberOfLines={1}>{user.organization?.name ?? user.email}</AppText>
              {user.is_admin ? <Badge kind="premium">Admin</Badge> : null}
            </View>
            {user.organization ? <AppText variant="small" muted>{user.email}</AppText> : null}
            {!user.is_verified ? (
              <View style={{ gap: space.sm, marginTop: space.sm }}>
                <Notice kind="info" message={t.auth.notVerified} />
                <Notice message={notice} />
                <View style={{ flexDirection: "row", gap: space.sm, flexWrap: "wrap" }}>
                  <Button kind="secondary" title={t.auth.resend} onPress={resend} />
                  <Button kind="secondary" title={t.auth.checkAgain} onPress={() => void refresh()} />
                </View>
              </View>
            ) : null}
          </Card>
          <Card>
            {user.is_admin ? (
              <MenuRow icon="shield" label={t.admin.title} value={user.pending ? String(user.pending) : undefined} onPress={() => router.push("/admin")} />
            ) : null}
            <MenuRow icon="grid" label={t.dashboard.title} onPress={() => router.push("/dashboard")} />
            <MenuRow icon="lock" label={t.settings.changePassword} onPress={() => router.push("/settings/password")} />
            <MenuRow icon="log-out" label={t.auth.logout} onPress={confirmLogout} />
            <MenuRow icon="trash-2" label={t.settings.deleteAccount} onPress={() => router.push("/settings/delete")} danger last />
          </Card>
        </>
      ) : (
        <Card style={{ padding: space.lg, gap: space.md }}>
          <AppText variant="heading">{t.account.forBusinesses}</AppText>
          <AppText muted>{t.account.forBusinessesText}</AppText>
          <View style={{ flexDirection: "row", gap: space.sm }}>
            <View style={{ flex: 1 }}><Button title={t.auth.login} onPress={() => router.push("/login")} /></View>
            <View style={{ flex: 1 }}><Button kind="secondary" title={t.auth.register} onPress={() => router.push("/register")} /></View>
          </View>
        </Card>
      )}

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

function MenuRow({ icon, label, value, onPress, last, danger }: {
  icon: React.ComponentProps<typeof Icon>["name"]; label: string; value?: string; onPress: () => void; last?: boolean; danger?: boolean;
}) {
  const theme = useTheme();
  const color = danger ? theme.danger : undefined;
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      style={({ pressed }) => ({
        flexDirection: "row", alignItems: "center", gap: space.md, padding: space.md,
        borderBottomWidth: last ? 0 : 1, borderBottomColor: theme.cardBorder, opacity: pressed ? 0.7 : 1,
      })}
    >
      <Icon name={icon} size={19} color={color ?? theme.textMuted} />
      <AppText style={{ flex: 1, color }}>{label}</AppText>
      {value ? <AppText muted>{value}</AppText> : null}
      <Icon name="chevron-right" size={18} color={theme.textMuted} />
    </Pressable>
  );
}
