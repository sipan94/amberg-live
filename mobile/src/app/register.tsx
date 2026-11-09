/** Create an account. Same answer for new and existing addresses (like the website). */
import { useQuery } from "@tanstack/react-query";
import { router, Stack } from "expo-router";
import { useState } from "react";
import { Pressable, View } from "react-native";

import { LinkText } from "@/components/detail";
import { FormError, Notice, SwitchRow, TextField } from "@/components/form";
import { FormScreen } from "@/components/FormScreen";
import { Button } from "@/components/ui";
import { t } from "@/i18n/de";
import { api, ApiError } from "@/lib/api";
import type { FieldErrors } from "@/lib/forms";
import { openWeb } from "@/lib/links";
import type { Meta } from "@/lib/types";
import { space } from "@/theme";

export default function RegisterScreen() {
  const meta = useQuery({ queryKey: ["meta"], queryFn: () => api<Meta>("/meta"), staleTime: 60 * 60_000 });
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [password2, setPassword2] = useState("");
  const [terms, setTerms] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fields, setFields] = useState<FieldErrors>({});
  const [done, setDone] = useState<string | null>(null);

  const submit = async () => {
    setBusy(true);
    setError(null);
    setFields({});
    try {
      const res = await api<{ message: string }>("/auth/register", {
        method: "POST", body: { email: email.trim(), password, password2, accept_terms: terms },
      });
      setDone(res.message);
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
      <Stack.Screen options={{ title: t.auth.registerTitle }} />
      {done ? (
        <>
          <Notice message={done} />
          <Button title={t.auth.login} onPress={() => router.replace("/login")} />
        </>
      ) : (
        <>
          <FormError message={error} />
          <TextField label={t.auth.email} value={email} onChangeText={setEmail} error={fields.email}
            keyboardType="email-address" autoCapitalize="none" autoComplete="email" textContentType="username" autoCorrect={false} />
          <TextField label={t.auth.password} value={password} onChangeText={setPassword} error={fields.password}
            hint={t.auth.passwordHint} secureTextEntry autoComplete="new-password" textContentType="newPassword" />
          <TextField label={t.auth.password2} value={password2} onChangeText={setPassword2} error={fields.password2}
            secureTextEntry autoComplete="new-password" textContentType="newPassword" />
          <SwitchRow label={t.auth.acceptTerms} value={terms} onChange={setTerms} error={fields.accept_terms} />
          <View style={{ flexDirection: "row", gap: space.lg }}>
            <Pressable onPress={() => meta.data && openWeb(meta.data.legal.agb)} accessibilityRole="link"><LinkText>{t.auth.readTerms}</LinkText></Pressable>
            <Pressable onPress={() => meta.data && openWeb(meta.data.legal.datenschutz)} accessibilityRole="link"><LinkText>{t.auth.readPrivacy}</LinkText></Pressable>
          </View>
          <Button title={t.auth.register} onPress={submit} loading={busy} />
        </>
      )}
    </FormScreen>
  );
}
