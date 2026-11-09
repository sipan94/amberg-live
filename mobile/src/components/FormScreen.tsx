/** Scrollable screen for forms that moves up with the keyboard. */
import { ReactNode } from "react";
import { KeyboardAvoidingView, Platform, ScrollView } from "react-native";

import { space } from "@/theme";

export function FormScreen({ children }: { children: ReactNode }) {
  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : undefined} keyboardVerticalOffset={90}>
      <ScrollView
        contentContainerStyle={{ padding: space.lg, gap: space.lg, paddingBottom: space.xxl * 2 }}
        keyboardShouldPersistTaps="handled"
        keyboardDismissMode="on-drag"
      >
        {children}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
