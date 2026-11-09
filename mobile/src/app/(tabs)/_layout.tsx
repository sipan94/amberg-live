import { Feather } from "@expo/vector-icons";
import { Tabs } from "expo-router";
import { ComponentProps } from "react";

import { t } from "@/i18n/de";
import { font, useTheme } from "@/theme";

type IconName = ComponentProps<typeof Feather>["name"];

const TABS: { name: string; title: string; icon: IconName }[] = [
  { name: "index", title: t.tabs.home, icon: "home" },
  { name: "events", title: t.tabs.events, icon: "calendar" },
  { name: "offers", title: t.tabs.offers, icon: "tag" },
  { name: "places", title: t.tabs.places, icon: "map-pin" },
  { name: "account", title: t.tabs.account, icon: "user" },
];

export default function TabLayout() {
  const theme = useTheme();
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        sceneStyle: { backgroundColor: theme.bg },
        tabBarActiveTintColor: theme.accentText,
        tabBarInactiveTintColor: theme.textMuted,
        tabBarStyle: { backgroundColor: theme.tabBar, borderTopColor: theme.cardBorder },
        tabBarLabelStyle: { fontFamily: font.medium, fontSize: 11 },
      }}
    >
      {TABS.map((tab) => (
        <Tabs.Screen
          key={tab.name}
          name={tab.name}
          options={{
            title: tab.title,
            tabBarIcon: ({ color, size }) => <Feather name={tab.icon} color={String(color)} size={size - 2} />,
          }}
        />
      ))}
    </Tabs>
  );
}
