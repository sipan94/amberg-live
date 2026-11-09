/** Login for businesses, clubs and admins. */
import { router, Stack } from "expo-router";
import { useState } from "react";
import { Pressable } from "react-native";

import { LinkText } from "@/components/detail";
import { FormError, TextField } from "@/components/form";
import { FormScreen } from "@/components/FormScreen";
import { AppText, Button } from "@/components/ui";
import { t } from "@/i18n/de";
import { ApiError } from "@/lib/api";
import { goBack } from "@/lib/nav";
import { useAuth } from "@/lib/auth";
import type { FieldErrors } from "@/lib/forms";

export default function LoginScreen() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fields, setFields] = useState<FieldErrors>({});

  const submit = async () => {
    setBusy(true);
    setError(null);
    setFields({});
    try {
      await login(email.trim(), password);
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
      <Stack.Screen options={{ title: t.auth.loginTitle }} />
      <AppText muted>{t.auth.loginIntro}</AppText>
      <FormError message={error} />
      <TextField label={t.auth.email} value={email} onChangeText={setEmail} error={fields.email}
        keyboardType="email-address" autoCapitalize="none" autoComplete="email" textContentType="username" autoCorrect={false} />
      <TextField label={t.auth.password} value={password} onChangeText={setPassword} error={fields.password}
        secureTextEntry autoComplete="current-password" textContentType="password" returnKeyType="go" onSubmitEditing={submit} />
      <Button title={t.auth.login} onPress={submit} loading={busy} />
      <Pressable onPress={() => router.push("/forgot-password")} accessibilityRole="link" hitSlop={8}>
        <LinkText>{t.auth.forgot}</LinkText>
      </Pressable>
      <Pressable onPress={() => router.replace("/register")} accessibilityRole="link" hitSlop={8}>
        <LinkText>{t.auth.noAccount}</LinkText>
      </Pressable>
    </FormScreen>
  );
}
