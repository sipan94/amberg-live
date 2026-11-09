/** Filter chips, search field and segmented switch. */
import { ReactNode } from "react";
import { Pressable, ScrollView, Text, TextInput, View } from "react-native";

import { font, radius, space, useTheme } from "@/theme";
import { Icon } from "./ui";

export function Chip({ label, active, onPress, icon }: { label: string; active?: boolean; onPress: () => void; icon?: ReactNode }) {
  const theme = useTheme();
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityState={{ selected: !!active }}
      hitSlop={4}
      style={({ pressed }) => ({
        flexDirection: "row",
        alignItems: "center",
        gap: 6,
        paddingHorizontal: 14,
        paddingVertical: 8,
        borderRadius: radius.pill,
        borderWidth: 1,
        backgroundColor: active ? theme.chipActiveBg : theme.chipBg,
        borderColor: active ? theme.chipActiveBorder : theme.cardBorder,
        opacity: pressed ? 0.8 : 1,
      })}
    >
      {icon}
      <Text style={{ fontFamily: font.medium, fontSize: 14, color: theme.text }}>{label}</Text>
    </Pressable>
  );
}

export function ChipRow({ children }: { children: ReactNode }) {
  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      contentContainerStyle={{ paddingHorizontal: space.lg, gap: space.sm }}
      keyboardShouldPersistTaps="handled"
    >
      {children}
    </ScrollView>
  );
}

export function SearchField({ value, onChangeText, placeholder }: { value: string; onChangeText: (v: string) => void; placeholder: string }) {
  const theme = useTheme();
  return (
    <View
      style={{
        flexDirection: "row",
        alignItems: "center",
        gap: space.sm,
        marginHorizontal: space.lg,
        paddingHorizontal: space.md,
        borderRadius: radius.md,
        borderWidth: 1,
        borderColor: theme.cardBorder,
        backgroundColor: theme.card,
      }}
    >
      <Icon name="search" size={17} color={theme.textMuted} />
      <TextInput
        value={value}
        onChangeText={onChangeText}
        placeholder={placeholder}
        placeholderTextColor={theme.textMuted}
        returnKeyType="search"
        autoCorrect={false}
        clearButtonMode="while-editing"
        accessibilityLabel={placeholder}
        style={{ flex: 1, paddingVertical: 11, fontSize: 16, fontFamily: font.regular, color: theme.text }}
      />
    </View>
  );
}

export function Segmented<T extends string>({ options, value, onChange }: {
  options: { value: T; label: string }[]; value: T; onChange: (v: T) => void;
}) {
  const theme = useTheme();
  return (
    <View
      accessibilityRole="tablist"
      style={{ flexDirection: "row", marginHorizontal: space.lg, padding: 3, borderRadius: radius.md, backgroundColor: theme.dark ? "#24211d" : "#eeece7" }}
    >
      {options.map((o) => {
        const active = o.value === value;
        return (
          <Pressable
            key={o.value}
            onPress={() => onChange(o.value)}
            accessibilityRole="tab"
            accessibilityState={{ selected: active }}
            style={{
              flex: 1,
              alignItems: "center",
              paddingVertical: 8,
              borderRadius: radius.sm + 2,
              backgroundColor: active ? theme.card : "transparent",
              ...(active && !theme.dark ? { shadowColor: "#24211d", shadowOpacity: 0.08, shadowRadius: 3, shadowOffset: { width: 0, height: 1 }, elevation: 1 } : {}),
            }}
          >
            <Text style={{ fontFamily: active ? font.semibold : font.medium, fontSize: 14, color: active ? theme.text : theme.textMuted }}>
              {o.label}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}
