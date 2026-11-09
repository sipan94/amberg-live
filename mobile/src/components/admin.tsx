/** Admin building blocks: item card, reject dialog, small confirm helper. */
import { Image } from "expo-image";
import { useState } from "react";
import { Alert, KeyboardAvoidingView, Modal, Platform, Pressable, ScrollView, Text, View } from "react-native";

import { t } from "@/i18n/de";
import { itemLabel } from "@/lib/admin";
import type { AdminItem } from "@/lib/types";
import { font, radius, space, useTheme } from "@/theme";
import { FormError, TextField } from "./form";
import { AppText, Badge, Button, Card, Icon, StatusBadge } from "./ui";

/** Asks before destructive actions (on the web preview it just goes ahead). */
export function confirm(title: string, message: string, action: string, onYes: () => void) {
  if (Platform.OS === "web") return onYes();
  Alert.alert(title, message, [
    { text: t.forms.cancel, style: "cancel" },
    { text: action, style: "destructive", onPress: onYes },
  ]);
}

const dateTime = (iso: string | null) => {
  if (!iso) return "";
  const d = new Date(iso.endsWith("Z") || iso.includes("+") ? iso : `${iso}Z`);
  return d.toLocaleString("de-DE", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
};

export function AdminItemCard({ item, onPress, children }: { item: AdminItem; onPress?: () => void; children?: React.ReactNode }) {
  const theme = useTheme();
  const img = item.image ?? item.logo ?? null;
  const sub = item.kind === "event" ? item.when
    : item.kind === "offer" ? `${item.valid_from?.split("-").reverse().join(".")}${item.valid_until ? ` – ${item.valid_until.split("-").reverse().join(".")}` : ""}`
    : item.address ?? "";
  return (
    <Card onPress={onPress}>
      {img ? <Image source={{ uri: img.small }} style={{ width: "100%", height: 140 }} contentFit="cover" /> : null}
      <View style={{ padding: space.md, gap: 4 }}>
        <View style={{ flexDirection: "row", gap: 6, flexWrap: "wrap", alignItems: "center" }}>
          <StatusBadge status={item.status} label={item.status_label} />
          {item.is_featured ? <Badge kind="tip">{t.admin.tip}</Badge> : null}
          {item.is_premium ? <Badge kind="premium">{t.admin.premium}</Badge> : null}
        </View>
        <AppText variant="heading" style={{ fontSize: 17 }} numberOfLines={2}>{itemLabel(item)}</AppText>
        {sub ? <AppText variant="small" muted>{sub}</AppText> : null}
        {item.kind !== "organization" ? <AppText variant="small" muted>{item.organization.name}</AppText> : null}
        <AppText variant="small" muted>{t.admin.owner}: {item.owner_email}</AppText>
        {item.submitted_at ? <AppText variant="small" muted>{t.admin.submitted}: {dateTime(item.submitted_at)}</AppText> : null}
        {item.kind !== "organization" && item.organization.status !== "approved" ? (
          <AppText variant="small" style={{ color: theme.danger }}>{t.admin.orgNotApproved}</AppText>
        ) : null}
        {item.description_text ? <AppText variant="small" numberOfLines={4} style={{ marginTop: 4 }}>{item.description_text}</AppText> : null}
        {item.rejection_reason ? <AppText variant="small" style={{ color: theme.danger }}>{t.dashboard.reason}: {item.rejection_reason}</AppText> : null}
        {children ? <View style={{ flexDirection: "row", flexWrap: "wrap", gap: space.sm, marginTop: space.sm }}>{children}</View> : null}
      </View>
    </Card>
  );
}

/** Bottom sheet for a rejection reason; presets are the website's standard reasons. */
export function RejectDialog({ visible, label, presets, onClose, onSend }: {
  visible: boolean; label: string; presets: string[]; onClose: () => void; onSend: (reason: string) => Promise<string | null>;
}) {
  const theme = useTheme();
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const send = async () => {
    setBusy(true);
    setError(await onSend(reason.trim()));
    setBusy(false);
  };
  const close = () => {
    setReason("");
    setError(null);
    onClose();
  };

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={close}>
      <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : undefined} style={{ flex: 1, justifyContent: "flex-end", backgroundColor: "rgba(0,0,0,0.35)" }}>
        <View style={{ backgroundColor: theme.bg, borderTopLeftRadius: radius.lg, borderTopRightRadius: radius.lg, maxHeight: "85%" }}>
          <ScrollView contentContainerStyle={{ padding: space.lg, gap: space.md, paddingBottom: space.xxl }} keyboardShouldPersistTaps="handled">
            <View style={{ flexDirection: "row", alignItems: "center" }}>
              <AppText variant="heading" style={{ flex: 1 }} numberOfLines={2}>{t.admin.rejectTitle}: {label}</AppText>
              <Pressable onPress={close} hitSlop={12} accessibilityRole="button" accessibilityLabel={t.common.close}><Icon name="x" size={22} /></Pressable>
            </View>
            <View style={{ gap: space.sm }}>
              {presets.map((p) => (
                <Pressable key={p} onPress={() => setReason(p)} accessibilityRole="button"
                  style={{ padding: space.md, borderRadius: radius.md, borderWidth: 1, borderColor: reason === p ? theme.chipActiveBorder : theme.cardBorder, backgroundColor: reason === p ? theme.chipActiveBg : theme.card }}>
                  <Text style={{ fontFamily: font.regular, fontSize: 15, color: theme.text }}>{p}</Text>
                </Pressable>
              ))}
            </View>
            <FormError message={error} />
            <TextField label={t.admin.rejectReason} value={reason} onChangeText={setReason} multiline />
            <Button title={t.admin.rejectSend} onPress={send} loading={busy} disabled={reason.length < 5} />
          </ScrollView>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
}
