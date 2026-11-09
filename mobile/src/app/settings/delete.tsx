/** DSGVO: delete the account with all content and images, right from the app. */
import { useQueryClient } from "@tanstack/react-query";
import { router, Stack } from "expo-router";
import { useState } from "react";
import { Alert } from "react-native";

import { FormError, SwitchRow, TextField } from "@/components/form";
import { FormScreen } from "@/components/FormScreen";
import { AppText, Button } from "@/components/ui";
import { t } from "@/i18n/de";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { FieldErrors } from "@/lib/forms";

export default function DeleteAccountScreen() {
  const { logout } = useAuth();
  const queryClient = useQueryClient();
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fields, setFields] = useState<FieldErrors>({});

  const submit = async () => {
    setBusy(true);
    setError(null);
    setFields({});
    try {
      const res = await api<{ message: string }>("/auth/delete-account", { method: "POST", body: { password, confirm } });
      await logout(); // the token is gone with the account; this clears it on the phone
      queryClient.clear();
      Alert.alert(t.settings.deleteAccount, res.message);
      router.dismissTo("/account");
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
    <FormScreen>
      <Stack.Screen options={{ title: t.settings.deleteAccount }} />
      <AppText>{t.settings.deleteIntro}</AppText>
      <FormError message={error} />
      <TextField label={t.auth.password} value={password} onChangeText={setPassword} error={fields.password}
        secureTextEntry autoComplete="current-password" textContentType="password" />
      <SwitchRow label={t.settings.deleteConfirm} value={confirm} onChange={setConfirm} error={fields.confirm} />
      <Button title={t.settings.deleteButton} onPress={submit} loading={busy} disabled={!confirm || !password} />
    </FormScreen>
  );
}
