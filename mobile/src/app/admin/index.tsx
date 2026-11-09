/** Verwaltung: numbers, open reviews and the admin menu (GET /admin/overview). */
import { useQuery } from "@tanstack/react-query";
import { Redirect, router, Stack } from "expo-router";
import { Pressable, RefreshControl, ScrollView, View } from "react-native";

import { AppText, Card, ErrorState, Icon, Loading } from "@/components/ui";
import { t } from "@/i18n/de";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { AdminKind, AdminOverview } from "@/lib/types";
import { space, useTheme } from "@/theme";

export default function AdminScreen() {
  const { user } = useAuth();
  const q = useQuery({ queryKey: ["admin", "overview"], queryFn: ({ signal }) => api<AdminOverview>("/admin/overview", { signal }), enabled: !!user?.is_admin });

  if (!user?.is_admin) return <Redirect href="/account" />;
  if (q.isPending) return <Loading />;
  if (q.isError) return <ErrorState message={q.error.message} onRetry={() => q.refetch()} />;
  const d = q.data;
  const pendingTotal = d.pending.event + d.pending.offer + d.pending.organization;

  return (
    <ScrollView contentContainerStyle={{ padding: space.lg, gap: space.lg, paddingBottom: space.xxl * 2 }}
      refreshControl={<RefreshControl refreshing={q.isRefetching} onRefresh={() => void q.refetch()} />}>
      <Stack.Screen options={{ title: t.admin.title }} />

      <Card onPress={() => router.push({ pathname: "/admin/queue", params: { kind: firstPending(d.pending) } })} highlight={pendingTotal > 0}>
        <View style={{ padding: space.lg, gap: space.sm }}>
          <View style={{ flexDirection: "row", alignItems: "center", gap: space.sm }}>
            <Icon name="check-square" size={20} />
            <AppText variant="heading" style={{ flex: 1 }}>{t.admin.review}</AppText>
            <Icon name="chevron-right" size={18} />
          </View>
          <AppText muted>{pendingTotal ? t.admin.pending(pendingTotal) : t.admin.queueEmpty}</AppText>
          {pendingTotal ? (
            <View style={{ flexDirection: "row", gap: space.lg }}>
              {(Object.keys(d.pending) as AdminKind[]).map((k) => (
                <AppText key={k} variant="small"><AppText variant="small" style={{ fontFamily: "SchibstedGrotesk_700Bold" }}>{d.pending[k]}</AppText> {t.admin.kinds[k]}</AppText>
              ))}
            </View>
          ) : null}
        </View>
      </Card>

      <View style={{ flexDirection: "row", flexWrap: "wrap", gap: space.md }}>
        <Stat label={t.admin.statViews} value={d.views_total} hint={t.admin.statViewsHint} />
        <Stat label={t.admin.statEvents} value={d.stats.events_upcoming} />
        <Stat label={t.admin.statOrgs} value={d.stats.orgs} hint={t.admin.statPremium(d.stats.premium)} />
        <Stat label={t.admin.statUsers} value={d.stats.users} hint={t.admin.statUsersNew(d.stats.users_new)} />
      </View>

      <Card style={{ padding: space.lg, gap: space.sm }}>
        <AppText variant="label" muted>{t.admin.statViews}</AppText>
        <Bars days={d.days} />
      </Card>

      <Card>
        {[
          { icon: "layers" as const, label: t.admin.content, go: () => router.push("/admin/content") },
          { icon: "users" as const, label: t.admin.users, go: () => router.push("/admin/users") },
          { icon: "tag" as const, label: t.admin.categories, go: () => router.push("/admin/categories") },
          { icon: "list" as const, label: t.admin.log, go: () => router.push("/admin/log") },
        ].map((m, i, all) => <MenuRow key={m.label} icon={m.icon} label={m.label} onPress={m.go} last={i === all.length - 1} />)}
      </Card>

      {d.top_events.length ? (
        <View style={{ gap: space.sm }}>
          <AppText variant="heading">{t.admin.topEvents}</AppText>
          <Card>
            {d.top_events.map((e, i) => (
              <MenuRow key={e.slug} label={e.title} value={String(e.views)} last={i === d.top_events.length - 1}
                onPress={() => router.push({ pathname: "/events/[slug]", params: { slug: e.slug } })} />
            ))}
          </Card>
        </View>
      ) : null}

      {d.recent.length ? (
        <View style={{ gap: space.sm }}>
          <AppText variant="heading">{t.admin.recent}</AppText>
          <Card style={{ padding: space.md, gap: space.sm }}>
            {d.recent.map((r, i) => (
              <AppText key={i} variant="small"><AppText variant="small" muted>{r.action}: </AppText>{r.label}</AppText>
            ))}
          </Card>
        </View>
      ) : null}
    </ScrollView>
  );
}

function firstPending(p: Record<AdminKind, number>): AdminKind {
  return (["event", "offer", "organization"] as AdminKind[]).find((k) => p[k] > 0) ?? "event";
}

function Stat({ label, value, hint }: { label: string; value: number; hint?: string }) {
  return (
    <Card style={{ flexBasis: "47%", flexGrow: 1, padding: space.md, gap: 2 }}>
      <AppText variant="label" muted>{label}</AppText>
      <AppText variant="title" style={{ fontSize: 26 }}>{value.toLocaleString("de-DE")}</AppText>
      {hint ? <AppText variant="small" muted>{hint}</AppText> : null}
    </Card>
  );
}

/** Daily views of the last 30 days as small bars. */
function Bars({ days }: { days: { date: string; views: number }[] }) {
  const theme = useTheme();
  const max = Math.max(1, ...days.map((d) => d.views));
  return (
    <View style={{ flexDirection: "row", alignItems: "flex-end", height: 80, gap: 2 }}
      accessibilityLabel={`${t.admin.statViews}: ${days.reduce((s, d) => s + d.views, 0)}`}>
      {days.map((d) => (
        <View key={d.date} style={{ flex: 1, height: Math.max(2, (d.views / max) * 80), borderRadius: 2, backgroundColor: d.views ? theme.accent : theme.cardBorder }} />
      ))}
    </View>
  );
}

function MenuRow({ icon, label, value, onPress, last }: {
  icon?: React.ComponentProps<typeof Icon>["name"]; label: string; value?: string; onPress: () => void; last?: boolean;
}) {
  const theme = useTheme();
  return (
    <Pressable onPress={onPress} accessibilityRole="button"
      style={({ pressed }) => ({ flexDirection: "row", alignItems: "center", gap: space.md, padding: space.md, borderBottomWidth: last ? 0 : 1, borderBottomColor: theme.cardBorder, opacity: pressed ? 0.7 : 1 })}>
      {icon ? <Icon name={icon} size={19} color={theme.textMuted} /> : null}
      <AppText style={{ flex: 1 }} numberOfLines={1}>{label}</AppText>
      {value ? <AppText muted>{value}</AppText> : null}
      <Icon name="chevron-right" size={18} color={theme.textMuted} />
    </Pressable>
  );
}
