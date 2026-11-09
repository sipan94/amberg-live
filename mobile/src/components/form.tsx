/** Form fields. Error texts come from the server (same German messages as the website). */
import DateTimePicker, { DateTimePickerAndroid } from "@react-native-community/datetimepicker";
import { Image } from "expo-image";
import * as ImagePicker from "expo-image-picker";
import { ReactNode, useState } from "react";
import { Platform, Pressable, Switch, Text, TextInput, TextInputProps, View } from "react-native";

import { t } from "@/i18n/de";
import type { PickedImage } from "@/lib/forms";
import { font, radius, space, useTheme } from "@/theme";
import { AppText, Icon } from "./ui";

export function Field({ label, error, hint, children }: { label: string; error?: string[]; hint?: string; children: ReactNode }) {
  const theme = useTheme();
  return (
    <View style={{ gap: 6 }}>
      <Text style={{ fontFamily: font.medium, fontSize: 14, color: theme.textSoft }}>{label}</Text>
      {children}
      {hint && !error?.length ? <AppText variant="small" muted>{hint}</AppText> : null}
      {error?.map((e) => (
        <Text key={e} style={{ fontFamily: font.regular, fontSize: 14, color: theme.danger }} accessibilityLiveRegion="polite">{e}</Text>
      ))}
    </View>
  );
}

export function TextField({ label, error, hint, multiline, ...rest }: TextInputProps & { label: string; error?: string[]; hint?: string }) {
  const theme = useTheme();
  return (
    <Field label={label} error={error} hint={hint}>
      <TextInput
        {...rest}
        multiline={multiline}
        accessibilityLabel={label}
        placeholderTextColor={theme.textMuted}
        style={{
          fontFamily: font.regular, fontSize: 16, color: theme.text, backgroundColor: theme.card,
          borderWidth: 1, borderColor: error?.length ? theme.danger : theme.cardBorder, borderRadius: radius.md,
          paddingHorizontal: space.md, paddingVertical: 11, minHeight: multiline ? 120 : undefined,
          textAlignVertical: multiline ? "top" : "center",
        }}
      />
    </Field>
  );
}

export function SwitchRow({ label, value, onChange, error }: { label: string; value: boolean; onChange: (v: boolean) => void; error?: string[] }) {
  const theme = useTheme();
  return (
    <Field label="" error={error}>
      <View style={{ flexDirection: "row", alignItems: "center", gap: space.md, marginTop: -6 }}>
        <Switch value={value} onValueChange={onChange} trackColor={{ true: theme.accent }} accessibilityLabel={label} />
        <AppText style={{ flex: 1 }}>{label}</AppText>
      </View>
    </Field>
  );
}

export function ChoiceChips<T extends string | number>({ label, options, value, onChange, error }: {
  label: string; options: { value: T; label: string }[]; value: T | null; onChange: (v: T) => void; error?: string[];
}) {
  const theme = useTheme();
  return (
    <Field label={label} error={error}>
      <View style={{ flexDirection: "row", flexWrap: "wrap", gap: space.sm }}>
        {options.map((o) => {
          const active = o.value === value;
          return (
            <Pressable
              key={String(o.value)}
              onPress={() => onChange(o.value)}
              accessibilityRole="radio"
              accessibilityState={{ checked: active }}
              style={{
                paddingHorizontal: 14, paddingVertical: 8, borderRadius: radius.pill, borderWidth: 1,
                backgroundColor: active ? theme.chipActiveBg : theme.chipBg, borderColor: active ? theme.chipActiveBorder : theme.cardBorder,
              }}
            >
              <Text style={{ fontFamily: font.medium, fontSize: 14, color: theme.text }}>{o.label}</Text>
            </Pressable>
          );
        })}
      </View>
    </Field>
  );
}

// ---- dates and times: values are "YYYY-MM-DD" / "HH:MM" strings, exactly what the server expects ----

const pad = (n: number) => String(n).padStart(2, "0");
const toDateStr = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const toTimeStr = (d: Date) => `${pad(d.getHours())}:${pad(d.getMinutes())}`;

function parse(value: string, mode: "date" | "time"): Date {
  const now = new Date();
  if (mode === "date" && /^\d{4}-\d{2}-\d{2}$/.test(value)) {
    const [y, m, d] = value.split("-").map(Number);
    return new Date(y, m - 1, d, 12);
  }
  if (mode === "time" && /^\d{2}:\d{2}$/.test(value)) {
    const [h, min] = value.split(":").map(Number);
    return new Date(now.getFullYear(), now.getMonth(), now.getDate(), h, min);
  }
  return mode === "time" ? new Date(now.getFullYear(), now.getMonth(), now.getDate(), 19, 0) : now;
}

function display(value: string, mode: "date" | "time") {
  if (!value) return "";
  if (mode === "time") return `${value} Uhr`;
  const [y, m, d] = value.split("-");
  return `${d}.${m}.${y}`;
}

