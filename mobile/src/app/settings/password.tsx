/** Change password. The server logs out all other devices afterwards. */
import { Stack } from "expo-router";
import { useState } from "react";
import { Alert } from "react-native";

import { FormError, TextField } from "@/components/form";
import { FormScreen } from "@/components/FormScreen";
import { AppText, Button } from "@/components/ui";
import { t } from "@/i18n/de";
import { api, ApiError } from "@/lib/api";
import { goBack } from "@/lib/nav";
import type { FieldErrors } from "@/lib/forms";

export default function ChangePasswordScreen() {
  const [current, setCurrent] = useState("");
  const [password, setPassword] = useState("");
  const [password2, setPassword2] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fields, setFields] = useState<FieldErrors>({});

  const submit = async () => {
    setBusy(true);
    setError(null);
    setFields({});
    try {
      const res = await api<{ message: string }>("/auth/change-password", {
        method: "POST", body: { current_password: current, password, password2 },
      });
      Alert.alert(t.settings.changePassword, res.message);
      goBack("/account");
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
      <Stack.Screen options={{ title: t.settings.changePassword }} />
      <AppText muted>{t.settings.otherDevices}</AppText>
      <FormError message={error} />
      <TextField label={t.settings.currentPassword} value={current} onChangeText={setCurrent} error={fields.current_password}
        secureTextEntry autoComplete="current-password" textContentType="password" />
      <TextField label={t.settings.newPassword} value={password} onChangeText={setPassword} error={fields.password}
        hint={t.auth.passwordHint} secureTextEntry autoComplete="new-password" textContentType="newPassword" />
      <TextField label={t.auth.password2} value={password2} onChangeText={setPassword2} error={fields.password2}
        secureTextEntry autoComplete="new-password" textContentType="newPassword" />
      <Button title={t.forms.save} onPress={submit} loading={busy} />
    </FormScreen>
  );
}
