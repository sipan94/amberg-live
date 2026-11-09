/** Pieces of detail pages: action buttons, info rows, text links. */
import { Pressable, View } from "react-native";

import { font, radius, space, useTheme } from "@/theme";
import { AppText, Icon } from "./ui";

export function Action({ icon, label, onPress, active }: {
  icon: React.ComponentProps<typeof Icon>["name"]; label: string; onPress: () => void; active?: boolean;
}) {
  const theme = useTheme();
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={label}
      style={({ pressed }) => ({
        flex: 1, alignItems: "center", gap: 6, paddingVertical: space.md, borderRadius: radius.md, borderWidth: 1,
        borderColor: active ? theme.chipActiveBorder : theme.cardBorder,
        backgroundColor: active ? theme.chipActiveBg : theme.card,
        opacity: pressed ? 0.8 : 1,
      })}
    >
      <Icon name={icon} size={19} color={active ? theme.accentText : theme.text} />
      <AppText variant="label" numberOfLines={1}>{label}</AppText>
    </Pressable>
  );
}

export function InfoRow({ icon, label, value, extra, last, onPress }: {
  icon: React.ComponentProps<typeof Icon>["name"]; label: string; value: string; extra?: string; last?: boolean; onPress?: () => void;
}) {
  const theme = useTheme();
  const body = (
    <View style={{ flexDirection: "row", gap: space.md, padding: space.md, borderBottomWidth: last ? 0 : 1, borderBottomColor: theme.cardBorder }}>
      <Icon name={icon} size={18} color={theme.textMuted} />
      <View style={{ flex: 1, gap: 2 }}>
        <AppText variant="label" muted>{label}</AppText>
        <AppText selectable={!onPress} style={onPress ? { color: theme.accentText, fontFamily: font.medium } : undefined}>{value}</AppText>
        {extra ? <AppText variant="small" muted selectable>{extra}</AppText> : null}
      </View>
      {onPress ? <Icon name="chevron-right" size={18} color={theme.textMuted} /> : null}
    </View>
  );
  return onPress ? <Pressable onPress={onPress} accessibilityRole="link">{body}</Pressable> : body;
}

export function LinkText({ children }: { children: React.ReactNode }) {
  const theme = useTheme();
  return <AppText style={{ color: theme.accentText, fontFamily: font.medium, textDecorationLine: "underline" }}>{children}</AppText>;
}
