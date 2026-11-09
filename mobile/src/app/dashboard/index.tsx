/** Mein Bereich: profile status, own events and offers with review status (GET /me/overview). */
import { useQuery } from "@tanstack/react-query";
import { Image } from "expo-image";
import { Redirect, router, Stack } from "expo-router";
import { RefreshControl, ScrollView, View } from "react-native";

import { Notice } from "@/components/form";
import { AppText, Button, Card, ErrorState, Icon, Loading, StatusBadge } from "@/components/ui";
import { t } from "@/i18n/de";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { MyEvent, MyOffer, Overview } from "@/lib/types";
import { radius, space, useTheme } from "@/theme";

export default function DashboardScreen() {
  const { user } = useAuth();
  const q = useQuery({ queryKey: ["overview"], queryFn: ({ signal }) => api<Overview>("/me/overview", { signal }), enabled: !!user });

  if (!user) return <Redirect href="/login" />;
  if (q.isPending) return <Loading />;
  if (q.isError) return <ErrorState message={q.error.message} onRetry={() => q.refetch()} />;
  const { organization: org, events, offers } = q.data;
  const verified = q.data.user.is_verified;

  return (
    <ScrollView
      contentContainerStyle={{ padding: space.lg, gap: space.lg, paddingBottom: space.xxl * 2 }}
      refreshControl={<RefreshControl refreshing={q.isRefetching} onRefresh={() => void q.refetch()} />}
    >
      <Stack.Screen options={{ title: t.dashboard.title }} />
      {!verified ? <Notice kind="info" message={t.auth.notVerified} /> : null}

      {/* Profile */}
      {org ? (
        <Card style={{ padding: space.lg, gap: space.sm }}>
          <View style={{ flexDirection: "row", alignItems: "center", gap: space.md }}>
            <Logo url={org.logo?.small} club={org.type === "club"} />
            <View style={{ flex: 1, gap: 4 }}>
              <AppText variant="heading" numberOfLines={1}>{org.name}</AppText>
              <View style={{ flexDirection: "row" }}><StatusBadge status={org.status} label={org.status_label} /></View>
            </View>
          </View>
          {org.rejection_reason ? <AppText variant="small" style={{ color: "#b42318" }}>{t.dashboard.reason}: {org.rejection_reason}</AppText> : null}
          <Button kind="secondary" title={t.dashboard.editProfile} onPress={() => router.push("/dashboard/profile")} disabled={!verified} />
        </Card>
      ) : (
        <Card style={{ padding: space.lg, gap: space.md }}>
          <AppText>{t.dashboard.noProfile}</AppText>
          <Button title={t.dashboard.createProfile} onPress={() => router.push("/dashboard/profile")} disabled={!verified} />
        </Card>
      )}

      {org ? (
        <>
          <Section title={t.dashboard.events} action={t.dashboard.newEvent} disabled={!verified}
            onAction={() => router.push({ pathname: "/dashboard/event", params: {} })}>
            {events.length ? events.map((e) => <ItemRow key={e.id} item={e} subtitle={e.when}
              onPress={() => router.push({ pathname: "/dashboard/event", params: { id: String(e.id) } })} />)
              : <AppText muted>{t.dashboard.none}</AppText>}
          </Section>
          <Section title={t.dashboard.offers} action={t.dashboard.newOffer} disabled={!verified}
            onAction={() => router.push({ pathname: "/dashboard/offer", params: {} })}>
            {offers.length ? offers.map((o) => <ItemRow key={o.id} item={o} subtitle={offerDates(o)}
              onPress={() => router.push({ pathname: "/dashboard/offer", params: { id: String(o.id) } })} />)
              : <AppText muted>{t.dashboard.none}</AppText>}
          </Section>
          <AppText variant="small" muted>{t.dashboard.reviewNote}</AppText>
        </>
      ) : null}
    </ScrollView>
  );
}

function offerDates(o: MyOffer) {
  const f = (iso: string) => iso.split("-").reverse().join(".");
  return o.valid_until ? `${f(o.valid_from)} – ${f(o.valid_until)}` : `${t.offers.from} ${f(o.valid_from)}`;
}

function Logo({ url, club }: { url?: string; club: boolean }) {
  const theme = useTheme();
  return (
    <View style={{ width: 52, height: 52, borderRadius: radius.md, overflow: "hidden", alignItems: "center", justifyContent: "center", backgroundColor: theme.dark ? "#34302b" : "#eeece7" }}>
      {url ? <Image source={{ uri: url }} style={{ width: 52, height: 52 }} /> : <Icon name={club ? "flag" : "shopping-bag"} size={22} color={theme.textMuted} />}
    </View>
  );
}

function Section({ title, action, onAction, disabled, children }: {
  title: string; action: string; onAction: () => void; disabled?: boolean; children: React.ReactNode;
}) {
  return (
    <View style={{ gap: space.sm }}>
      <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: space.sm }}>
        <AppText variant="heading" style={{ flexShrink: 1 }}>{title}</AppText>
        <Button kind="secondary" title={`+ ${action}`} onPress={onAction} disabled={disabled} />
      </View>
      {children}
    </View>
  );
}

function ItemRow({ item, subtitle, onPress }: { item: MyEvent | MyOffer; subtitle: string; onPress: () => void }) {
  const theme = useTheme();
  return (
    <Card onPress={onPress}>
      <View style={{ flexDirection: "row", gap: space.md, padding: space.md, alignItems: "center" }}>
        {item.image ? <Image source={{ uri: item.image.small }} style={{ width: 56, height: 56, borderRadius: radius.sm }} contentFit="cover" /> : null}
        <View style={{ flex: 1, gap: 3 }}>
          <View style={{ flexDirection: "row", gap: 6, alignItems: "center", flexWrap: "wrap" }}>
            <StatusBadge status={item.status} label={item.status_label} />
            <AppText variant="label" muted>{t.dashboard.views(item.view_count)}</AppText>
          </View>
          <AppText numberOfLines={1} style={{ fontFamily: "SchibstedGrotesk_600SemiBold" }}>{item.title}</AppText>
          <AppText variant="small" muted numberOfLines={1}>{subtitle}</AppText>
          {item.rejection_reason ? <AppText variant="small" style={{ color: theme.danger }} numberOfLines={3}>{t.dashboard.reason}: {item.rejection_reason}</AppText> : null}
        </View>
        <Icon name="chevron-right" size={18} color={theme.textMuted} />
      </View>
    </Card>
  );
}
