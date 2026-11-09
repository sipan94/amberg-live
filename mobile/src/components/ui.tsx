/** Small building blocks shared by all screens. */
import { Feather } from "@expo/vector-icons";
import { ComponentProps, ReactNode } from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text, TextProps, View, ViewStyle } from "react-native";

import { t } from "@/i18n/de";
import { font, radius, space, Theme, useTheme } from "@/theme";

type IconName = ComponentProps<typeof Feather>["name"];

/** Category icon names from the website (forms/admin.py CATEGORY_ICONS) → Feather icons. */
const CATEGORY_ICONS: Record<string, IconName> = {
  music: "music", family: "users", sport: "activity", food: "coffee", culture: "book-open",
  market: "shopping-bag", club: "flag", other: "grid", star: "star", heart: "heart",
  calendar: "calendar", tag: "tag", store: "shopping-cart", globe: "globe",
};

export function categoryIcon(name?: string | null): IconName {
  return (name && CATEGORY_ICONS[name]) || "grid";
}

export function Icon({ name, size = 18, color }: { name: IconName; size?: number; color?: string }) {
  const theme = useTheme();
  return <Feather name={name} size={size} color={color ?? theme.text} />;
}

type Variant = "title" | "heading" | "body" | "small" | "label";

export function AppText({ variant = "body", muted, style, ...rest }: TextProps & { variant?: Variant; muted?: boolean }) {
  const theme = useTheme();
  return (
    <Text
      {...rest}
      maxFontSizeMultiplier={1.6}
      style={[textStyles[variant], { color: muted ? theme.textMuted : theme.text }, style]}
    />
  );
}

const textStyles = StyleSheet.create({
  title: { fontFamily: font.bold, fontSize: 28, lineHeight: 34, letterSpacing: -0.4 },
  heading: { fontFamily: font.semibold, fontSize: 19, lineHeight: 25, letterSpacing: -0.2 },
  body: { fontFamily: font.regular, fontSize: 16, lineHeight: 23 },
  small: { fontFamily: font.regular, fontSize: 14, lineHeight: 19 },
  label: { fontFamily: font.medium, fontSize: 12, lineHeight: 16, letterSpacing: 0.2 },
});

export function Card({ children, highlight, style, onPress }: {
  children: ReactNode; highlight?: boolean; style?: ViewStyle; onPress?: () => void;
}) {
  const theme = useTheme();
  const base = [cardStyle(theme, highlight), style];
  if (!onPress) return <View style={base}>{children}</View>;
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      style={({ pressed }) => [...base, pressed && { opacity: 0.85, transform: [{ scale: 0.985 }] }]}
    >
      {children}
    </Pressable>
  );
}

function cardStyle(theme: Theme, highlight?: boolean): ViewStyle {
  return {
    backgroundColor: highlight ? theme.highlightBg : theme.card,
    borderColor: highlight ? theme.highlightBorder : theme.cardBorder,
    borderWidth: StyleSheet.hairlineWidth * 2,
    borderRadius: radius.lg,
    overflow: "hidden",
    ...(theme.dark ? {} : { shadowColor: "#24211d", shadowOpacity: 0.06, shadowRadius: 8, shadowOffset: { width: 0, height: 2 }, elevation: 1 }),
  };
}

type BadgeKind = "tip" | "premium" | "neutral" | "now" | "danger";

export function Badge({ kind, children }: { kind: BadgeKind; children: ReactNode }) {
  const theme = useTheme();
  const colors: Record<BadgeKind, { bg: string; fg: string }> = theme.dark
    ? { tip: { bg: "rgba(227,169,43,0.2)", fg: "#f9edcc" }, premium: { bg: "#f2d894", fg: "#1a1815" },
        neutral: { bg: "#34302b", fg: "#cbc6bd" }, now: { bg: "rgba(123,197,138,0.18)", fg: "#b9e3c1" }, danger: { bg: "rgba(249,112,102,0.16)", fg: "#fda29b" } }
    : { tip: { bg: "#f2d894", fg: "#321f08" }, premium: { bg: "#2a2520", fg: "#f2d894" },
        neutral: { bg: "#eeece7", fg: "#4a4640" }, now: { bg: "#e3f1e5", fg: "#2f6b3a" }, danger: { bg: "#fdecea", fg: "#b42318" } };
  const c = colors[kind];
  return (
    <View style={{ backgroundColor: c.bg, borderRadius: radius.pill, paddingHorizontal: 8, paddingVertical: 2 }}>
      <Text style={{ color: c.fg, fontFamily: font.medium, fontSize: 12, lineHeight: 16 }}>{children}</Text>
    </View>
  );
}

export function Section({ title, action, onAction, children }: {
  title: string; action?: string; onAction?: () => void; children: ReactNode;
}) {
  const theme = useTheme();
  return (
    <View style={{ marginTop: space.xl }}>
      <View style={{ flexDirection: "row", alignItems: "baseline", justifyContent: "space-between", marginBottom: space.md, paddingHorizontal: space.lg }}>
        <AppText variant="heading" accessibilityRole="header">{title}</AppText>
        {action && onAction ? (
          <Pressable onPress={onAction} hitSlop={12} accessibilityRole="link">
            <Text style={{ color: theme.accentText, fontFamily: font.medium, fontSize: 15 }}>{action}</Text>
          </Pressable>
        ) : null}
      </View>
      {children}
    </View>
  );
}

export function Loading() {
  const theme = useTheme();
  return (
    <View style={{ flex: 1, alignItems: "center", justifyContent: "center", padding: space.xxl }}>
      <ActivityIndicator color={theme.accentText} accessibilityLabel={t.common.loading} />
    </View>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <View style={{ flex: 1, alignItems: "center", justifyContent: "center", padding: space.xxl, gap: space.lg }}>
      <Icon name="wifi-off" size={28} />
      <AppText style={{ textAlign: "center" }}>{message}</AppText>
      {onRetry ? <Button title={t.common.retry} onPress={onRetry} /> : null}
    </View>
  );
}

export function Button({ title, onPress, kind = "primary", disabled, loading }: {
  title: string; onPress: () => void; kind?: "primary" | "secondary"; disabled?: boolean; loading?: boolean;
}) {
  const theme = useTheme();
  const primary = kind === "primary";
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled || loading}
      accessibilityRole="button"
      accessibilityState={{ disabled: disabled || loading }}
      style={({ pressed }) => ({
        backgroundColor: primary ? theme.accent : theme.card,
        borderColor: primary ? theme.accent : theme.cardBorder,
        borderWidth: 1,
        borderRadius: radius.md,
        paddingVertical: 12,
        paddingHorizontal: 20,
        alignItems: "center",
        opacity: disabled ? 0.5 : pressed ? 0.85 : 1,
        transform: [{ scale: pressed ? 0.98 : 1 }],
      })}
    >
      {loading ? (
        <ActivityIndicator color={primary ? "#1a1815" : theme.text} />
      ) : (
        <Text style={{ color: primary ? "#1a1815" : theme.text, fontFamily: font.semibold, fontSize: 16 }}>{title}</Text>
      )}
    </Pressable>
  );
}

/** Moderation status from the server: pending (gold), approved (green), rejected (red). */
export function StatusBadge({ status, label }: { status: string; label: string }) {
  const kind: BadgeKind = status === "approved" ? "now" : status === "rejected" ? "danger" : "tip";
  return <Badge kind={kind}>{label}</Badge>;
}
