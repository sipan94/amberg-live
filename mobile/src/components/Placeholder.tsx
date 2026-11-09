/** Temporary screen for parts that come in the next phases. */
import { View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { t } from "@/i18n/de";
import { space } from "@/theme";
import { AppText, Icon } from "./ui";

export function Placeholder({ title, icon }: { title: string; icon: React.ComponentProps<typeof Icon>["name"] }) {
  const insets = useSafeAreaInsets();
  return (
    <View style={{ flex: 1, paddingTop: insets.top + space.lg, paddingHorizontal: space.lg }}>
      <AppText variant="title" accessibilityRole="header">{title}</AppText>
      <View style={{ flex: 1, alignItems: "center", justifyContent: "center", gap: space.md }}>
        <Icon name={icon} size={32} />
        <AppText muted>{t.common.soon}</AppText>
      </View>
    </View>
  );
}
