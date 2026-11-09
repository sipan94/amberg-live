/** Create / edit / delete an event (same fields and checks as the website's form). */
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Stack, useLocalSearchParams } from "expo-router";
import { useEffect, useState } from "react";
import { Alert, Platform, View } from "react-native";

import { ChoiceChips, DateTimeField, FormError, ImageField, SmallButton, SwitchRow, TextField } from "@/components/form";
import { FormScreen } from "@/components/FormScreen";
import { AppText, Button, ErrorState, Loading } from "@/components/ui";
import { t } from "@/i18n/de";
import { api, ApiError } from "@/lib/api";
import { goBack } from "@/lib/nav";
import { FieldErrors, PickedImage, submitForm } from "@/lib/forms";
import type { FormOptions, MyEvent, Overview, SaveResult } from "@/lib/types";
import { space } from "@/theme";

const split = (iso: string | null) => (iso ? { date: iso.slice(0, 10), time: iso.slice(11, 16) } : { date: "", time: "" });

export default function EventFormScreen() {
  const { id, admin } = useLocalSearchParams<{ id?: string; admin?: string }>();
  const editing = !!id;
  const asAdmin = admin === "1"; // admin edits any entry; status stays as it is
  const itemPath = asAdmin ? `/admin/event/${id}` : `/me/events/${id}`;
  const queryClient = useQueryClient();
  const options = useQuery({ queryKey: ["form-options"], queryFn: () => api<FormOptions>("/me/form-options"), staleTime: 60 * 60_000 });
  const overview = useQuery({ queryKey: ["overview"], queryFn: () => api<Overview>("/me/overview"), enabled: !editing && !asAdmin });
  const existing = useQuery({ queryKey: ["my-event", id], queryFn: () => api<MyEvent>(itemPath), enabled: editing });

  const [v, setV] = useState({
    title: "", description: "", start_date: "", start_time: "", end_date: "", end_time: "",
    recurrence: "none", recurrence_until: "", location_name: "", address: "", price_info: "",
  });
  const [categoryId, setCategoryId] = useState<number | null>(null);
  const [isFree, setIsFree] = useState(true);
  const [rights, setRights] = useState(false);
  const [image, setImage] = useState<PickedImage | null>(null);
  const [removeImage, setRemoveImage] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fields, setFields] = useState<FieldErrors>({});
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (loaded) return;
    if (editing && existing.data) {
      const e = existing.data;
      const s = split(e.start), en = split(e.end);
      setV({ title: e.title, description: e.description_text, start_date: s.date, start_time: s.time, end_date: en.date, end_time: en.time,
        recurrence: e.recurrence, recurrence_until: e.recurrence_until ?? "", location_name: e.location_name, address: e.address ?? "", price_info: e.price_info ?? "" });
      setCategoryId(e.category_id);
      setIsFree(e.is_free);
      setLoaded(true);
    } else if (!editing && overview.data) {
      // New event: the organisation's own place as a starting point (like the website).
      const org = overview.data.organization;
      setV((s) => ({ ...s, location_name: org?.name ?? "", address: org?.address ?? "" }));
      setLoaded(true);
    }
  }, [editing, existing.data, overview.data, loaded]);

  const pending = options.isPending || (editing ? existing.isPending : overview.isPending);
  if (pending) return <Loading />;
  const failed = options.error ?? existing.error ?? overview.error;
  if (failed) return <ErrorState message={failed.message} onRetry={() => { void options.refetch(); void existing.refetch(); }} />;
  const opts = options.data!;
  const set = (k: keyof typeof v) => (val: string) => setV((s) => ({ ...s, [k]: val }));

  const submit = async () => {
    setBusy(true);
    setError(null);
    setFields({});
    const res = await submitForm<SaveResult<MyEvent>>(editing ? itemPath : "/me/events", editing ? "PUT" : "POST", {
      ...v, category_id: categoryId, is_free: isFree, remove_image: removeImage, rights_confirmed: rights,
    }, { image });
    setBusy(false);
    if (!res.ok) {
      setError(res.error);
      setFields(res.fields);
      return;
    }
    await queryClient.invalidateQueries({ queryKey: asAdmin ? ["admin"] : ["overview"] });
    queryClient.removeQueries({ queryKey: ["my-event", id] });
    Alert.alert(t.dashboard.events, res.data.message);
    goBack(asAdmin ? "/admin" : "/dashboard");
  };

  const remove = () => {
    const go = async () => {
      try {
        await api(itemPath, { method: "DELETE" });
        await queryClient.invalidateQueries({ queryKey: asAdmin ? ["admin"] : ["overview"] });
        goBack(asAdmin ? "/admin" : "/dashboard");
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
      <Stack.Screen options={{ title: editing ? t.dashboard.editEvent : t.dashboard.newEvent }} />
      <FormError message={error} />
      <TextField label={t.fields.title} value={v.title} onChangeText={set("title")} error={fields.title} />
      <ChoiceChips label={t.fields.category} options={opts.categories.map((c) => ({ value: c.id, label: c.name }))}
        value={categoryId} onChange={setCategoryId} error={fields.category_id} />
      <TextField label={t.fields.description} value={v.description} onChangeText={set("description")} error={fields.description} multiline />

      <Row>
        <DateTimeField label={t.fields.startDate} mode="date" value={v.start_date} onChange={set("start_date")} error={fields.start_date} />
        <DateTimeField label={t.fields.startTime} mode="time" value={v.start_time} onChange={set("start_time")} error={fields.start_time} />
      </Row>
      <Row>
        <DateTimeField label={t.fields.endDate} mode="date" value={v.end_date} onChange={set("end_date")} error={fields.end_date} optional placeholder={t.forms.optional} />
        <DateTimeField label={t.fields.endTime} mode="time" value={v.end_time} onChange={set("end_time")} error={fields.end_time} optional placeholder={t.forms.optional} />
      </Row>

      <ChoiceChips label={t.fields.recurrence} options={opts.recurrence} value={v.recurrence} onChange={set("recurrence")} error={fields.recurrence} />
      {v.recurrence !== "none" ? (
        <DateTimeField label={t.fields.recurrenceUntil} mode="date" value={v.recurrence_until} onChange={set("recurrence_until")}
          error={fields.recurrence_until} optional placeholder={t.forms.optional} />
      ) : null}

      <TextField label={t.fields.location} value={v.location_name} onChangeText={set("location_name")} error={fields.location_name} />
      <TextField label={t.fields.address} value={v.address} onChangeText={set("address")} error={fields.address} />
      <SwitchRow label={t.fields.isFree} value={isFree} onChange={setIsFree} error={fields.is_free} />
      <TextField label={t.fields.priceInfo} value={v.price_info} onChangeText={set("price_info")} error={fields.price_info} placeholder={t.forms.optional} />
      <ImageField label={t.fields.image} currentUrl={existing.data?.image?.small} picked={image} onPick={setImage}
        removed={removeImage} onRemove={setRemoveImage} error={fields.image} aspect={[16, 9]} />

      {!asAdmin ? <SwitchRow label={opts.rights_label} value={rights} onChange={setRights} error={fields.rights_confirmed} /> : null}
      {!asAdmin ? <AppText variant="small" muted>{opts.review_note}</AppText> : null}
      <Button title={asAdmin ? t.forms.save : t.forms.submit} onPress={submit} loading={busy} />
      {editing ? <View style={{ alignItems: "flex-start" }}><SmallButton icon="trash-2" label={t.forms.delete} onPress={remove} danger /></View> : null}
    </FormScreen>
  );
}

function Row({ children }: { children: React.ReactNode }) {
  return <View style={{ flexDirection: "row", gap: space.md }}>{Array.isArray(children) ? children.map((c, i) => <View key={i} style={{ flex: 1 }}>{c}</View>) : children}</View>;
}
