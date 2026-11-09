import {
  SchibstedGrotesk_400Regular,
  SchibstedGrotesk_500Medium,
  SchibstedGrotesk_600SemiBold,
  SchibstedGrotesk_700Bold,
  useFonts,
} from "@expo-google-fonts/schibsted-grotesk";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import * as Notifications from "expo-notifications";
import { router, Stack } from "expo-router";
import * as SplashScreen from "expo-splash-screen";
import { StatusBar } from "expo-status-bar";
import * as SystemUI from "expo-system-ui";
import { useEffect } from "react";
import { Platform } from "react-native";

import { AuthProvider, useAuth } from "@/lib/auth";
import { FavoritesProvider } from "@/lib/favorites";
import { font, useTheme } from "@/theme";

SplashScreen.preventAutoHideAsync();

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 60_000, retry: 1 },
  },
});

export default function RootLayout() {
  const [fontsLoaded] = useFonts({
    SchibstedGrotesk_400Regular,
    SchibstedGrotesk_500Medium,
    SchibstedGrotesk_600SemiBold,
    SchibstedGrotesk_700Bold,
  });

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <FavoritesProvider>
          <Navigator fontsLoaded={fontsLoaded} />
        </FavoritesProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}

function Navigator({ fontsLoaded }: { fontsLoaded: boolean }) {
  const theme = useTheme();
  const { ready } = useAuth();

  useEffect(() => {
    SystemUI.setBackgroundColorAsync(theme.bg);
  }, [theme.bg]);

  useEffect(() => {
    if (fontsLoaded && ready) SplashScreen.hideAsync();
  }, [fontsLoaded, ready]);

  // Tapping a reminder opens its event.
  useEffect(() => {
    if (Platform.OS === "web") return;
    const sub = Notifications.addNotificationResponseReceivedListener((response) => {
      const url = response.notification.request.content.data?.url;
      if (typeof url === "string") router.push(url as never);
    });
    return () => sub.remove();
  }, []);

  if (!fontsLoaded || !ready) return null;

  return (
    <>
      <StatusBar style={theme.dark ? "light" : "dark"} />
      <Stack
        screenOptions={{
          contentStyle: { backgroundColor: theme.bg },
          headerStyle: { backgroundColor: theme.bg },
          headerTintColor: theme.text,
          headerShadowVisible: false,
          headerTitleStyle: { fontFamily: font.semibold },
          headerBackTitleStyle: { fontFamily: font.regular },
        }}
      >
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen name="events/[slug]" options={{ title: "" }} />
        <Stack.Screen name="offers/[slug]" options={{ title: "" }} />
        <Stack.Screen name="places/[slug]" options={{ title: "" }} />
        <Stack.Screen name="favorites" />
        <Stack.Screen name="login" options={{ presentation: "modal" }} />
        <Stack.Screen name="register" options={{ presentation: "modal" }} />
      </Stack>
    </>
  );
}
