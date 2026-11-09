/** Create / edit / delete an offer. */
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Stack, useLocalSearchParams } from "expo-router";
import { useEffect, useState } from "react";
import { Alert, Platform, View } from "react-native";

import { DateTimeField, FormError, ImageField, SmallButton, SwitchRow, TextField } from "@/components/form";
import { FormScreen } from "@/components/FormScreen";
import { AppText, Button, ErrorState, Loading } from "@/components/ui";
import { t } from "@/i18n/de";
import { api, ApiError } from "@/lib/api";
import { goBack } from "@/lib/nav";
import { FieldErrors, PickedImage, submitForm } from "@/lib/forms";
import type { FormOptions, MyOffer, SaveResult } from "@/lib/types";
import { space } from "@/theme";

const today = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};

export default function OfferFormScreen() {
  const { id } = useLocalSearchParams<{ id?: string }>();
  const editing = !!id;
  const queryClient = useQueryClient();
  const options = useQuery({ queryKey: ["form-options"], queryFn: () => api<FormOptions>("/me/form-options"), staleTime: 60 * 60_000 });
  const existing = useQuery({ queryKey: ["my-offer", id], queryFn: () => api<MyOffer>(`/me/offers/${id}`), enabled: editing });

  const [v, setV] = useState({ title: "", description: "", valid_from: today(), valid_until: "" });
  const [rights, setRights] = useState(false);
  const [image, setImage] = useState<PickedImage | null>(null);
  const [removeImage, setRemoveImage] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fields, setFields] = useState<FieldErrors>({});
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (loaded || !existing.data) return;
    const o = existing.data;
    setV({ title: o.title, description: o.description_text, valid_from: o.valid_from, valid_until: o.valid_until ?? "" });
    setLoaded(true);
  }, [existing.data, loaded]);

  if (options.isPending || (editing && existing.isPending)) return <Loading />;
  const failed = options.error ?? existing.error;
  if (failed) return <ErrorState message={failed.message} onRetry={() => { void options.refetch(); void existing.refetch(); }} />;
  const opts = options.data!;
  const set = (k: keyof typeof v) => (val: string) => setV((s) => ({ ...s, [k]: val }));

  const submit = async () => {
    setBusy(true);
    setError(null);
    setFields({});
    const res = await submitForm<SaveResult<MyOffer>>(editing ? `/me/offers/${id}` : "/me/offers", editing ? "PUT" : "POST", {
      ...v, remove_image: removeImage, rights_confirmed: rights,
    }, { image });
    setBusy(false);
    if (!res.ok) {
      setError(res.error);
      setFields(res.fields);
      return;
    }
    await queryClient.invalidateQueries({ queryKey: ["overview"] });
    queryClient.removeQueries({ queryKey: ["my-offer", id] });
    Alert.alert(t.dashboard.offers, res.data.message);
    goBack("/dashboard");
  };

  const remove = () => {
    const go = async () => {
      try {
        await api(`/me/offers/${id}`, { method: "DELETE" });
        await queryClient.invalidateQueries({ queryKey: ["overview"] });
        goBack("/dashboard");
      } catch (e) {
        setError(e instanceof ApiError ? e.message : t.errors.generic);
      }
    };
    if (Platform.OS === "web") return void go();
    Alert.alert(t.forms.delete, t.dashboard.deleteConfirm(v.title), [
      { text: t.forms.cancel, style: "cancel" },
      { text: t.forms.delete, style: "destructive", onPress: () => void go() },
    ]);
  };

  return (
    <FormScreen>
      <Stack.Screen options={{ title: editing ? t.dashboard.editOffer : t.dashboard.newOffer }} />
      <FormError message={error} />
      <TextField label={t.fields.title} value={v.title} onChangeText={set("title")} error={fields.title} />
      <TextField label={t.fields.description} value={v.description} onChangeText={set("description")} error={fields.description} multiline />
      <View style={{ flexDirection: "row", gap: space.md }}>
        <View style={{ flex: 1 }}>
          <DateTimeField label={t.fields.validFrom} mode="date" value={v.valid_from} onChange={set("valid_from")} error={fields.valid_from} />
        </View>
        <View style={{ flex: 1 }}>
          <DateTimeField label={t.fields.validUntil} mode="date" value={v.valid_until} onChange={set("valid_until")} error={fields.valid_until} optional placeholder={t.forms.optional} />
        </View>
      </View>
      <ImageField label={t.fields.image} currentUrl={existing.data?.image?.small} picked={image} onPick={setImage}
        removed={removeImage} onRemove={setRemoveImage} error={fields.image} aspect={[16, 9]} />
      <SwitchRow label={opts.rights_label} value={rights} onChange={setRights} error={fields.rights_confirmed} />
      <AppText variant="small" muted>{opts.review_note}</AppText>
      <Button title={t.forms.submit} onPress={submit} loading={busy} />
      {editing ? <View style={{ alignItems: "flex-start" }}><SmallButton icon="trash-2" label={t.forms.delete} onPress={remove} danger /></View> : null}
    </FormScreen>
  );
}
