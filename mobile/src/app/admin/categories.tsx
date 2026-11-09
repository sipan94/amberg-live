/** Categories: add, edit, delete (GET/POST/PUT/DELETE /admin/categories). */
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Stack } from "expo-router";
import { useState } from "react";
import { Pressable, ScrollView, View } from "react-native";

import { confirm } from "@/components/admin";
import { FormError, SmallButton, TextField } from "@/components/form";
import { AppText, Button, Card, categoryIcon, ErrorState, Icon, Loading } from "@/components/ui";
import { t } from "@/i18n/de";
import { refreshAdmin } from "@/lib/admin";
import { api, ApiError } from "@/lib/api";
import type { FieldErrors } from "@/lib/forms";
import type { AdminCategory } from "@/lib/types";
import { radius, space, useTheme } from "@/theme";

type Draft = { id: number | null; name: string; icon: string; color: string; sort_order: string };

export default function CategoriesScreen() {
  const theme = useTheme();
  const queryClient = useQueryClient();
  const q = useQuery({ queryKey: ["admin", "categories"], queryFn: () => api<{ icons: string[]; items: AdminCategory[] }>("/admin/categories") });
  const [draft, setDraft] = useState<Draft | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [fields, setFields] = useState<FieldErrors>({});
  const [busy, setBusy] = useState(false);

  if (q.isPending) return <Loading />;
  if (q.isError) return <ErrorState message={q.error.message} onRetry={() => q.refetch()} />;

  const refresh = () => Promise.all([refreshAdmin(queryClient), queryClient.invalidateQueries({ queryKey: ["meta"] })]);
  const open = (c?: AdminCategory) => {
    setError(null);
    setFields({});
    setDraft(c ? { id: c.id, name: c.name, icon: c.icon, color: c.color, sort_order: String(c.sort_order) }
      : { id: null, name: "", icon: q.data.icons[0], color: "#736d63", sort_order: "" });
  };

  const save = async () => {
    if (!draft) return;
    setBusy(true);
    setError(null);
    setFields({});
    try {
      await api(draft.id ? `/admin/categories/${draft.id}` : "/admin/categories", {
        method: draft.id ? "PUT" : "POST",
        body: { name: draft.name, icon: draft.icon, color: draft.color, sort_order: draft.sort_order },
      });
      setDraft(null);
      await refresh();
    } catch (e) {
      if (e instanceof ApiError) {
        setError(e.message);
        setFields(e.fields);
      } else throw e;
    } finally {
      setBusy(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={{ padding: space.lg, gap: space.md, paddingBottom: space.xxl * 2 }} keyboardShouldPersistTaps="handled">
      <Stack.Screen options={{ title: t.admin.categories }} />

      {draft ? (
        <Card style={{ padding: space.lg, gap: space.md }}>
          <AppText variant="heading">{draft.id ? t.admin.editCategory : t.admin.newCategory}</AppText>
          <FormError message={error} />
          <TextField label={t.admin.catName} value={draft.name} onChangeText={(v) => setDraft({ ...draft, name: v })} error={fields.name} />
          <AppText variant="small" muted>{t.admin.catIcon}</AppText>
          <View style={{ flexDirection: "row", flexWrap: "wrap", gap: space.sm }}>
            {q.data.icons.map((i) => (
              <Pressable key={i} onPress={() => setDraft({ ...draft, icon: i })} accessibilityRole="radio" accessibilityLabel={i} accessibilityState={{ checked: draft.icon === i }}
                style={{ width: 44, height: 44, borderRadius: radius.md, alignItems: "center", justifyContent: "center", borderWidth: 1,
                  borderColor: draft.icon === i ? theme.chipActiveBorder : theme.cardBorder, backgroundColor: draft.icon === i ? theme.chipActiveBg : theme.card }}>
                <Icon name={categoryIcon(i)} size={19} color={draft.color} />
              </Pressable>
            ))}
          </View>
          <TextField label={t.admin.catColor} value={draft.color} onChangeText={(v) => setDraft({ ...draft, color: v })} error={fields.color} autoCapitalize="none" autoCorrect={false} />
          <TextField label={t.admin.catSort} value={draft.sort_order} onChangeText={(v) => setDraft({ ...draft, sort_order: v })} error={fields.sort_order} keyboardType="number-pad" />
          <View style={{ flexDirection: "row", gap: space.sm }}>
            <View style={{ flex: 1 }}><Button title={t.forms.save} onPress={save} loading={busy} /></View>
            <View style={{ flex: 1 }}><Button kind="secondary" title={t.forms.cancel} onPress={() => setDraft(null)} /></View>
          </View>
        </Card>
      ) : (
        <Button title={`+ ${t.admin.newCategory}`} onPress={() => open()} />
      )}

      <Card>
        {q.data.items.map((c, i) => (
          <View key={c.id} style={{ flexDirection: "row", alignItems: "center", gap: space.md, padding: space.md, borderBottomWidth: i === q.data.items.length - 1 ? 0 : 1, borderBottomColor: theme.cardBorder }}>
            <Icon name={categoryIcon(c.icon)} size={20} color={c.color} />
            <View style={{ flex: 1 }}>
              <AppText>{c.name}</AppText>
              <AppText variant="small" muted>{t.admin.catEvents(c.events)}</AppText>
            </View>
            <SmallButton icon="edit-2" label={t.admin.edit} onPress={() => open(c)} />
            <Pressable onPress={() => confirm(t.admin.delete, t.admin.deleteConfirm(c.name), t.admin.delete, () => void (async () => {
              try {
                await api(`/admin/categories/${c.id}`, { method: "DELETE" });
                await refresh();
              } catch (e) {
                setError(e instanceof ApiError ? e.message : t.errors.generic);
              }
            })())} hitSlop={8} accessibilityRole="button" accessibilityLabel={`${t.admin.delete}: ${c.name}`}>
              <Icon name="trash-2" size={18} color={theme.danger} />
            </Pressable>
          </View>
        ))}
      </Card>
    </ScrollView>
  );
}
