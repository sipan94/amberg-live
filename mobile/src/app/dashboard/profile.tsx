/** Create / edit the business or club profile (POST/PUT /me/organization). */
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Stack, useLocalSearchParams } from "expo-router";
import { useEffect, useState } from "react";
import { Alert, View } from "react-native";

import { ChoiceChips, FormError, ImageField, SwitchRow, TextField } from "@/components/form";
import { FormScreen } from "@/components/FormScreen";
import { AppText, Button, ErrorState, Loading } from "@/components/ui";
import { t } from "@/i18n/de";
import { api } from "@/lib/api";
import { goBack } from "@/lib/nav";
import { useAuth } from "@/lib/auth";
import { FieldErrors, PickedImage, submitForm } from "@/lib/forms";
import type { FormOptions, MyOrganization, Overview, SaveResult } from "@/lib/types";
import { space } from "@/theme";

export default function ProfileScreen() {
  const queryClient = useQueryClient();
  const { refresh } = useAuth();
  const options = useQuery({ queryKey: ["form-options"], queryFn: () => api<FormOptions>("/me/form-options"), staleTime: 60 * 60_000 });
  const { id, admin } = useLocalSearchParams<{ id?: string; admin?: string }>();
  const asAdmin = admin === "1" && !!id; // admin edits any profile; status stays as it is
  // The own profile comes with the overview; an admin loads the chosen one.
  const overview = useQuery({
    queryKey: asAdmin ? ["admin", "item", "organization", id] : ["overview"],
    queryFn: async () => (asAdmin
      ? { organization: await api<MyOrganization>(`/admin/organization/${id}`) }
      : await api<Overview>("/me/overview")),
  });
  const org = (overview.data?.organization ?? null) as MyOrganization | null;

  const [v, setV] = useState({ name: "", org_type: "business", description: "", address: "", phone: "", email: "", website: "" });
  const [hours, setHours] = useState<Record<string, string>>({});
  const [rights, setRights] = useState(false);
  const [logo, setLogo] = useState<PickedImage | null>(null);
  const [cover, setCover] = useState<PickedImage | null>(null);
  const [removeLogo, setRemoveLogo] = useState(false);
  const [removeCover, setRemoveCover] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fields, setFields] = useState<FieldErrors>({});
  const [loaded, setLoaded] = useState(false);

  // Fill the form once with the saved profile.
  useEffect(() => {
    if (loaded || !overview.data) return;
    if (org) {
      setV({ name: org.name, org_type: org.type, description: org.description_text, address: org.address ?? "",
        phone: org.phone ?? "", email: org.email ?? "", website: org.website ?? "" });
      setHours(org.opening_hours_raw);
    }
    setLoaded(true);
  }, [overview.data, org, loaded]);

  if (options.isPending || overview.isPending) return <Loading />;
  if (options.isError) return <ErrorState message={options.error.message} onRetry={() => options.refetch()} />;
  if (overview.isError) return <ErrorState message={overview.error.message} onRetry={() => overview.refetch()} />;
  const set = (k: keyof typeof v) => (val: string) => setV((s) => ({ ...s, [k]: val }));

  const submit = async () => {
    setBusy(true);
    setError(null);
    setFields({});
    const res = await submitForm<SaveResult<MyOrganization>>(asAdmin ? `/admin/organization/${id}` : "/me/organization", org ? "PUT" : "POST", {
      ...v,
      ...Object.fromEntries(options.data.weekdays.map((d) => [`hours_${d.key}`, hours[d.key] ?? ""])),
      remove_logo: removeLogo, remove_cover: removeCover, rights_confirmed: rights,
    }, { logo, cover });
    setBusy(false);
    if (!res.ok) {
      setError(res.error);
      setFields(res.fields);
      return;
    }
    await queryClient.invalidateQueries({ queryKey: asAdmin ? ["admin"] : ["overview"] });
    if (!asAdmin) void refresh();
    Alert.alert(t.dashboard.profile, res.data.message);
    goBack(asAdmin ? "/admin" : "/dashboard");
  };

  return (
    <FormScreen>
      <Stack.Screen options={{ title: org ? t.dashboard.editProfile : t.dashboard.createProfile }} />
      <FormError message={error} />
      <TextField label={t.fields.name} value={v.name} onChangeText={set("name")} error={fields.name} />
      <ChoiceChips label={t.fields.type} options={options.data.org_types} value={v.org_type} onChange={set("org_type")} error={fields.org_type} />
      <TextField label={t.fields.description} value={v.description} onChangeText={set("description")} error={fields.description} multiline />
      <TextField label={t.fields.address} value={v.address} onChangeText={set("address")} error={fields.address} autoComplete="street-address" />
      <TextField label={t.fields.phone} value={v.phone} onChangeText={set("phone")} error={fields.phone} keyboardType="phone-pad" />
      <TextField label={t.fields.email} value={v.email} onChangeText={set("email")} error={fields.email} keyboardType="email-address" autoCapitalize="none" autoCorrect={false} />
      <TextField label={t.fields.website} value={v.website} onChangeText={set("website")} error={fields.website} keyboardType="url" autoCapitalize="none" autoCorrect={false} placeholder="https://" />
      <ImageField label={t.fields.logo} currentUrl={org?.logo?.small} picked={logo} onPick={setLogo} removed={removeLogo} onRemove={setRemoveLogo} error={fields.logo} aspect={[1, 1]} />
      <ImageField label={t.fields.cover} currentUrl={org?.cover_image?.url} picked={cover} onPick={setCover} removed={removeCover} onRemove={setRemoveCover} error={fields.cover} aspect={[16, 9]} />

      <View style={{ gap: space.sm }}>
        <AppText variant="heading" style={{ fontSize: 16 }}>{t.fields.hours}</AppText>
        {options.data.weekdays.map((d) => (
          <TextField key={d.key} label={d.label} value={hours[d.key] ?? ""} placeholder={t.fields.hoursHint}
            onChangeText={(val) => setHours((h) => ({ ...h, [d.key]: val }))} error={fields[`hours_${d.key}`]} />
        ))}
      </View>

      {!asAdmin ? <SwitchRow label={options.data.rights_label} value={rights} onChange={setRights} error={fields.rights_confirmed} /> : null}
      {!asAdmin ? <AppText variant="small" muted>{options.data.review_note}</AppText> : null}
      <Button title={asAdmin ? t.forms.save : t.forms.submit} onPress={submit} loading={busy} />
    </FormScreen>
  );
}
