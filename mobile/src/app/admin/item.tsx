/** One entry as the admin sees it: review, Tipp, Premium, edit, delete (GET /admin/<kind>/<id>). */
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { router, Stack, useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { ScrollView, View } from "react-native";

import { AdminItemCard, confirm, RejectDialog } from "@/components/admin";
import { DateTimeField, Notice, SmallButton } from "@/components/form";
import { AppText, Card, ErrorState, Loading } from "@/components/ui";
import { t } from "@/i18n/de";
import { adminApi, itemLabel, refreshAdmin } from "@/lib/admin";
import { api, ApiError } from "@/lib/api";
import { openWeb } from "@/lib/links";
import { goBack } from "@/lib/nav";
import type { AdminItem, AdminKind, AdminQueue } from "@/lib/types";
import { space } from "@/theme";

export default function AdminItemScreen() {
  const { kind, id } = useLocalSearchParams<{ kind: AdminKind; id: string }>();
  const queryClient = useQueryClient();
  const q = useQuery({ queryKey: ["admin", "item", kind, id], queryFn: ({ signal }) => api<AdminItem>(`/admin/${kind}/${id}`, { signal }) });
  // Reject presets come with the queue.
  const presets = useQuery({ queryKey: ["admin", "queue", kind], queryFn: () => api<AdminQueue>("/admin/queue", { params: { kind } }) });
  const [notice, setNotice] = useState<string | null>(null);
  const [rejecting, setRejecting] = useState(false);
  const [premiumUntil, setPremiumUntil] = useState<string | null>(null);

  if (q.isPending) return <Loading />;
  if (q.isError) return <ErrorState message={q.error.message} onRetry={() => q.refetch()} />;
  const item = q.data;
  const orgId = item.kind === "organization" ? item.id : item.organization.id;
  const until = premiumUntil ?? item.premium_until?.slice(0, 10) ?? "";

  const run = async (fn: () => Promise<string | null | undefined>) => {
    try {
      setNotice((await fn()) ?? null);
    } catch (e) {
      setNotice(e instanceof ApiError ? e.message : t.errors.generic);
    }
    await refreshAdmin(queryClient);
  };

  const edit = () => {
    const pathname = item.kind === "event" ? "/dashboard/event" : item.kind === "offer" ? "/dashboard/offer" : "/dashboard/profile";
    router.push({ pathname, params: { id: String(item.id), admin: "1" } });
  };

  return (
    <ScrollView contentContainerStyle={{ padding: space.lg, gap: space.md, paddingBottom: space.xxl * 2 }}>
      <Stack.Screen options={{ title: t.admin.kinds[item.kind] }} />
      <Notice message={notice} />
      <AdminItemCard item={item}>
        {item.status !== "approved" ? <SmallButton icon="check" label={t.admin.approve} onPress={() => run(async () => {
          const r = await adminApi.approve(item.kind, item.id);
          return [r.message, r.note].filter(Boolean).join(" ");
        })} /> : null}
        {item.status !== "rejected" ? <SmallButton icon="x" label={t.admin.reject} onPress={() => setRejecting(true)} danger /> : null}
        {item.kind !== "organization" ? <SmallButton icon="star" label={item.is_featured ? t.admin.tipOff : t.admin.tip}
          onPress={() => run(async () => ((await adminApi.feature(item.kind, item.id)).is_featured ? t.admin.tipOn : t.admin.tipOff))} /> : null}
        <SmallButton icon="edit-2" label={t.admin.edit} onPress={edit} />
        <SmallButton icon="globe" label={t.places.website} onPress={() => openWeb(item.web_url)} />
      </AdminItemCard>

      {/* Premium belongs to the organisation (also shown on its events and offers). */}
      <Card style={{ padding: space.md, gap: space.md }}>
        <AppText variant="heading" style={{ fontSize: 16 }}>{t.admin.premium}: {item.organization.name}</AppText>
        <DateTimeField label={t.admin.premiumUntil} mode="date" value={until} onChange={setPremiumUntil} optional placeholder={t.forms.optional} />
        <View style={{ flexDirection: "row", gap: space.sm, flexWrap: "wrap" }}>
          <SmallButton icon="award" label={t.admin.premiumSave} onPress={() => run(async () => {
            const r = await adminApi.premium(orgId, until || null);
            return r.is_premium ? `${t.admin.premium} ✓` : null;
          })} />
          {item.is_premium ? <SmallButton icon="slash" label={t.admin.premiumOff} onPress={() => run(async () => {
            await adminApi.premium(orgId, null, true);
            setPremiumUntil("");
            return t.admin.premiumOff;
          })} /> : null}
        </View>
      </Card>

      <View style={{ alignItems: "flex-start" }}>
        <SmallButton icon="trash-2" label={t.admin.delete} danger onPress={() => confirm(t.admin.delete, t.admin.deleteConfirm(itemLabel(item)), t.admin.delete, () => void (async () => {
          try {
            await adminApi.remove(item.kind, item.id);
            await refreshAdmin(queryClient);
            goBack("/admin");
          } catch (e) {
            setNotice(e instanceof ApiError ? e.message : t.errors.generic);
          }
        })())} />
      </View>

      <RejectDialog
        visible={rejecting}
        label={itemLabel(item)}
        presets={presets.data?.reject_presets ?? []}
        onClose={() => setRejecting(false)}
        onSend={async (reason) => {
          try {
            const res = await adminApi.reject(item.kind, item.id, reason);
            setRejecting(false);
            setNotice(res.message);
            await refreshAdmin(queryClient);
            return null;
          } catch (e) {
            return e instanceof ApiError ? (e.fields.reason?.[0] ?? e.message) : t.errors.generic;
          }
        }}
      />
    </ScrollView>
  );
}
