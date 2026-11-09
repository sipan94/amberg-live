/** Forgotten password: the server mails a link; the new password is set on the website. */
import { Stack } from "expo-router";
import { useState } from "react";

import { FormError, Notice, TextField } from "@/components/form";
import { FormScreen } from "@/components/FormScreen";
import { AppText, Button } from "@/components/ui";
import { t } from "@/i18n/de";
import { api, ApiError } from "@/lib/api";
import type { FieldErrors } from "@/lib/forms";

export default function ForgotPasswordScreen() {
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fields, setFields] = useState<FieldErrors>({});
  const [done, setDone] = useState<string | null>(null);

  const submit = async () => {
    setBusy(true);
    setError(null);
    setFields({});
    try {
      setDone((await api<{ message: string }>("/auth/forgot-password", { method: "POST", body: { email: email.trim() } })).message);
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
      <Stack.Screen options={{ title: t.auth.forgotTitle }} />
      <AppText muted>{t.auth.forgotIntro}</AppText>
      {done ? <Notice message={done} /> : (
        <>
          <FormError message={error} />
          <TextField label={t.auth.email} value={email} onChangeText={setEmail} error={fields.email}
            keyboardType="email-address" autoCapitalize="none" autoComplete="email" autoCorrect={false} returnKeyType="send" onSubmitEditing={submit} />
          <Button title={t.auth.sendLink} onPress={submit} loading={busy} />
        </>
      )}
    </FormScreen>
  );
}