export function DateTimeField({ label, mode, value, onChange, error, optional, placeholder }: {
  label: string; mode: "date" | "time"; value: string; onChange: (v: string) => void; error?: string[]; optional?: boolean; placeholder?: string;
}) {
  const theme = useTheme();
  const [iosOpen, setIosOpen] = useState(false);
  const fmt = mode === "date" ? toDateStr : toTimeStr;

  if (Platform.OS === "web") {
    return <TextField label={label} value={value} onChangeText={onChange} error={error} placeholder={mode === "date" ? "JJJJ-MM-TT" : "HH:MM"} />;
  }

  const open = () => {
    if (Platform.OS === "android") {
      DateTimePickerAndroid.open({ value: parse(value, mode), mode, is24Hour: true, onValueChange: (_e, d) => onChange(fmt(d)) });
    } else {
      setIosOpen((o) => !o);
    }
  };

  return (
    <Field label={label} error={error}>
      <View style={{ flexDirection: "row", gap: space.sm }}>
        <Pressable
          onPress={open}
          accessibilityRole="button"
          accessibilityLabel={`${label}: ${display(value, mode) || placeholder || ""}`}
          style={{
            flex: 1, flexDirection: "row", alignItems: "center", gap: space.sm, backgroundColor: theme.card,
            borderWidth: 1, borderColor: error?.length ? theme.danger : theme.cardBorder, borderRadius: radius.md, paddingHorizontal: space.md, paddingVertical: 12,
          }}
        >
          <Icon name={mode === "date" ? "calendar" : "clock"} size={17} color={theme.textMuted} />
          <Text style={{ fontFamily: font.regular, fontSize: 16, color: value ? theme.text : theme.textMuted }}>
            {display(value, mode) || placeholder || "–"}
          </Text>
        </Pressable>
        {optional && value ? (
          <Pressable onPress={() => onChange("")} accessibilityRole="button" accessibilityLabel={t.forms.clear}
            style={{ justifyContent: "center", paddingHorizontal: space.md, borderRadius: radius.md, borderWidth: 1, borderColor: theme.cardBorder, backgroundColor: theme.card }}>
            <Icon name="x" size={17} color={theme.textMuted} />
          </Pressable>
        ) : null}
      </View>
      {Platform.OS === "ios" && iosOpen ? (
        <DateTimePicker
          value={parse(value, mode)}
          mode={mode}
          display={mode === "date" ? "inline" : "spinner"}
          locale="de-DE"
          themeVariant={theme.dark ? "dark" : "light"}
          accentColor={theme.accent}
          onValueChange={(_e, d) => onChange(fmt(d))}
        />
      ) : null}
    </Field>
  );
}

// ---- images ---------------------------------------------------------------------------------

export function ImageField({ label, currentUrl, picked, onPick, removed, onRemove, error, aspect }: {
  label: string; currentUrl?: string | null; picked: PickedImage | null; onPick: (img: PickedImage | null) => void;
  removed: boolean; onRemove: (v: boolean) => void; error?: string[]; aspect?: [number, number];
}) {
  const theme = useTheme();
  const preview = picked?.uri ?? (removed ? null : currentUrl);

  const choose = async () => {
    const res = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ["images"], allowsEditing: true, aspect, quality: 0.85 });
    if (res.canceled || !res.assets?.length) return;
    const a = res.assets[0];
    onPick({ uri: a.uri, name: a.fileName || `bild.${(a.mimeType || "image/jpeg").split("/")[1]}`, type: a.mimeType || "image/jpeg", file: a.file });
    onRemove(false);
  };

  return (
    <Field label={label} error={error} hint={t.forms.imageHint}>
      {preview ? (
        <Image source={{ uri: preview }} style={{ width: "100%", height: 170, borderRadius: radius.md }} contentFit="cover" />
      ) : null}
      <View style={{ flexDirection: "row", gap: space.sm }}>
        <SmallButton icon="image" label={preview ? t.forms.changeImage : t.forms.chooseImage} onPress={choose} />
        {preview ? (
          <SmallButton icon="trash-2" label={t.forms.removeImage} onPress={() => { onPick(null); onRemove(!!currentUrl); }} />
        ) : null}
      </View>
    </Field>
  );
}

export function SmallButton({ icon, label, onPress, danger }: { icon: React.ComponentProps<typeof Icon>["name"]; label: string; onPress: () => void; danger?: boolean }) {
  const theme = useTheme();
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      style={({ pressed }) => ({
        flexDirection: "row", alignItems: "center", gap: 6, paddingHorizontal: space.md, paddingVertical: 9,
        borderRadius: radius.md, borderWidth: 1, borderColor: danger ? theme.danger : theme.cardBorder, backgroundColor: theme.card, opacity: pressed ? 0.8 : 1,
      })}
    >
      <Icon name={icon} size={16} color={danger ? theme.danger : theme.text} />
      <Text style={{ fontFamily: font.medium, fontSize: 14, color: danger ? theme.danger : theme.text }}>{label}</Text>
    </Pressable>
  );
}

/** Red box above a form for errors that belong to no single field. */
export function FormError({ message }: { message?: string | null }) {
  const theme = useTheme();
  if (!message) return null;
  return (
    <View accessibilityLiveRegion="polite" style={{ flexDirection: "row", gap: space.sm, padding: space.md, borderRadius: radius.md, backgroundColor: theme.dark ? "rgba(249,112,102,0.12)" : "#fdecea" }}>
      <Icon name="alert-circle" size={18} color={theme.danger} />
      <AppText style={{ flex: 1, color: theme.danger }}>{message}</AppText>
    </View>
  );
}

export function Notice({ message, kind = "success" }: { message?: string | null; kind?: "success" | "info" }) {
  const theme = useTheme();
  if (!message) return null;
  const bg = kind === "success" ? (theme.dark ? "rgba(123,197,138,0.12)" : "#e3f1e5") : theme.highlightBg;
  const fg = kind === "success" ? theme.success : theme.text;
  return (
    <View accessibilityLiveRegion="polite" style={{ flexDirection: "row", gap: space.sm, padding: space.md, borderRadius: radius.md, backgroundColor: bg }}>
      <Icon name={kind === "success" ? "check-circle" : "info"} size={18} color={fg} />
      <AppText style={{ flex: 1, color: fg }}>{message}</AppText>
    </View>
  );
}
